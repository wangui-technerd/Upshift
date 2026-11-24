# UpShift NLP model handoff

## Main notebook for review

Use **[MiniLM_Final.ipynb](notebooks/MiniLM_Final.ipynb)**. It contains the full workflow with executed results, five figures and short numbered explanations. It embeds the shared model functions and saves the same schema-2 bundle and encoder format loaded by the app. It requires the three original CSVs; TweetEval and the pretrained encoder are downloaded on a fresh run.

[Open in Colab](https://colab.research.google.com/github/CoIlins/SemProject_MLEngine/blob/main/MiniLM_Final.ipynb) · [AI submission repository](https://github.com/CoIlins/SemProject_MLEngine) · [Original base notebook](notebooks/LogisticRegression_Base.ipynb)

Saved outputs and five figures are included for assessment; no setup is needed to read them. Step 1 is a short optional cell for rerunning with your own folder containing the three original CSVs. See the [run instructions](https://github.com/CoIlins/SemProject_MLEngine#read-or-rerun).

Earlier clear-steps notebooks and the standalone service described below remain development history. Use the final notebook for assessment and [the current backend guide](../backend/README.md) for Android integration.

This project contains two separate NLP tasks:

1. **Job retrieval and skill evidence:** TF-IDF lexical matching and a local pretrained sentence encoder; ESCO concept IDs with explicit local extensions.
2. **Sentiment comparison:** VADER versus a supervised TF-IDF/logistic-regression classifier on independently labelled TweetEval sentiment data. Sentiment is never used to rank employability.

The earlier career-category experiment remains in the base notebook; it is not part of the final job-ranking walkthrough. A conversational generative coach is not implemented by these classifiers.

## Run

Python 3.12 was used. Install `requirements.txt` in a dedicated environment. For CPU-only PyTorch, install torch from the official CPU index before installing the remaining requirements.

```powershell
python run_pipeline.py --resume-file "path/to/Resume.csv" --jobs-file "path/to/postings.csv" --skills-file "path/to/skills_en.csv" --max-jobs 6000
python -m pytest tests
python verify_export.py
```

A fresh run trains and evaluates from the three original raw CSVs. It also downloads the public sentiment benchmark and pretrained encoder. No CV is sent to a hosted inference API. Local CPU worker count is limited to two. `--reuse-checkpoints` is an explicit recovery option for the same data and unchanged career/sentiment classifier code only; leave it off after changing training data or preprocessing.

The corrected Colab notebook embeds the shared source so it can run without a GitHub checkout. It uses the original files under `MyDrive/UpShift_AI_Data`, writes into its own project folder and preserves the original notebook/data.

## Outputs

- `artifacts/upshift_bundle.joblib`: lexical index, job metadata, stable skill lookup, career classifier and trained sentiment model.
- `artifacts/semantic_encoder/`: the actual saved encoder, for offline inference.
- `results/`: measured comparisons, confusion matrices, exact splits/data fingerprints and annotation templates.
- `upshift_ai_handoff.zip`: Python service code, models, requirements and key results.

Raw datasets, caches, trained artifacts and large result files are ignored by Git. Do not load joblib from an untrusted source. The recorded environment versions and source revisions accompany the export.

## Local API

Unzip the handoff, install requirements, set `UPSHIFT_ARTIFACT_DIR` to that folder and `UPSHIFT_API_TOKEN` to a local secret. From the handoff directory:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

- `GET /health`
- `POST /recommend`: `{"resume_text":"...","top_k":5,"method":"lexical"}`; method can also be `semantic`.
- `POST /sentiment`: `{"text":"The recommendations were helpful."}`.

Both POST routes require `Authorization: Bearer <local token>`. The shared token is for local integration only. Public deployment needs verified per-user authentication, HTTPS, limits and operational monitoring; never embed a shared service secret in Android. No public endpoint is deployed by the notebook.

The app can construct `resume_text` from its existing profile fields. PDF/DOCX parsing belongs in a separate validated upload/extraction layer and is not needed for the profile-text contract.

## Scores and eligibility

`similarity` is a raw retrieval score. `skills_match_percentage` is separately computed from explicitly detected required skills; it is null when requirements cannot be established. Neither is a probability of employment. Matched, unmentioned required, unmentioned preferred and other-mentioned skills are separate fields, each with stable IDs.

Results also carry location, work type, experience, dates, expiry and eligibility status. The current catalogue is historical: all sampled postings were expired at this run. `live_only=true` excludes expired or unverified opportunities. This is a complete research pipeline, not a claim of an available Kenyan job feed.

## Evaluation boundaries

The classifier and sentiment comparisons use distinct labels and splits. TweetEval is an external English-tweet benchmark, not validated Kenyan student/app feedback. Job-category compatibility is a **weak proxy**, not independently established recommendation relevance. Human relevance and skill-span evaluation templates are supplied rather than inventing ground truth. Long texts are represented using up to four sampled chunks; this is recorded, not described as full-document coverage.

## Sources

- Original Resume.csv, postings.csv and skills_en.csv supplied by the project; retain their original dataset attribution/terms.
- TweetEval / SemEval-2017 sentiment: https://github.com/cardiffnlp/tweeteval (exact revision recorded).
- VADER: https://www.nltk.org/api/nltk.sentiment.vader.html
- Semantic encoder: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (exact revision recorded; Apache-2.0 model).
- scikit-learn: https://scikit-learn.org/stable/
