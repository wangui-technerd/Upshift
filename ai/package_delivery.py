"""Package completed, verified outputs without raw CSVs or training caches."""
from pathlib import Path
import json,hashlib,zipfile,shutil,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import pandas as pd
from upshift_ai.api import create_app

def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def package():
    results=ROOT/'results';artifacts=ROOT/'artifacts'
    verification=json.loads((results/'export_verification.json').read_text())
    assert verification['status']=='passed'
    notebook=ROOT/'notebooks/UpShift_AI_Complete_Executed.ipynb'
    assert notebook.is_file()
    for name in ['MODEL-LICENSE-Apache-2.0.txt','THIRD_PARTY_NOTICES.md']:
        shutil.copy2(ROOT/name,artifacts/name)
    upstream=ROOT/'.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41/README.md'
    if upstream.exists():shutil.copy2(upstream,artifacts/'semantic_encoder/UPSTREAM_MODEL_CARD.md')
    contract=create_app(artifacts,token='documentation-only').openapi()
    (results/'openapi.json').write_text(json.dumps(contract,indent=2))
    sentiment=pd.read_csv(results/'sentiment_metrics.csv')
    career=pd.read_csv(results/'career_test_metrics.csv')
    proxy=pd.read_csv(results/'retrieval_proxy_summary.csv')
    def table(df):
        cols=list(df.columns)
        lines=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
        for row in df.itertuples(index=False,name=None):
            lines.append('| '+' | '.join(f'{v:.4f}'if isinstance(v,float)else str(v)for v in row)+' |')
        return '\n'.join(lines)
    report='''# UpShift AI: measured results and handoff

The delivered notebook was executed locally on CPU, reloading models trained by the companion pipeline. Its outputs are actual measured results. The notebook also trains from scratch in a fresh Colab project folder. The original notebook is preserved.

## Sentiment comparison

Same 12,277 deduplicated held-out TweetEval sentiment texts; selection was frozen on validation. This external English-tweet benchmark does not measure Kenyan student-feedback performance.

'''+table(sentiment[['method','accuracy','macro_f1']])+'''

TF-IDF/logistic regression was selected on validation. Sentiment is separate from job ranking and never measures a person's employability.

## Supporting CV category classification

'''+table(career)+'''

The model was selected on training cross-validation. Category accuracy is not job-matching accuracy; the classifier does not restrict recommendations. A short computing-profile example is still misclassified as CHEF. This known failure is retained, and the auxiliary classifier is not used by the recommendation endpoint.

## Retrieval comparison

'''+table(proxy)+'''

Category compatibility @5 is only a weak proxy. Neither method has measured independent human relevance accuracy. Human annotation templates and strict evaluation helpers are provided in the project results/source. Do not present these proxy scores as recommendation accuracy.

The index contains 6,000 historical early-career postings; all are expired and eligibility is unverified. Live-only requests correctly return no matches. A current eligible job feed is needed for product release.

## Verification and files

- 27 unit/API regression tests passed; the executed notebook reruns them.
- Actual exported-model verification passed offline: lexical and semantic predictions, stable descending rank, expiry/eligibility metadata, abstention on unknown vocabulary, authentication, request validation and sentiment inference.
- `api.py`, `upshift_ai/`, `upshift_bundle.joblib`, `semantic_encoder/`: local backend inference.
- `results/openapi.json`: exact request/response contract.
- `UpShift_AI_Complete_Executed.ipynb`: readable source, executed examples, measured charts, evaluation and reproduction instructions.
- `PROJECT_GUIDE.md`: source data, score meanings, environment and operation details.
- `research_source/`: reproducible runner, tests and shared modules; supply the three original CSVs to retrain.
- `SHA256SUMS.json`: artifact/file checksums.

To run the exported API, install requirements, set `UPSHIFT_ARTIFACT_DIR` to the extracted handoff directory and `UPSHIFT_API_TOKEN` to a local secret, then run `python -m uvicorn api:app --host 127.0.0.1 --port 8000` from that directory. POST routes require `Authorization: Bearer <local token>`. The backend should use proper user authentication before public release; do not embed the shared token in Android.

Remaining validation: independent CV/job relevance and contextual skill annotations, Kenyan student-feedback testing, and verification of a current eligible job source. A generative conversational coach and app/backend wiring are separate from this model deliverable.
'''
    (results/'MODEL_HANDOFF.md').write_text(report,encoding='utf-8')
    entries={}
    for path in artifacts.rglob('*'):
        if path.is_file()and'checkpoint'not in path.name and'__pycache__'not in str(path):entries[path.relative_to(artifacts).as_posix()]=path
    entries['PROJECT_GUIDE.md']=ROOT/'README.md'
    entries['MODEL_HANDOFF.md']=results/'MODEL_HANDOFF.md'
    entries[notebook.name]=notebook
    names=['sentiment_metrics.csv','sentiment_validation.csv','sentiment_reports.json','sentiment_data_audit.json','career_test_metrics.csv','career_validation.json','career_reports.json','retrieval_proxy_summary.csv','relevance_evaluation.json','run_summary.json','initial_training_run.json','export_verification.json','openapi.json']
    for name in names:
        if(results/name).exists():entries['results/'+name]=results/name
    for path in results.glob('*.png'):entries['results/'+path.name]=path
    for name in ['run_pipeline.py','verify_export.py','requirements.txt']:
        entries['research_source/'+name]=ROOT/name
    for folder in ['upshift_ai','tests']:
        for path in (ROOT/folder).glob('*.py'):entries['research_source/'+folder+'/'+path.name]=path
    checksums={name:sha(path)for name,path in sorted(entries.items())}
    (results/'SHA256SUMS.json').write_text(json.dumps(checksums,indent=2))
    target=ROOT/'upshift_ai_handoff.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED)as archive:
        for name,path in sorted(entries.items()):archive.write(path,name)
        archive.write(results/'SHA256SUMS.json','SHA256SUMS.json')
    with zipfile.ZipFile(target)as archive:
        assert archive.testzip()is None
        assert set(entries).issubset(archive.namelist())
    delivery=ROOT.parent/'output/ai';delivery.mkdir(parents=True,exist_ok=True)
    for path in [target,notebook,results/'MODEL_HANDOFF.md']:
        shutil.copy2(path,delivery/path.name)
    manifest={'zip_sha256':sha(target),'zip_bytes':target.stat().st_size,'notebook_sha256':sha(notebook),'file_count':len(entries)+1}
    (delivery/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2),flush=True)
    return delivery

if __name__=='__main__':package()
