"""Build the readable, self-contained Colab deliverable from the shared source."""
from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parent
cells=[]
def md(text):cells.append(nbf.v4.new_markdown_cell(text))
def code(text):cells.append(nbf.v4.new_code_cell(text))

md('''# UpShift: job matching, skill gaps and a fair sentiment comparison

This notebook is a reproducible research deliverable. It separates **job retrieval**, **skill evidence**, **CV-category classification**, and **sentiment analysis**. Sentiment analysis is a task; logistic regression is an algorithm that can perform that task. The fair comparison below is VADER versus a trained TF-IDF/logistic-regression sentiment classifier on the same labelled test examples.

The original notebook and three raw datasets are preserved. This copy embeds its Python source, trains from the raw data in a fresh Colab session, exports a backend-ready bundle, and checks inference. Saved outputs in this delivered copy were executed locally on CPU; they do not claim a Colab GPU run. Re-running without an existing bundle trains the pipeline. Existing artifacts are explicitly reported as reused.

**Interpretation:** historical jobs are research examples, not verified live Kenyan opportunities. Raw similarity and required-skill coverage are not hiring probabilities. Human recommendation relevance has not been labelled; category compatibility is reported only as a weak proxy.''')
code('''import os, sys
from pathlib import Path
try:
    from google.colab import drive
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
if IN_COLAB:
    from google.colab import drive
    drive.mount('/content/drive')
    DATA_ROOT = Path('/content/drive/MyDrive/UpShift_AI_Data')
    PROJECT_ROOT = DATA_ROOT / 'complete_ai_project'
else:
    PROJECT_ROOT = Path.cwd()
    DATA_ROOT = PROJECT_ROOT / 'data'
PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
os.chdir(PROJECT_ROOT)
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN', '1')
os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
os.environ.setdefault('HF_HOME', str(PROJECT_ROOT / '.cache/huggingface'))
print('Execution environment:', 'Google Colab' if IN_COLAB else 'local CPU')
print('Project folder:', PROJECT_ROOT)
''')
md('## 1. Dependencies and shared source\nThe next cells write the exact shared modules used by training, exports and inference. They make the notebook portable without a repository checkout. They only write inside the new project folder.')
code('''import subprocess
if IN_COLAB:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
                    'torch==2.9.0', '--index-url', 'https://download.pytorch.org/whl/cpu'], check=True)
else:
    print('Using the installed local project environment.')
(PROJECT_ROOT / 'upshift_ai').mkdir(exist_ok=True)
(PROJECT_ROOT / 'tests').mkdir(exist_ok=True)
''')
for filename in ['requirements.txt','README.md','run_pipeline.py','verify_export.py','THIRD_PARTY_NOTICES.md','MODEL-LICENSE-Apache-2.0.txt']:
    code('%%writefile '+filename+'\n'+(ROOT/filename).read_text(encoding='utf-8'))
for path in sorted((ROOT/'upshift_ai').glob('*.py'))+sorted((ROOT/'tests').glob('*.py')):
    code('%%writefile '+path.relative_to(ROOT).as_posix()+'\n'+path.read_text(encoding='utf-8'))
