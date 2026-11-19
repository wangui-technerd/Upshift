"""Validate the actual exported artifact and inference API, fully offline."""
from pathlib import Path
import os,sys,json,time
ROOT=Path(__file__).resolve().parent
os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1';os.environ['OMP_NUM_THREADS']='2'
sys.path.insert(0,str(ROOT))
import joblib
from fastapi.testclient import TestClient
from upshift_ai.api import create_app
from upshift_ai.matching import recommend
from upshift_ai.sentiment import analyse_sentiment
from upshift_ai.semantic import load_encoder

def verify():
 root=ROOT/'artifacts';bundle=joblib.load(root/'upshift_bundle.joblib');model=load_encoder(root/'semantic_encoder')
 cv='Computing student with Python, SQL, Kotlin, Android, Firebase and React.js project experience.'
 checks=[]
 for method in ['lexical','semantic']:
  result=recommend(bundle,cv,method=method,encoder=model)
  assert result['status']=='matches_found'and len(result['matches'])==5
  assert result['matches']==recommend(bundle,cv,method=method,encoder=model)['matches']
  assert all(item['eligibility_status']=='unverified'and item['is_expired']for item in result['matches'])
  assert all(a['similarity']>=b['similarity']for a,b in zip(result['matches'],result['matches'][1:]))
  checks.append(method+' reload + deterministic order + metadata')
 assert recommend(bundle,cv,live_only=True)['status']=='no_match';checks.append('live-only excludes historical unverified vacancies')
 assert recommend(bundle,'zzzxqvzzzxqv')['status']=='no_match';checks.append('unknown input abstains')
 client=TestClient(create_app(root,token='verification-only-token'));headers={'Authorization':'Bearer verification-only-token'}
 assert client.get('/health').status_code==200
 assert client.post('/recommend',json={'resume_text':cv}).status_code==401
 for invalid in [{'resume_text':' '},{'resume_text':cv,'top_k':True},{'resume_text':cv,'top_k':21},{'resume_text':cv,'method':'wrong'}]:assert client.post('/recommend',headers=headers,json=invalid).status_code==422
 for method in ['lexical','semantic']:
  response=client.post('/recommend',headers=headers,json={'resume_text':cv,'method':method});assert response.status_code==200;assert len(response.json()['matches'])==5
 for text in ['Helpful and clear!','The app displays five jobs.','Terrible and disappointing.']:
  response=client.post('/sentiment',headers=headers,json={'text':text});assert response.status_code==200;assert response.json()['label']in ['positive','negative','neutral']
 checks.extend(['health route','authentication required','invalid requests rejected','lexical and semantic HTTP inference','sentiment HTTP inference'])
 (ROOT/'results/export_verification.json').write_text(json.dumps({'status':'passed','offline':True,'checks':checks},indent=2))
 print(json.dumps({'status':'passed','checks':checks},indent=2),flush=True)
 return checks
if __name__=='__main__':verify()
