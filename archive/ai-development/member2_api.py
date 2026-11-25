"""Run from extracted handoff: python -m uvicorn member2_api:app."""
import os
from pathlib import Path
from secrets import compare_digest
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict, field_validator
from upshift_ai.handoff import ModelService


def create_app(root=None,token=None):
    root=Path(root or os.environ.get('UPSHIFT_ARTIFACT_DIR',Path(__file__).resolve().parent/'artifacts'))
    secret=token or os.environ.get('UPSHIFT_API_TOKEN')
    if not secret:raise RuntimeError('Set UPSHIFT_API_TOKEN to a backend-only secret.')
    service=ModelService(root)
    app=FastAPI(title='UpShift AI Member 2 handoff',version='2026.11.22')
    def auth(authorization:str|None=Header(default=None)):
        if authorization is None or not compare_digest(authorization,'Bearer '+secret):raise HTTPException(401,'Unauthorized')
    @app.get('/health')
    def health():return {'status':'ok','schema_version':2,'selected_method':service.method,'catalogue_status':'historical_research_not_live'}
    @app.post('/recommendations',dependencies=[Depends(auth)])
    def recommendations(body:RecommendationRequest):
        try:return service.recommendations(body.resume_text,body.top_k,body.live_only)
        except ValueError as e:raise HTTPException(422,str(e)) from e
    @app.post('/sentiment',dependencies=[Depends(auth)])
    def sentiment(body:SentimentRequest):return service.sentiment(body.text)
    return app


class RecommendationRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    resume_text:str=Field(min_length=1,max_length=50000,strict=True)
    top_k:int=Field(default=5,ge=1,le=20,strict=True)
    live_only:bool=False
    @field_validator('resume_text')
    @classmethod
    def nonblank(cls,v):
        if not v.strip():raise ValueError('CV text must not be blank.')
        return v


class SentimentRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text:str=Field(min_length=1,max_length=10000,strict=True)
    @field_validator('text')
    @classmethod
    def nonblank(cls,v):
        if not v.strip():raise ValueError('Feedback must not be blank.')
        return v


# Factory also supports tests without environment credentials.
if os.environ.get('UPSHIFT_API_TOKEN'):app=create_app()
