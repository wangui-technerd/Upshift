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
