"""Execute the reproducible CPU research pipeline and export a self-contained handoff."""
from pathlib import Path
import argparse,sys,os,json,time,shutil,zipfile,platform,importlib.metadata
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN','1');os.environ.setdefault('HF_HUB_DISABLE_XET','1');os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME',str(ROOT/'.cache/huggingface'))
sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,joblib
from threadpoolctl import threadpool_limits
from sklearn.feature_extraction.text import TfidfVectorizer
from upshift_ai.data import load_resumes,load_jobs,fingerprint
from upshift_ai.skills import build_lexicon
from upshift_ai.preprocessing import TOKEN_PATTERN
from upshift_ai.semantic import load_encoder,encode_documents,MODEL_ID
from upshift_ai.evaluation import career_comparison,retrieval_proxy_evaluation
from upshift_ai.sentiment import sentiment_benchmark,analyse_sentiment
from upshift_ai.matching import recommend

def progress(stage):print('\n=== '+stage+' ===',flush=True)
def run(resume_file,jobs_file,skills_file,max_jobs=6000,reuse_checkpoints=False):
 start=time.perf_counter();results=ROOT/'results';artifacts=ROOT/'artifacts';data=ROOT/'data'
 for path in [results,artifacts,data]:path.mkdir(parents=True,exist_ok=True)
 progress('1. Original raw data and audit')
 resumes,resume_audit=load_resumes(resume_file);jobs,job_audit=load_jobs(jobs_file,max_jobs=max_jobs)
 skills=pd.read_csv(skills_file,dtype=str);lexicon=build_lexicon(skills)
 audit={'resumes':resume_audit,'jobs':job_audit,'skills':{'rows':len(skills),'aliases':len(lexicon.aliases),'ambiguous_aliases_excluded':len(lexicon.audit['ambiguous_aliases_excluded'])}}
 (results/'data_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
 (results/'skill_alias_audit.json').write_text(json.dumps(lexicon.audit,indent=2))
 jobs[['job_id','title','company_name','location','proxy_category','is_expired']].to_csv(results/'catalogue_manifest.csv',index=False)
 progress('2. Career-category classifier comparison (supporting task)')
 if reuse_checkpoints and (artifacts/'career_checkpoint.joblib').exists():career,train,test,winner=joblib.load(artifacts/'career_checkpoint.joblib')
 else:
  career,train,test,winner=career_comparison(resumes,results);joblib.dump((career,train,test,winner),artifacts/'career_checkpoint.joblib')
 progress('3. Independently labelled sentiment: VADER vs logistic regression')
 if reuse_checkpoints and (artifacts/'sentiment_checkpoint.joblib').exists():sentiment=joblib.load(artifacts/'sentiment_checkpoint.joblib')
 else:
  sentiment,_=sentiment_benchmark(data,results);joblib.dump(sentiment,artifacts/'sentiment_checkpoint.joblib',compress=3)
 progress('4. Shared job index and contextual skill requirements')
 retriever=TfidfVectorizer(token_pattern=TOKEN_PATTERN,ngram_range=(1,2),min_df=2,max_df=.95,max_features=40000,sublinear_tf=True)
 retriever.fit(pd.concat([resumes.loc[train,'text'],jobs.text],ignore_index=True));job_vectors=retriever.transform(jobs.text)
 job_skills=[]
 for i,row in enumerate(jobs.itertuples()):
  original=row.title+'\n'+row.description+'\n'+str(row.skills_desc)
  found=lexicon.job_skills(original)
  job_skills.append({k:found[k]for k in ['required','preferred','mentioned','excluded']})
  if(i+1)%1000==0:print('Skill-indexed jobs:',i+1,flush=True)
 counts=pd.DataFrame([{k:len(v)for k,v in row.items()}for row in job_skills]);counts.describe().to_csv(results/'skill_index_summary.csv')
 progress('5. Local pretrained semantic encoder with sampled document chunks')
 encoder=load_encoder();vectors=encode_documents(encoder,jobs.text.tolist(),data/'semantic_job_vectors.npy');encoder.save(str(artifacts/'semantic_encoder'))
 bundle={'schema_version':2,'retriever':retriever,'job_vectors':job_vectors,'semantic_vectors':vectors,'jobs':jobs,'job_skills':job_skills,'lexicon':lexicon,'career_model':career,'sentiment':sentiment}
 progress('6. Retrieval comparison: explicitly labelled category PROXY')
 retrieval_proxy_evaluation(bundle,resumes,test,encoder,results)
 progress('7. Export, reload consistency and examples')
 example='I am a computer science student. My projects use Kotlin, Android, React.js, Python, SQL and Firebase. I have no Java experience.'
 examples={method:recommend(bundle,example,method=method,encoder=encoder)for method in ['lexical','semantic']}
 examples['sentiment']={text:analyse_sentiment(bundle,text)for text in ['The suggestions were helpful and clear.','The app shows five job listings.','I am disappointed by these irrelevant recommendations.']}
 examples['career_prediction']=str(career.predict([example])[0])
 (results/'example_predictions.json').write_text(json.dumps(examples,indent=2))
 joblib.dump(bundle,artifacts/'upshift_bundle.joblib',compress=3)
 reloaded=joblib.load(artifacts/'upshift_bundle.joblib')
 assert recommend(reloaded,example)==recommend(bundle,example)
 assert analyse_sentiment(reloaded,'This is useful')==analyse_sentiment(bundle,'This is useful')
 assert recommend(reloaded,'zzzxqvzzzxqvzzzxqv')['status']=='no_match'
 packages=['numpy','pandas','scipy','scikit-learn','joblib','nltk','torch','sentence-transformers','transformers','fastapi','uvicorn']
 versions={name:importlib.metadata.version(name)for name in packages}
 metadata={'schema_version':2,'python':platform.python_version(),'versions':versions,'seed':42,'raw_file_sha256':{Path(p).name:fingerprint(p)for p in [resume_file,jobs_file,skills_file]},
  'data_audit':audit,'career_model':winner,'semantic_model_id':MODEL_ID,'semantic_model_revision':getattr(encoder[0].auto_model.config,'_commit_hash',None),
  'semantic_fine_tuned':False,'semantic_chunking':{'words':160,'stride':120,'max_sampled_chunks':4,'notes':'Evenly sampled windows for longer texts; not full-document coverage.'},
  'default_ranking':'lexical','score_definition':'Raw text similarity; skills_match_percentage is separate required-skill coverage, not hiring probability.',
  'sentiment_winner_selected_on_validation':sentiment['selected'],'sentiment_benchmark':sentiment['source'],
  'independent_job_relevance_evaluation':'not evaluated: no human labels','runtime_seconds':time.perf_counter()-start,'reused_classifier_checkpoints':bool(reuse_checkpoints),
  'limitations':['Historical research vacancies, not a live eligible job feed','No target-domain student relevance or feedback labels','Rule-based skill context handles common cases, not arbitrary language','Career classification and job retrieval are separate tasks','Semantic encoder is pretrained, not fine-tuned on CV/job relevance pairs']}
 (artifacts/'metadata.json').write_text(json.dumps(metadata,indent=2))
 (results/'run_summary.json').write_text(json.dumps(metadata,indent=2))
 shutil.copytree(ROOT/'upshift_ai',artifacts/'upshift_ai',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
 shutil.copy2(ROOT/'requirements.txt',artifacts/'requirements.txt')
 (artifacts/'api.py').write_text('from upshift_ai.api import create_app\napp = create_app()\n')
 (artifacts/'README.md').write_text('Trusted local research artifact. Install requirements.txt; set UPSHIFT_ARTIFACT_DIR to this folder and UPSHIFT_API_TOKEN to a local integration secret. Run python -m uvicorn api:app --host 127.0.0.1 --port 8000. POST /recommend and /sentiment. Replace the shared local token with verified user authentication before public deployment. Historical jobs are not verified live opportunities. See metadata.json.\n')
 with zipfile.ZipFile(ROOT/'upshift_ai_handoff.zip','w',zipfile.ZIP_DEFLATED)as archive:
  for path in artifacts.rglob('*'):
   if path.is_file()and'checkpoint'not in path.name and'__pycache__'not in str(path):archive.write(path,path.relative_to(artifacts))
  for name in ['sentiment_metrics.csv','sentiment_reports.json','career_test_metrics.csv','retrieval_proxy_summary.csv','relevance_evaluation.json','run_summary.json']:
   archive.write(results/name,Path('results')/name)
 progress('COMPLETE: artifacts and handoff exported')
 return metadata

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--resume-file',required=True);p.add_argument('--jobs-file',required=True);p.add_argument('--skills-file',required=True);p.add_argument('--max-jobs',type=int,default=6000)
 p.add_argument('--reuse-checkpoints',action='store_true',help='Same inputs and unchanged classifier code only.')
 args=p.parse_args()
 with threadpool_limits(limits=2):run(args.resume_file,args.jobs_file,args.skills_file,args.max_jobs,args.reuse_checkpoints)