code('''if IN_COLAB:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'], check=True)
import json, joblib, pandas as pd
from IPython.display import display, Image
sys.path.insert(0, str(PROJECT_ROOT))
''')
md('''## 2. Original inputs and reproducible run

Place `Resume.csv`, `postings.csv`, and `skills_en.csv` directly in `MyDrive/UpShift_AI_Data` for Colab. Local execution can set `UPSHIFT_RESUMES`, `UPSHIFT_JOBS`, and `UPSHIFT_SKILLS`. No CV is sent to an inference service.

The seed is 42. The catalogue contains 6,000 sampled, unique early-career postings. Career models use stratified held-out CVs and cross-validation for selection. Sentiment uses official TweetEval train/validation/test splits, removes exact cross-split duplicates, and selects the method on validation before examining test scores. Semantic retrieval uses a pinned pretrained encoder; it is not trained on invented relevance labels.

Set `UPSHIFT_FORCE_TRAIN=1` to rebuild all models. The normal fresh Colab run trains automatically; this executed copy reloads the locally trained artifact and reports that fact.''')
code('''inputs = {
    '--resume-file': Path(os.environ.get('UPSHIFT_RESUMES', str(DATA_ROOT / 'Resume.csv'))),
    '--jobs-file': Path(os.environ.get('UPSHIFT_JOBS', str(DATA_ROOT / 'postings.csv'))),
    '--skills-file': Path(os.environ.get('UPSHIFT_SKILLS', str(DATA_ROOT / 'skills_en.csv'))),
}
force = os.environ.get('UPSHIFT_FORCE_TRAIN', '0') == '1'
if force or not (PROJECT_ROOT / 'artifacts/upshift_bundle.joblib').exists():
    missing = [str(p) for p in inputs.values() if not p.is_file()]
    if missing: raise FileNotFoundError('Missing original CSVs: ' + ', '.join(missing))
    command = [sys.executable, 'run_pipeline.py', '--max-jobs', '6000']
    for flag, path in inputs.items(): command.extend([flag, str(path)])
    subprocess.run(command, check=True)
    print('Training, evaluation and export executed in this notebook session.')
else:
    print('RELOADED completed local training artifacts; training was not repeated in this notebook session.')
bundle = joblib.load(PROJECT_ROOT / 'artifacts/upshift_bundle.joblib')
metadata = json.loads((PROJECT_ROOT / 'artifacts/metadata.json').read_text())
print('Schema:', bundle['schema_version'], '| indexed jobs:', len(bundle['jobs']))
print('Recorded environment:', metadata['python'], metadata['versions'])
print('Dataset SHA-256 fingerprints:', metadata['raw_file_sha256'])
display(pd.json_normalize(metadata['data_audit']))
''')
md('## 3. Career classification: supporting experiment\nThese labels describe CV categories, not whether an applicant will succeed at a job. The selected classifier does not filter the job catalogue or decide eligibility. In the saved short computing-profile example the classifier incorrectly predicts CHEF. This failure is retained for review; it demonstrates why this auxiliary classifier must not control the main recommendation path. Job retrieval independently returns computing roles.')
code('''display(pd.read_json('results/career_validation.json'))
display(pd.read_csv('results/career_test_metrics.csv'))
print('Selected by training cross-validation:', metadata['career_model'])
''')
md('''## 4. Sentiment: VADER versus logistic regression

Both methods predict negative, neutral, or positive sentiment on exactly the same held-out TweetEval examples. TF-IDF vocabulary and logistic regression are fit only on training texts; hyperparameters and VADER thresholds are selected on validation. The majority baseline shows class imbalance. Accuracy, macro F1, per-class reports and confusion matrices are retained. External English tweets are not a validation of Kenyan student feedback.''')
code('''print('Source and exact revision:', metadata['sentiment_benchmark'])
display(pd.read_csv('results/sentiment_validation.csv'))
display(pd.read_csv('results/sentiment_metrics.csv'))
print('Method selected on validation:', metadata['sentiment_winner_selected_on_validation'])
reports = json.loads(Path('results/sentiment_reports.json').read_text())
for name in ['VADER default', 'TF-IDF + logistic regression']:
    print(name)
    display(pd.DataFrame(reports[name]['classification_report']).T)
''')
md('''## 5. Job retrieval and skill gaps

TF-IDF lexical retrieval and MiniLM semantic retrieval are compared on the same catalogue and held-out queries. Category compatibility @5 is a **weak proxy**, not human relevance precision. Independent labels cannot be manufactured from the model's own predictions.

ESCO URI identifiers unify aliases. Explicit local extensions cover technologies missing from this ESCO version. Requirements, preferred skills and incidental mentions are separate; common negation is excluded. A missing skill means absent from the submitted text, not proof that the person cannot do it. The encoder represents long documents with up to four sampled windows; some content is omitted.''')
code('''display(pd.read_csv('results/retrieval_proxy_summary.csv'))
print(json.loads(Path('results/relevance_evaluation.json').read_text()))
print('Expired indexed postings:', int(bundle['jobs'].is_expired.sum()), '/', len(bundle['jobs']))
print('Independent relevance/skill accuracy remains unmeasured until humans annotate the provided templates.')
''')
code('''from upshift_ai.matching import recommend
from upshift_ai.semantic import load_encoder
from upshift_ai.sentiment import analyse_sentiment
encoder = load_encoder(PROJECT_ROOT / 'artifacts/semantic_encoder')
sample_cv = 'Computing student with Python, SQL, Kotlin, Android, Firebase and React.js project experience. I have no Java experience.'
for method in ['lexical', 'semantic']:
    result = recommend(bundle, sample_cv, method=method, encoder=encoder)
    print(method, result['status'])
    display(pd.DataFrame(result['matches'])[['title','location','similarity','skills_match_percentage','is_expired','eligibility_status']])
print('Live-only result:', recommend(bundle, sample_cv, live_only=True)['status'])
print('Supporting career prediction:', bundle['career_model'].predict([sample_cv])[0])
for text in ['Helpful and clear!', 'The app displays five jobs.', 'Terrible and disappointing.']:
    print(text, analyse_sentiment(bundle, text))
''')
md('## 6. Measured figures and export checks\nThese figures use the saved, measured test outputs. API checks run against the actual exported bundle, including offline semantic inference.')
code('''from upshift_ai.reporting import make_figures
for filename in make_figures(PROJECT_ROOT / 'results'):
    display(Image(filename=str(PROJECT_ROOT / 'results' / filename)))
subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q', '--basetemp', 'notebook_test_temp'], check=True)
subprocess.run([sys.executable, 'verify_export.py'], check=True)
display(json.loads(Path('results/export_verification.json').read_text()))
''')
md('''## 7. Independent validation and backend integration

`results/retrieval_annotation_queries.csv` contains the held-out query texts, and `retrieval_annotation_sheet.csv` is a shuffled, deduplicated union of retrieved pairs without method names. Reviewers assign `relevant` 0/1 based on role requirements and CV evidence, and review eligibility separately. Leave uncertain items blank until adjudicated. Unlabelled pairs are never counted as negative. `human_evaluation.evaluate_relevance` reports Precision@5 only for completely judged top-five lists.

`skill_annotation_template.csv` separately supports manual skill-set precision/recall. Blank gold fields mean unannotated; `[]` means a reviewed document with no applicable skills. Context and span accuracy require further annotation. Keep CV text private when sharing these files.

The exported API accepts profile text through `POST /recommend`, and feedback text through `POST /sentiment`. `GET /health` reports schema and catalogue status. Both POST routes require the local integration token. The backend should replace that token with authenticated user requests before release. A generative AI coach, live eligible job feed, and Android/backend connection are separate integration work, not features silently implemented by a sentiment classifier.''')
code('''from upshift_ai.human_evaluation import skill_annotation_template
from upshift_ai.data import load_resumes
if inputs['--resume-file'].is_file():
    resumes, _ = load_resumes(inputs['--resume-file'])
    _, train, test, _ = joblib.load('artifacts/career_checkpoint.joblib')
    skill_annotation_template(bundle, resumes, test, Path('results/skill_annotation_template.csv'))
print('Bundle:', PROJECT_ROOT / 'artifacts/upshift_bundle.joblib')
print('Offline encoder:', PROJECT_ROOT / 'artifacts/semantic_encoder')
print('Backend handoff:', PROJECT_ROOT / 'upshift_ai_handoff.zip')
print('API contract and operation instructions: README.md')
''')
md('''## Sources and limits

- Original project-supplied Resume.csv, postings.csv and ESCO skills_en.csv: keep the original dataset attribution and terms.
- [TweetEval](https://github.com/cardiffnlp/tweeteval): official sentiment splits; exact downloaded source revision is recorded in metadata. Follow the original dataset terms.
- [NLTK VADER](https://www.nltk.org/api/nltk.sentiment.vader.html): lexicon sentiment baseline.
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): Apache-2.0 pretrained encoder, pinned revision.
- [scikit-learn](https://scikit-learn.org/stable/): fitted classifiers, pipelines and evaluation.

This completes the reproducible prototype model pipeline and comparison. It does not establish hiring probability, student fairness, Kenyan eligibility, current vacancy availability, or human relevance accuracy. Those require appropriate target-domain labels and data. Models and data fingerprints are saved for review.''')
notebook=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.14'}})
out=ROOT/'notebooks/UpShift_AI_Complete.ipynb';out.parent.mkdir(exist_ok=True)
nbf.write(notebook,out)
print(out)
