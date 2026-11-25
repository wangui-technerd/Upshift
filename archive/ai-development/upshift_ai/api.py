"""Local-integration API factory; inference loads only trusted self-produced artifacts."""
from pathlib import Path
import os,threading
from secrets import compare_digest
from typing import Literal
import joblib
from fastapi import FastAPI,Header,HTTPException,Depends
from pydantic import BaseModel,Field,field_validator,ConfigDict
from .matching import recommend
from .sentiment import analyse_sentiment

class RecommendationRequest(BaseModel):
 model_config=ConfigDict(extra='forbid')
 resume_text:str=Field(min_length=1,max_length=50000,strict=True)
 top_k:int=Field(default=5,ge=1,le=20,strict=True)
 method:Literal['lexical','semantic']='lexical'
 min_similarity:float=Field(default=0,ge=0,le=1,allow_inf_nan=False)
 live_only:bool=False
 @field_validator('resume_text')
 @classmethod
 def nonblank(cls,value):
  if not value.strip():raise ValueError('CV text must not be blank.')
  return value
class SentimentRequest(BaseModel):
 model_config=ConfigDict(extra='forbid')
 text:str=Field(min_length=1,max_length=10000,strict=True)
 @field_validator('text')
 @classmethod
 def nonblank(cls,value):
  if not value.strip():raise ValueError('Feedback must not be blank.')
  return value

def create_app(artifact_dir=None,token=None):
 root=Path(artifact_dir or os.environ.get('UPSHIFT_ARTIFACT_DIR',Path(__file__).resolve().parent.parent/'artifacts'))
 expected=token or os.environ.get('UPSHIFT_API_TOKEN')
 if not expected:raise RuntimeError('Set UPSHIFT_API_TOKEN for local integration; do not embed this shared secret in a released Android app.')
 bundle=joblib.load(root/'upshift_bundle.joblib')
 if bundle.get('schema_version')!=2:raise RuntimeError('Incompatible model bundle schema.')
 app=FastAPI(title='UpShift NLP',version='1.0.0',description='Historical research catalogue. Not a live eligibility service. Sentiment is separate from employability.')
 lock=threading.Lock();encoder=None
 def authorise(authorization:str|None=Header(default=None)):
  if authorization is None or not compare_digest(authorization,'Bearer '+expected):raise HTTPException(401,'Unauthorized')
 def get_encoder():
  nonlocal encoder
  if encoder is None:
   with lock:
    if encoder is None:
     from .semantic import load_encoder
     encoder=load_encoder(root/'semantic_encoder')
  return encoder
 @app.get('/health')
 def health():return {'status':'ok','schema_version':2,'jobs':len(bundle['jobs']),'catalogue_status':'historical_research_not_live'}
 @app.post('/recommend',dependencies=[Depends(authorise)])
 def recommendations(request:RecommendationRequest):
  try:return recommend(bundle,request.resume_text,request.top_k,request.method,request.min_similarity,get_encoder()if request.method=='semantic'else None,request.live_only)
  except ValueError as error:raise HTTPException(422,str(error))from error
 @app.post('/sentiment',dependencies=[Depends(authorise)])
 def sentiment(request:SentimentRequest):return analyse_sentiment(bundle,request.text)
 return app
