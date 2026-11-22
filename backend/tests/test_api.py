import unittest
from datetime import timedelta

from google.api_core.exceptions import ServiceUnavailable
from backend.listing_service import listing_day
from unittest.mock import patch
from backend.listing_store import MemoryStore
from fastapi.testclient import TestClient
from backend.app import create_app, RateLimiter
from backend.errors import Problem
from backend.models import Models
from backend.firebase_auth import FirebaseTokenVerifier

class TestVerifier:
    configured = True
    def verify(self, token):
        if token != "test-id-token":
            raise Problem(401, "unauthorized", "Invalid token")
        return "test-user"

class TestModels:
    state = "ready"
    bundle = {"sentiment": True}
    def recommendations(self, text, top_k):
        return {"method": "semantic", "matches": [{"job_id": "research-1",
                "application_url": "https://example.org/archived", "job_posting_url": "https://example.org/archived"}]}
    def recommendations_from_vacancies(self, text, vacancies, top_k):
        return {"matches": vacancies[:top_k], "received": text, "top_k": top_k}
    def sentiment(self, text):
        return {"label":"positive","method":"test-double"}

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(model_adapter=TestModels(), token_verifier=TestVerifier(), listing_store=MemoryStore()))
        self.addCleanup(self.client.close)
        self.headers = {"Authorization":"Bearer test-id-token"}
    def test_auth_required_and_invalid_rejected(self):
        self.assertEqual(self.client.post("/recommendations",json={"resume_text":"Kotlin"}).status_code,401)
        self.assertEqual(self.client.post("/sentiment",json={"text":"Helpful"},headers={"Authorization":"Bearer invalid"}).status_code,401)
    def test_authenticated_inference_contract(self):
        response=self.client.post("/recommendations",headers=self.headers,json={"resume_text":"Kotlin projects", "top_k":3})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["top_k"],3)
        self.assertEqual(response.json()["status"], "no_match")
        self.assertEqual(response.json()["matches"], [])
        self.assertEqual(response.headers["Cache-Control"],"no-store")
        self.assertEqual(self.client.post("/sentiment",headers=self.headers,json={"text":"Helpful"}).json()["label"],"positive")
    def test_research_requires_explicit_selection_and_disables_apply(self):
        response = self.client.post("/recommendations", headers=self.headers,
                                    json={"resume_text": "Kotlin", "catalogue": "research"})
        self.assertEqual(response.status_code, 200)
        match = response.json()["matches"][0]
        self.assertEqual(match["job_id"], "research-1")
        self.assertEqual(match["application_url"], "")
        self.assertEqual(match["job_posting_url"], "")
        self.assertFalse(match["ready_for_live_application"])

    def test_validation_does_not_echo_cv(self):
        private="personal text"*5000
        for body in ({"resume_text":"   "},{"resume_text":"Kotlin","top_k":True},{"resume_text":private}):
            response=self.client.post("/recommendations",headers=self.headers,json=body)
            self.assertEqual(response.status_code,422)
            self.assertNotIn(private,response.text)
    def test_local_accounts_and_storage_routes_removed(self):
        for path in ("/auth/sign-up","/auth/sign-in","/me/profile","/opportunities","/me/progress"):
            self.assertEqual(self.client.post(path,json={}).status_code,404)
    def test_missing_models_report_unavailable(self):
        with patch.dict("os.environ",{},clear=True):
            models=Models()
        with TestClient(create_app(model_adapter=models,token_verifier=TestVerifier(),listing_store=MemoryStore())) as client:
            self.assertEqual(client.get("/health").json()["model_status"],"not_configured")
            self.assertEqual(client.post("/recommendations",headers=self.headers,json={"resume_text":"Kotlin"}).status_code,503)
            self.assertEqual(client.post("/sentiment",headers=self.headers,json={"text":"Helpful"}).status_code,503)
    def test_deployment_startup_requires_model_and_firebase(self):
        with patch.dict("os.environ", {"UPSHIFT_REQUIRE_MODEL": "1"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "requires a loaded UpShift model"):
                create_app(model_adapter=Models(), token_verifier=TestVerifier())
            with self.assertRaisesRegex(RuntimeError, "configured Firebase project"):
                create_app(model_adapter=TestModels(), token_verifier=FirebaseTokenVerifier())
            self.assertIsNotNone(create_app(model_adapter=TestModels(), token_verifier=TestVerifier()))

    def test_rate_limit(self):
        limiter=RateLimiter()
        for _ in range(30): limiter.check("a")
        with self.assertRaises(Problem) as caught: limiter.check("a")
        self.assertEqual(caught.exception.status,429)
        limiter.check("b")
    def test_missing_project_fails_closed(self):
        with patch.dict("os.environ",{},clear=True):
            verifier=FirebaseTokenVerifier()
        with self.assertRaises(Problem) as caught: verifier.verify("anything")
        self.assertEqual(caught.exception.status,503)
    def test_emulator_cannot_be_used_with_live_project(self):
        with patch.dict("os.environ",{"UPSHIFT_FIREBASE_PROJECT_ID":"real-project","FIREBASE_AUTH_EMULATOR_HOST":"127.0.0.1:9099"}):
            verifier=FirebaseTokenVerifier()
            with self.assertRaises(Problem) as caught: verifier.verify("anything")
            self.assertEqual(caught.exception.status,503)

class LiveRecommendationsTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.models = TestModels()
        self.client = TestClient(create_app(self.models, TestVerifier(), self.store))
        self.addCleanup(self.client.close)
        for key, status in (('approved', 'approved'), ('suspended', 'suspended')):
            self.store.rows['partner_companies', key] = {'status': status}

    def vacancy(self, key, **overrides):
        row = {
            'id': key, 'company_id': 'approved', 'company': 'Example employer',
            'title': 'Software intern', 'description': 'Build Python services and test APIs.',
            'location': 'Nairobi, Kenya', 'availability_status': 'published',
            'ready_for_live_application': True, 'is_fictional': False, 'revision': 2,
            'source_url': 'https://example.org/jobs', 'deadline': listing_day().isoformat(),
            'owner_uid': 'excluded-from-inference',
        }
        self.store.rows['opportunities', key] = row | overrides

    def request(self, **fields):
        return self.client.post('/recommendations', json={'resume_text': 'Python', **fields},
                                headers={'Authorization': 'Bearer test-id-token'})

    def test_ranks_only_eligible_public_rows_across_pages(self):
        yesterday = (listing_day() - timedelta(days=1)).isoformat()
        for i in range(101):
            self.vacancy(f'expired-{i:03}', deadline=yesterday)
        self.vacancy('draft', availability_status='pending_review')
        self.vacancy('demo', is_fictional=True)
        self.vacancy('suspended', company_id='suspended')
        self.vacancy('unverified', ready_for_live_application=False)
        self.vacancy('malformed', deadline='unknown')
        self.vacancy('no-company', company_id='missing')
        self.vacancy('elsewhere', location='Mombasa, Kenya')
        self.vacancy('valid')
        self.vacancy('valid-no-deadline', deadline=None)
        response = self.request(location='  nAIrobi  ')
        self.assertEqual(response.status_code, 200, response.text)
        matches = response.json()['matches']
        self.assertEqual([m['job_id'] for m in matches], ['valid', 'valid-no-deadline'])
        self.assertTrue(matches[0]['ready_for_live_application'])
        self.assertEqual(matches[0]['application_url'], 'https://example.org/jobs')
        self.assertNotIn('owner_uid', matches[0])

    def test_excludes_a_vacancy_closed_during_inference(self):
        self.vacancy('changing')
        original_rank = self.models.recommendations_from_vacancies

        def rank_then_close(text, vacancies, top_k):
            result = original_rank(text, vacancies, top_k)
            self.store.rows['opportunities', 'changing']['availability_status'] = 'archived'
            return result

        self.models.recommendations_from_vacancies = rank_then_close
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['status'], 'no_match')
        self.assertEqual(response.json()['matches'], [])

    def test_firestore_failure_returns_503_without_research_fallback(self):
        def unavailable(*args, **kwargs):
            raise ServiceUnavailable('unavailable')

        self.store.list = unavailable
        response = self.request()
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(response.json()['error']['code'], 'listing_store_unavailable')


if __name__ == "__main__": unittest.main()
