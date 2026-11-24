# UpShift API

Firebase-authenticated AI inference and vacancy management, with Firestore persistence.

See [vacancy setup and test guide](../docs/VACANCY_BACKEND.md) for server configuration, company approval, submissions, moderation and selected-source collection.

Accounts, profiles, saved roles and learning progress use Firebase. There is no local password/session database or SQLite application database. The matching and sentiment endpoints require the separately configured trusted model artifact.

`POST /feedback` accepts a Firebase ID token and `{ "text": "...", "submission_id": "a UUID" }`. It saves the message to the server-only Firestore `feedback` collection and returns `status: received` after the write succeeds. Repeating the same ID and message does not create a duplicate. This endpoint is separate from `/sentiment`, which analyses tone without submitting a message. Deploy/restart the backend alongside the updated Android app; the new app cannot submit feedback to older backend versions. Feedback records are available to authorised project administrators through the Firebase console; there is no public feedback feed.

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
