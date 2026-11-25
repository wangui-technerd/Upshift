from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.feature_extraction.text import TfidfVectorizer
from upshift_ai.skills import build_lexicon
from upshift_ai.matching import recommend
from upshift_ai.api import create_app

@pytest.fixture
def toy_bundle():
 lex=build_lexicon(pd.DataFrame([{'conceptUri':'esco:python','preferredLabel':'Python (computer programming)','altLabels':'Python programming'},{'conceptUri':'esco:sql','preferredLabel':'SQL','altLabels':'Structured query language'}]).fillna(''))
 jobs=pd.DataFrame([{'job_id':'1','title':'Python intern','description':'Requirements: Python and SQL are required.','company_name':'Fixture company','location':'Nairobi','formatted_work_type':'INTERNSHIP','formatted_experience_level':'Internship','is_expired':True,'eligibility_status':'unverified','listed_time_utc':'2024-01-01','expiry_utc':'2024-02-01','application_url':'https://example.org/job','job_posting_url':'https://example.org/job','text':'python sql intern'},{'job_id':'2','title':'Office intern','description':'About us: our website uses Python.','company_name':'Fixture company','location':'Kenya','formatted_work_type':'INTERNSHIP','formatted_experience_level':'Internship','is_expired':True,'eligibility_status':'unverified','listed_time_utc':'2024-01-01','expiry_utc':'2024-02-01','application_url':'https://example.org/job2','job_posting_url':'https://example.org/job2','text':'python office intern'}])
 vectorizer=TfidfVectorizer().fit(jobs.text)
 return {'schema_version':2,'jobs':jobs,'retriever':vectorizer,'job_vectors':vectorizer.transform(jobs.text),'lexicon':lex,'job_skills':[lex.job_skills(t)for t in jobs.description]}

def test_actual_coverage_and_not_hiring_probability(toy_bundle):
 result=recommend(toy_bundle,'My skills: Python',top_k=2)
 first=next(r for r in result['matches']if r['job_id']=='1')
 assert first['skill_coverage']==.5
 assert first['skills_match_percentage']==50
 assert [s['label']for s in first['required_skills_not_mentioned']]==['SQL']
 assert first['is_expired']is True

def test_mentioned_only_has_unknown_coverage(toy_bundle):
 item=next(r for r in recommend(toy_bundle,'Python',2)['matches']if r['job_id']=='2')
 assert item['skills_match_percentage']is None

def test_live_only_excludes_expired_unverified_jobs(toy_bundle):assert recommend(toy_bundle,'Python',live_only=True)['status']=='no_match'
def test_unrelated_text_abstains(toy_bundle):assert recommend(toy_bundle,'zzzxqvzzzxqv')['matches']==[]
def test_invalid_topk_rejected(toy_bundle):
 with pytest.raises(ValueError):recommend(toy_bundle,'Python',top_k=True)

@pytest.fixture
def client(toy_bundle,tmp_path):
 joblib.dump(toy_bundle,tmp_path/'upshift_bundle.joblib')
 return TestClient(create_app(tmp_path,token='test-only-token'))
def test_health(client):assert client.get('/health').json()['jobs']==2
def test_auth_required(client):assert client.post('/recommend',json={'resume_text':'Python'}).status_code==401
def test_authorised_recommendation(client):assert client.post('/recommend',headers={'Authorization':'Bearer test-only-token'},json={'resume_text':'Python'}).status_code==200
def test_boolean_topk_invalid(client):assert client.post('/recommend',headers={'Authorization':'Bearer test-only-token'},json={'resume_text':'Python','top_k':True}).status_code==422
