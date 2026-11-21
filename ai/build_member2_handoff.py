"""Build and verify the single-AI-assisted Member 2 delivery, offline."""
from pathlib import Path
import os, sys, json, shutil, hashlib, zipfile, time, io, contextlib
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1'
import pandas as pd
import joblib
import nbformat
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from fastapi.testclient import TestClient
from upshift_ai.handoff import ModelService
from upshift_ai.sentiment import analyse_sentiment
from complete_ai_review import run
from member2_api import create_app

CASES=[
('praise','The recommendations were helpful and easy to understand.','positive'),
('praise','I love the clear explanations and useful learning resources.','positive'),
('praise','Great app! It helped me find a relevant internship.','positive'),
('praise','The skill-gap guidance was excellent and encouraging.','positive'),
('expired','All these vacancies expired last year. This is frustrating.','negative'),
('irrelevant','These jobs are irrelevant to my qualifications.','negative'),
('cost','The recommended courses are too expensive for me.','negative'),
('error','The app keeps freezing and I cannot save my CV.','negative'),
('privacy','I am worried that my private CV information is not safe.','negative'),
('question','Where can I download my CV?','neutral'),
('question','How is the matching score calculated?','neutral'),
('question','Can I filter the roles by location?','neutral'),
('statement','The screen displays five recommendations.','neutral'),
('statement','I have completed the SQL course.','neutral'),
('mixed','The layout is nice, but all the jobs are expired and unusable.','negative'),
('mixed','The recommendations are useful, although the page loads slowly. Overall I like it.','positive'),
('mixed','Some suggestions fit my profile and some do not.','neutral'),
('negative','I hate these inaccurate skill assessments.','negative'),
('positive','Thank you, the next steps are clear and practical.','positive'),
('question','Does this course provide a certificate?','neutral'),
]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    report=run()
    destination=ROOT.parent/'output/member2_handoff'
    destination.mkdir(parents=True,exist_ok=True)
    art=destination/'artifacts';art.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'artifacts/upshift_bundle.joblib',art/'upshift_bundle.joblib')
    shutil.copytree(ROOT/'artifacts/semantic_encoder',art/'semantic_encoder',dirs_exist_ok=True)
    config={'schema_version':2,'selected_method':report['selected_method'],'review_status':report['status'],'independent_human_review':False,'sentiment_optional':True,'catalogue_status':'historical_research_not_live','source_bundle_sha256':sha(ROOT/'artifacts/upshift_bundle.joblib')}
    (art/'deployment_config.json').write_text(json.dumps(config,indent=2))
    shutil.copytree(ROOT/'upshift_ai',destination/'upshift_ai',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['requirements.txt','member2_api.py','member2_backend_models.py','MODEL-LICENSE-Apache-2.0.txt','THIRD_PARTY_NOTICES.md','run_pipeline.py','complete_ai_review.py','prepare_student_review.py','score_student_review.py','STUDENT_REVIEW_GUIDE.md','verify_export.py','verify_member2_handoff.py','build_member2_handoff.py']:
        shutil.copy2(ROOT/name,destination/name)
    shutil.copytree(ROOT/'student_review',destination/'student_review',dirs_exist_ok=True)
    shutil.copytree(ROOT/'tests',destination/'tests',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    (destination/'results').mkdir(exist_ok=True)
    for name in ['sentiment_metrics.csv','sentiment_validation.csv','sentiment_reports.json','sentiment_data_audit.json','career_test_metrics.csv','career_validation.json','career_reports.json','retrieval_proxy_summary.csv','export_verification.json','run_summary.json']:
        if (ROOT/'results'/name).exists():shutil.copy2(ROOT/'results'/name,destination/'results'/name)
    # Labels are fixed above before predictions; synthetic AI-authored cases only.
    sentiment=pd.DataFrame(CASES,columns=['case_type','text','expected_label'])
    sentiment.to_csv(destination/'results/sentiment_cases_frozen.csv',index=False)
    service=ModelService(art)
    sentiment['predicted_label']=[service.sentiment(t)['label'] for t in sentiment.text]
    sentiment['correct']=sentiment.expected_label.eq(sentiment.predicted_label)
    sentiment.to_csv(destination/'results/sentiment_app_checks.csv',index=False)
    sm={'cases':len(sentiment),'label_source':'AI-authored expected labels on synthetic app feedback; not independent human evaluation','accuracy':accuracy_score(sentiment.expected_label,sentiment.predicted_label),'macro_f1':f1_score(sentiment.expected_label,sentiment.predicted_label,average='macro',zero_division=0),'labels':['negative','neutral','positive'],'confusion_matrix':confusion_matrix(sentiment.expected_label,sentiment.predicted_label,labels=['negative','neutral','positive']).tolist(),'use':'Optional feedback triage only; not job ranking, readiness scoring or automatic decisions.'}
    (destination/'results/sentiment_app_summary.json').write_text(json.dumps(sm,indent=2))
    cv='Year 3 computing student. Python, JavaScript, React, HTML, CSS, SQL and Git. Built a Flask REST API and wrote basic pytest tests. Seeking a first software internship.'
    request={'resume_text':cv,'top_k':5}
    app=create_app(art,token='handoff-test-token');client=TestClient(app)
    headers={'Authorization':'Bearer handoff-test-token'}
    checks=[]
    assert client.get('/health').json()['selected_method']==report['selected_method'];checks.append('schema-2 reload and selected method')
    assert client.post('/recommendations',json=request).status_code==401;checks.append('unauthorised request rejected')
    for bad in [{'resume_text':' '},{'resume_text':cv,'top_k':True},{'resume_text':cv,'top_k':21}]:
        assert client.post('/recommendations',headers=headers,json=bad).status_code==422
    checks.append('blank text, boolean top_k and oversized top_k rejected')
    start=time.perf_counter();response=client.post('/recommendations',headers=headers,json=request)
    assert response.status_code==200,response.text
    result=response.json();elapsed=time.perf_counter()-start
    assert result['method']==report['selected_method'] and len(result['matches'])==5
    assert all(a['similarity']>=b['similarity'] for a,b in zip(result['matches'],result['matches'][1:]))
    again=client.post('/recommendations',headers=headers,json=request).json()
    assert again==result;checks.append('selected inference, five descending matches and deterministic repeat')
    assert client.post('/recommendations',headers=headers,json={**request,'live_only':True}).json()['matches']==[]
    checks.append('live-only research request returns no historical jobs')
    assert client.post('/sentiment',headers=headers,json={'text':'This is helpful.'}).status_code==200
    checks.append('sentiment HTTP inference')
    fixtures=[{'job_id':'fixture-software','title':'Software intern','description':'Requirements: Python, Git and SQL. Assist with Flask REST API development.','company_name':'FICTIONAL TEST ONLY'}, {'job_id':'fixture-lab','title':'Cell biology intern','description':'Requirements: tissue culture, molecular biology and laboratory experiments.','company_name':'FICTIONAL TEST ONLY'}]
    ranked=service.rank_vacancies(cv,fixtures,top_k=2)
    assert ranked['matches'][0]['job_id']=='fixture-software'
    assert service.rank_vacancies(cv,[],5)['matches']==[]
    checks.append('backend-supplied candidate ranking and empty candidate list')
    # Check the replacement against the actual backend interface in an isolated package.
    import importlib.util, types
    errors=ROOT.parent/'tmp/project-review-recruiter-20261119/backend/errors.py'
    package=types.ModuleType('handoff_backend_check');package.__path__=[];sys.modules[package.__name__]=package
    spec=importlib.util.spec_from_file_location(package.__name__+'.errors',errors)
    error_module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=error_module;spec.loader.exec_module(error_module)
    spec=importlib.util.spec_from_file_location(package.__name__+'.models',destination/'member2_backend_models.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    os.environ['UPSHIFT_MODEL_PATH']=str(art/'upshift_bundle.joblib')
    backend=adapter.Models();assert backend.state=='ready',backend.load_error
    assert backend.recommendations(cv,1)['method']==report['selected_method']
    assert backend.sentiment('Thank you for the useful advice!')['label'] in ['positive','negative','neutral']
    checks.append('replacement Models adapter loads schema-2 and runs both backend methods')
    import subprocess
    env=dict(os.environ);env['PYTHONPATH']=str(ROOT)
    tests=subprocess.run([sys.executable,'-m','pytest',str(ROOT/'tests'),'-q','--tb=short'],env=env,capture_output=True,text=True,timeout=60)
    assert tests.returncode==0,tests.stdout+tests.stderr
    (destination/'results/regression_tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    checks.append('27 existing model/API regression tests passed; see regression_tests.txt')
    for name,data in [('sample_request.json',request),('sample_response.json',result),('sample_candidate_ranking.json',ranked),('openapi.json',app.openapi())]:
        (destination/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
    verification={'status':'passed','offline':True,'checks':checks,'cold_semantic_http_seconds':elapsed,'timing_scope':'Local Windows CPU, includes model loading; not an Android performance benchmark.'}
    (destination/'results/member2_verification.json').write_text(json.dumps(verification,indent=2))
    write_readme(destination,report,sm,verification)
    write_notebook(destination,report,sentiment)
    # Every shipped file gets a checksum, excluding the checksum file itself.
    files={p.relative_to(destination).as_posix():sha(p) for p in destination.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='SHA256SUMS.json'}
    (destination/'SHA256SUMS.json').write_text(json.dumps(files,indent=2))
    target=destination.parent/'UpShift_Member2_Handoff_AI_Assisted.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):z.write(destination/name,name)
        z.write(destination/'SHA256SUMS.json','SHA256SUMS.json')
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(json.dumps({'zip':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'verification':verification,'sentiment':sm},indent=2))

def write_readme(dest,report,sm,verification):
    test=report['test_result'][0]
    text=f'''# Member 2: start here

Prepared 22 November 2026. Review type: **one AI-assisted reviewer**. No independent human validation or inter-reviewer agreement is claimed.

## What you receive

- `artifacts/upshift_bundle.joblib`: trusted schema-2 fitted models and 6,000 historical research vacancies.
- `artifacts/semantic_encoder/`: offline MiniLM encoder; keep the whole folder.
- `artifacts/deployment_config.json`: selected ranking method `{report['selected_method']}`. The bundle itself is unchanged; the config and service fix deployment selection.
- `upshift_ai/handoff.py`: `ModelService`, the supported Python entry point.
- `member2_api.py`: working backend-only local service with `/health`, `/recommendations`, `/sentiment`.
- `member2_backend_models.py`: replacement for the old schema-1-only `backend/models.py`.
- `UpShift_Final_AI_Assisted.ipynb`: original 41-cell executed clear notebook plus executed final review and handoff checks. Earlier clear-results toy exports are not this deployment format; use the schema-2 files above.
- `student_review/ai_assisted/`: 112 ratings, reasons, reviewer disclosure, per-profile metrics and method comparison. Human reviewer sheets remain blank.
- `results/`: original benchmark results, contextual sentiment errors, exact export checks.
- `sample_request.json`, `sample_response.json`, `sample_candidate_ranking.json`, `openapi.json`, pinned requirements and checksums.

## Evaluation in plain language

We compared TF-IDF cosine retrieval and MiniLM semantic retrieval on twelve fictional students across six fields. Six profiles selected the method and six reported held-out test performance. Labels were assigned by one AI assistant using the frozen 0/1/2 rubric, not by people. Requirement-focused excerpts were used, so this is a preliminary review rather than an exhaustive human audit. No labels were changed after results were calculated.

MiniLM won validation pooled NDCG@5. On the test profiles: P@5 **{test['precision_at_5']:.3f}**, pooled NDCG@5 **{test['pooled_ndcg_at_5']:.3f}**, at-least-one-good-match coverage **{test['good_match_coverage']:.1%}**. P@5 means the fraction of the five recommendations judged a good fit; it is not overall model accuracy. These modest results expose real failures, including experienced roles labelled entry level, field confusion and no relevant result for some student cases. Method choice is provisional pending representative independent review. Pooled NDCG measures ordering within the pooled top-five candidates, not the full catalogue.

Sentiment is a separate TF-IDF/logistic-regression classifier with VADER comparison in the original benchmark. On {sm['cases']} AI-authored app-feedback examples it scored {sm['accuracy']:.1%} accuracy and {sm['macro_f1']:.3f} macro F1. Inspect `results/sentiment_app_checks.csv` for every mistake. This small synthetic diagnostic is not a human-labelled app benchmark. Keep sentiment optional; it must not affect job ranks or perceived employability. No generative coach is supplied. Skill extraction uses ESCO/manual aliases and contextual rules, not a trained skill-gap classifier. Course recommendation links remain curated app/backend data.

## Install and run (Python 3.12 tested)

From the extracted handoff directory in PowerShell:

```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:UPSHIFT_API_TOKEN = "choose-a-private-backend-token"
.\\.venv\\Scripts\\python.exe -m uvicorn member2_api:app --host 127.0.0.1 --port 8000
```

If an existing environment has the torchvision `nms` import error, use this fresh environment. The text encoder does not require torchvision or torchaudio. A clean-machine dependency install has not been repeated for this handoff; inference was checked offline in the existing pinned environment. Do not put the service token or joblib loader in Android. Android authenticates to your Firebase-protected backend; your backend may call this service with its private token.

```powershell
$headers = @{{ Authorization = "Bearer $env:UPSHIFT_API_TOKEN" }}
$body = Get-Content sample_request.json -Raw
Invoke-RestMethod http://127.0.0.1:8000/recommendations -Method Post -Headers $headers -ContentType application/json -Body $body
```

The returned IDs/order/scores should match `sample_response.json`; tiny numeric differences across hardware/library builds are possible. Cosine similarity is not a percentage hiring probability. `skills_match_percentage` is extracted required-skill coverage; null means no reliable required-skill denominator. Skills not mentioned are not proof of inability.

## Connect to your existing Firebase backend

1. Keep `upshift_ai/` importable from the backend environment (copy it beside `backend/`, or add this extracted directory to PYTHONPATH).
2. Install the delivered pinned requirements alongside your backend dependencies; resolve any backend version conflicts before merging.
3. Replace the old `backend/models.py` with `member2_backend_models.py`, keeping the filename `models.py`. It preserves `Models.state`, `Models.bundle`, `recommendations(text, top_k)` and `sentiment(text)` and translates legacy skill field names. Existing Firebase routes and authentication remain yours.
4. Set `UPSHIFT_MODEL_PATH` to the absolute path of `artifacts/upshift_bundle.joblib`. Leave `deployment_config.json` and `semantic_encoder/` beside it. The old schema-1 loader will reject this bundle; do not use it or the toy clear-notebook export.
5. Test your authenticated `/recommendations` route using `resume_text` and `top_k`. `/recommend` in older research code is a different route. The supplied standalone service uses `/recommendations`.

The replacement adapter was actually loaded against the inspected backend's `Problem` interface and ran recommendations and sentiment. Live Firebase and a merged Android build were not exercised.

## Real vacancies: Member 2's integration task

The built-in index contains historical listings; it is for research/demo only. `live_only=true` returns no matches from that index. Do not enable Apply on these archived listings.

For real recommendations, query your approved, published, unexpired vacancies, enforce authorisation/location rules, then call:

```python
from upshift_ai.handoff import ModelService
service = ModelService("/absolute/path/to/artifacts")  # once at server startup
result = service.rank_vacancies(resume_text, approved_vacancies, top_k=5)
# or Models.recommendations_from_vacancies(text, approved_vacancies, 5)
```

Each vacancy needs unique `job_id`, `title`, `description`; optional `company_name` and `application_url`. This path computes fresh embeddings and skill extraction for the supplied descriptions, using the selected encoder. The caller must filter eligibility, expiry, approval and access before calling; this ranking function does not verify them. Cache vacancy embeddings by content hash for production scale. The historical student-review metrics do not establish performance on this new live corpus. An empty supplied list returns `no_match`, with no fallback to archived jobs.

## Reproduction and checks

- Run `python complete_ai_review.py` to reproduce saved ratings and their metrics; it verifies frozen profile/ranking hashes. This replays authored judgements, not a fresh independent review.
- Run `python -m pytest tests -q` for model/API logic tests.
- Run `python verify_member2_handoff.py` from the extracted delivery to verify all checksums, load offline and compare the real API prediction against the supplied expected output.
- `run_pipeline.py` and shared modules reproduce the engineering schema-2 training when the original source CSVs are supplied as described in `TRAINING_GUIDE.md`. Source CSVs are not included; the artifact does embed catalogue descriptions and fitted models. Observe dataset licences and repository permissions before redistribution/deployment; this handoff does not grant those rights.
- Full bundle reload, selected-method HTTP inference, deterministic order, validation, auth, historical live-only exclusion, sentiment, candidate ranking and backend adapter checks passed offline. See `results/member2_verification.json`. Cold selected-method HTTP inference took {verification['cold_semantic_http_seconds']:.2f}s on this local CPU, including encoder load; this is not a phone benchmark. Load once, reuse the service, and show loading/error states in Android.
- `SHA256SUMS.json` records every shipped file. Load only these trusted project-produced joblib files.

## Ownership after handoff

Member 1's AI-assisted evaluation and technical export are complete for this scope. Independent human validation remains explicitly pending. Member 2 owns Firebase/live vacancy wiring, deployment, backend auth and integrated API checks. Member 3 owns Android API wiring, loading/error states and final physical-phone tests. The existing Android main feed still needs replacement of its local scorer/sample repository with the connected response. No live production readiness is claimed here.
'''
    (dest/'START_HERE_MEMBER_2.md').write_text(text,encoding='utf-8')
    shutil.copy2(ROOT/'README.md',dest/'TRAINING_GUIDE.md')

def write_notebook(dest,report,sentiment):
    nb=nbformat.read(ROOT/'notebooks/UpShift_Clear_Steps.ipynb',as_version=4)
    nb.cells.append(nbformat.v4.new_markdown_cell('''## Final handoff: AI-assisted relevance review and deployment

Added 22 November 2026. The preceding 41 executed cells are preserved. This section evaluates the **engineering schema-2 export**, the same trusted artifact used to freeze both-method candidate lists. The earlier `clear_results` teaching export uses a different layout and is not the deployment artifact. Training/reproduction source for schema 2 is supplied in the handoff.

One AI assistant rated 112 pooled student/job pairs. No human reviews, two-reviewer agreement, or human ground truth are claimed. Requirements and student evidence drive 0=poor, 1=partial, 2=good relevance; eligibility and expiry are separate. Some evidence was reviewed as requirement-focused excerpts. Twelve fictional profiles cover six fields, with six validation and six test profiles. Frozen validation pooled NDCG@5 selects the method; test does not tune it. Review remains preliminary and does not prove usefulness to Kenyan students.
'''))
    summary=pd.read_csv(ROOT/'student_review/ai_assisted/summary.csv')
    code="""# Saved measured results, with their provenance shown explicitly.
import pandas as pd
import json
from pathlib import Path
roots = [Path.cwd(), Path.cwd() / 'ai', Path.cwd().parent, Path.cwd().parent.parent]
handoff_root = next(p for p in roots if (p / 'student_review/ai_assisted/evaluation.json').exists())
import sys
sys.path.insert(0, str(handoff_root))
from complete_ai_review import run
evaluation = run()  # Reproduce the authored ratings and metrics with frozen-input hash checks.
print('Review type:', evaluation['status'])
print(pd.read_csv(handoff_root / 'student_review/ai_assisted/summary.csv').to_string(index=False))
print('Selected on validation:', evaluation['selected_method'])
print('Independent human validation:', evaluation['independent_human_review'])
"""
    cell=nbformat.v4.new_code_cell(code)
    execute_cell(cell,42);nb.cells.append(cell)
    nb.cells.append(nbformat.v4.new_markdown_cell('''### Sentiment diagnostic and limitations

Twenty synthetic app-feedback cases were assigned expected labels by the same AI assistant before prediction. These are diagnostic examples, not independent human-labelled test data. Mixed statements use the stated overall sentiment. Errors are retained. Sentiment is optional feedback analysis and never determines employability or job rank.
'''))
    cell=nbformat.v4.new_code_cell("""# All expected labels and predictions are embedded for transparent inspection.
sentiment_checks = pd.DataFrame("""+repr(sentiment.to_dict('records'))+""")
import sys, os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
delivery = next(p for p in [Path.cwd(), Path.cwd() / 'output/member2_handoff'] if (p / 'artifacts/deployment_config.json').exists())
sys.path.insert(0, str(delivery))
from upshift_ai.handoff import ModelService
sentiment_model = ModelService(delivery / 'artifacts')
sentiment_checks['predicted_label'] = [sentiment_model.sentiment(t)['label'] for t in sentiment_checks.text]
sentiment_checks['correct'] = sentiment_checks.expected_label.eq(sentiment_checks.predicted_label)
from sklearn.metrics import accuracy_score, f1_score
print(sentiment_checks[['case_type','text','expected_label','predicted_label','correct']].to_string(index=False))
print('Accuracy:', accuracy_score(sentiment_checks.expected_label, sentiment_checks.predicted_label))
print('Macro F1:', f1_score(sentiment_checks.expected_label, sentiment_checks.predicted_label, average='macro', zero_division=0))
""")
    execute_cell(cell,43);nb.cells.append(cell)
    nb.cells.append(nbformat.v4.new_markdown_cell('''### Final verified files for Member 2

Use `artifacts/upshift_bundle.joblib`, `artifacts/semantic_encoder/`, `artifacts/deployment_config.json` and the delivered `upshift_ai/` together. `ModelService` reads the selected method automatically. `member2_backend_models.py` replaces the backend's schema-1 adapter; the supplied standalone API uses `/recommendations` and `resume_text`. See `START_HERE_MEMBER_2.md` for exact steps and sample responses. Historical listings are not current application opportunities. Member 2 must wire the current approved vacancy feed; Member 3 must test the connected Android journey.
'''))
    # Executed from project root against the exact staged delivery.
    code="""import sys, os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
candidates = [Path.cwd(), Path.cwd() / 'output/member2_handoff']
delivery = next(p for p in candidates if (p / 'artifacts/deployment_config.json').exists())
sys.path.insert(0, str(delivery))
from upshift_ai.handoff import ModelService
final_model = ModelService(delivery / 'artifacts')
request = json.loads((delivery / 'sample_request.json').read_text())
result = final_model.recommendations(request['resume_text'], request['top_k'])
expected = json.loads((delivery / 'sample_response.json').read_text())
assert result == expected
print('Export reload and sample prediction: PASS')
print('Selected method:', result['method'])
print(pd.DataFrame(result['matches'])[['job_id','title','similarity']].to_string(index=False))
"""
    cell=nbformat.v4.new_code_cell(code);execute_cell(cell,44);nb.cells.append(cell)
    nbformat.validate(nb)
    nbformat.write(nb,dest/'UpShift_Final_AI_Assisted.ipynb')

def execute_cell(cell,count):
    # Execute each added cell for real, preserving the original 41 saved outputs.
    global NOTEBOOK_NAMESPACE
    if 'NOTEBOOK_NAMESPACE' not in globals():NOTEBOOK_NAMESPACE={}
    buffer=io.StringIO()
    with contextlib.redirect_stdout(buffer):exec(compile(cell.source,'<final-notebook-cell>','exec'),NOTEBOOK_NAMESPACE)
    cell.execution_count=count
    cell.outputs=[nbformat.v4.new_output('stream',name='stdout',text=buffer.getvalue())]

if __name__=='__main__':main()
