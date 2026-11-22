# UpShift API

Firebase-authenticated AI inference and vacancy management, with Firestore persistence.

See [vacancy setup and test guide](../docs/VACANCY_BACKEND.md) for server configuration, company approval, submissions, moderation and selected-source collection.

Accounts, profiles, saved roles and learning progress use Firebase. There is no local password/session database or SQLite application database. The matching and sentiment endpoints require the separately configured trusted model artifact.

From the repository folder in PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Set UPSHIFT_FIREBASE_PROJECT_ID and server credentials before startup. Open http://127.0.0.1:8000/docs for endpoint details. Use Firebase ID tokens; management routes require the operator custom claim. Environment files are reference templates, not automatically loaded.

No source polling, claims assignment, Firestore publication or deployment happens merely by starting the API. See the guide for explicit operator steps.

## Enable the Member 2 recommendation model

Use Python 3.12 and the original, trusted Member 2 handoff. Extract its
`artifacts/` folder together, keeping `upshift_bundle.joblib`,
`deployment_config.json` and the full `semantic_encoder/` directory in the
same parent. Keep these files outside Git. The supplied configuration selects
the offline MiniLM semantic encoder.

From the repository root, with your Firebase environment already configured:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-model.txt
$env:UPSHIFT_MODEL_PATH = 'C:\path\to\handoff\artifacts\upshift_bundle.joblib'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Check `GET /health` for `model_status: ready`. If it reports `unavailable`,
check the server log for the loading error. To check the handoff's sample
ranking, add `"catalogue": "research"` to
`sample_request.json` and send it to `POST /recommendations` with a Firebase ID
token from your project as the Bearer token. The method and ordered job IDs
should match `sample_response.json`. Without a catalogue override the endpoint
ranks eligible Firestore vacancies.

For Cloud Run configuration and the post-deployment smoke test, see the
[deployment guide](../docs/DEPLOY_BACKEND.md).
