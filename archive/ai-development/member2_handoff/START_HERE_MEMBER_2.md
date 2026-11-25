# Member 2: start here

Prepared 22 November 2026. Review type: **one AI-assisted reviewer**. No independent human validation or inter-reviewer agreement is claimed.

## What you receive

- `artifacts/upshift_bundle.joblib`: trusted schema-2 fitted models and 6,000 historical research vacancies.
- `artifacts/semantic_encoder/`: offline MiniLM encoder; keep the whole folder.
- `artifacts/deployment_config.json`: selected ranking method `semantic`. The bundle itself is unchanged; the config and service fix deployment selection.
- `upshift_ai/handoff.py`: `ModelService`, the supported Python entry point.
- `member2_api.py`: working backend-only local service with `/health`, `/recommendations`, `/sentiment`.
- `member2_backend_models.py`: replacement for the old schema-1-only `backend/models.py`.
- `UpShift_Final_AI_Assisted.ipynb`: original 41-cell executed clear notebook plus executed final review and handoff checks. Earlier clear-results toy exports are not this deployment format; use the schema-2 files above.
- `student_review/ai_assisted/`: 112 ratings, reasons, reviewer disclosure, per-profile metrics and method comparison. Human reviewer sheets remain blank.
- `results/`: original benchmark results, contextual sentiment errors, exact export checks.
- `sample_request.json`, `sample_response.json`, `sample_candidate_ranking.json`, `openapi.json`, pinned requirements and checksums.

## Evaluation in plain language

We compared TF-IDF cosine retrieval and MiniLM semantic retrieval on twelve fictional students across six fields. Six profiles selected the method and six reported held-out test performance. Labels were assigned by one AI assistant using the frozen 0/1/2 rubric, not by people. Requirement-focused excerpts were used, so this is a preliminary review rather than an exhaustive human audit. No labels were changed after results were calculated.

MiniLM won validation pooled NDCG@5. On the test profiles: P@5 **0.333**, pooled NDCG@5 **0.774**, at-least-one-good-match coverage **83.3%**. P@5 means the fraction of the five recommendations judged a good fit; it is not overall model accuracy. These modest results expose real failures, including experienced roles labelled entry level, field confusion and no relevant result for some student cases. Method choice is provisional pending representative independent review. Pooled NDCG measures ordering within the pooled top-five candidates, not the full catalogue.

Sentiment is a separate TF-IDF/logistic-regression classifier with VADER comparison in the original benchmark. On 20 AI-authored app-feedback examples it scored 80.0% accuracy and 0.801 macro F1. Inspect `results/sentiment_app_checks.csv` for every mistake. This small synthetic diagnostic is not a human-labelled app benchmark. Keep sentiment optional; it must not affect job ranks or perceived employability. No generative coach is supplied. Skill extraction uses ESCO/manual aliases and contextual rules, not a trained skill-gap classifier. Course recommendation links remain curated app/backend data.

## Install and run (Python 3.12 tested)

From the extracted handoff directory in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:UPSHIFT_API_TOKEN = "choose-a-private-backend-token"
.\.venv\Scripts\python.exe -m uvicorn member2_api:app --host 127.0.0.1 --port 8000
```

If an existing environment has the torchvision `nms` import error, use this fresh environment. The text encoder does not require torchvision or torchaudio. A clean-machine dependency install has not been repeated for this handoff; inference was checked offline in the existing pinned environment. Do not put the service token or joblib loader in Android. Android authenticates to your Firebase-protected backend; your backend may call this service with its private token.

```powershell
$headers = @{ Authorization = "Bearer $env:UPSHIFT_API_TOKEN" }
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
- Full bundle reload, selected-method HTTP inference, deterministic order, validation, auth, historical live-only exclusion, sentiment, candidate ranking and backend adapter checks passed offline. See `results/member2_verification.json`. Cold selected-method HTTP inference took 5.36s on this local CPU, including encoder load; this is not a phone benchmark. Load once, reuse the service, and show loading/error states in Android.
- `SHA256SUMS.json` records every shipped file. Load only these trusted project-produced joblib files.

## Ownership after handoff

Member 1's AI-assisted evaluation and technical export are complete for this scope. Independent human validation remains explicitly pending. Member 2 owns Firebase/live vacancy wiring, deployment, backend auth and integrated API checks. Member 3 owns Android API wiring, loading/error states and final physical-phone tests. The existing Android main feed still needs replacement of its local scorer/sample repository with the connected response. No live production readiness is claimed here.
