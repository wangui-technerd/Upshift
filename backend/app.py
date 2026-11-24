"""Firebase-authenticated inference, partner vacancies and selected-source collection."""
import os
import threading
import time
from collections import OrderedDict
from typing import Literal
from uuid import UUID
from datetime import datetime, timezone
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from .errors import Problem
from .models import Models
from .firebase_auth import FirebaseTokenVerifier
from .listing_service import ListingService

class Body(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Recommendations(Body):
    resume_text: str = Field(min_length=1, max_length=50000)
    top_k: int = Field(default=5, ge=1, le=20, strict=True)
    catalogue: Literal['live', 'research'] = 'live'
    location: str | None = Field(default=None, min_length=1, max_length=200)
    experience_months: int | None = Field(default=None, ge=0, le=1200, strict=True)

class Text(Body):
    text: str = Field(min_length=1, max_length=10000)

class Feedback(Text):
    submission_id: UUID

class RateLimiter:
    """Bounded single-process limiter; production ingress also needs rate limits."""
    def __init__(self):
        self.lock = threading.Lock()
        self.entries = OrderedDict()
    def check(self, uid):
        now = time.monotonic()
        with self.lock:
            while self.entries and next(iter(self.entries.values()))[0] < now-60:
                self.entries.popitem(last=False)
            start, count = self.entries.get(uid, (now, 0))
            if count >= 30:
                raise Problem(429, 'rate_limited', 'Too many AI requests. Try again later.')
            self.entries[uid] = (start, count+1)
            if len(self.entries) > 10000:
                self.entries.popitem(last=False)

def create_app(model_adapter=None, token_verifier=None, listing_store=None, source_collector=None):
    models = model_adapter if model_adapter is not None else Models()
    verifier = token_verifier if token_verifier is not None else FirebaseTokenVerifier()
    if os.getenv('UPSHIFT_REQUIRE_MODEL') == '1' and (models.state != 'ready' or not verifier.configured):
        raise RuntimeError('Deployment requires a loaded UpShift model and a configured Firebase project.')
    limiter = RateLimiter()
    app = FastAPI(title='UpShift API', version='0.3.0', description='Firebase-authenticated inference and vacancy management. Data is persisted in Firestore.')
    auth = HTTPBearer(auto_error=False)

    @app.exception_handler(Problem)
    async def problem_handler(request, exc):
        headers = {'WWW-Authenticate':'Bearer'} if exc.status == 401 else {}
        if exc.status == 429: headers['Retry-After'] = '60'
        return JSONResponse(status_code=exc.status, content={'error':{'code':exc.code,'message':exc.message}}, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        fields = [{'field':'.'.join(map(str,e['loc'])),'message':e['msg']} for e in exc.errors()]
        return JSONResponse(status_code=422, content={'error':{'code':'validation_error','message':'Check the request fields.','fields':fields}})

    @app.middleware('http')
    async def privacy_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    def user(credentials: HTTPAuthorizationCredentials | None = Depends(auth)):
        if credentials is None:
            raise Problem(401, 'unauthorized', 'Sign in to continue.')
        uid = verifier.verify(credentials.credentials)
        limiter.check(uid)
        return uid

    def actor(credentials: HTTPAuthorizationCredentials | None = Depends(auth)):
        if credentials is None:
            raise Problem(401, 'unauthorized', 'Sign in to continue.')
        if not hasattr(verifier, 'verify_claims'):
            raise Problem(503, 'auth_unavailable', 'Claim verification is required for vacancy management.')
        claims = verifier.verify_claims(credentials.credentials)
        limiter.check(claims['uid'])
        return claims

    def admin(claims=Depends(actor)):
        if claims.get('upshift_admin') is not True:
            raise Problem(403, 'forbidden', 'An UpShift administrator account is required.')
        return claims

    from .listing_api import listing_router
    from .listing_store import FirestoreListingStore
    store = listing_store if listing_store is not None else FirestoreListingStore()
    listings = ListingService(store)
    app.include_router(listing_router(store, actor, admin, source_collector))

    @app.get('/health')
    def health():
        return {'status':'ok','auth_provider':'firebase','auth_configured':verifier.configured,
                'model_status':models.state,
                'sentiment_ready':bool(models.bundle and models.bundle.get('sentiment') is not None)}

    @app.post('/recommendations')
    def recommendations(body: Recommendations, uid=Depends(user)):
        if body.catalogue == 'research':
            if body.location is not None or body.experience_months is not None:
                raise Problem(422, 'unsupported_filter', 'Location and experience filters are available for live vacancies.')
            result = models.recommendations(body.resume_text, body.top_k)
            return {
                **result,
                'matches': [
                    {**match, 'application_url': '', 'job_posting_url': '',
                     'ready_for_live_application': False}
                    for match in result['matches']
                ],
            }
        return listings.recommend(models, body.resume_text, body.top_k, body.location, body.experience_months)

    @app.post('/sentiment')
    def sentiment(body: Text, uid=Depends(user)):
        return models.sentiment(body.text)

    @app.post('/feedback')
    def feedback(body: Feedback, uid=Depends(user)):
        key = ('feedback', str(body.submission_id))
        def save(rows):
            existing = rows[key]
            if existing:
                if existing['owner_uid'] != uid or existing['text'] != body.text:
                    raise Problem(409, 'feedback_conflict', 'Please start a new feedback message.')
                return {}, {'status': 'received', 'id': key[1]}
            row = {'id': key[1], 'owner_uid': uid, 'text': body.text,
                   'created_at': datetime.now(timezone.utc).isoformat()}
            return {key: row}, {'status': 'received', 'id': key[1]}
        try:
            return store.transact([key], save)
        except Problem:
            raise
        except Exception:
            raise Problem(503, 'feedback_unavailable', 'Could not send feedback. Please try again.')

    return app

app = create_app()
