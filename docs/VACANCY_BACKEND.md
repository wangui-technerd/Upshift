# Vacancy backend: setup and first test

The FastAPI service uses Firebase Authentication and Firestore. It manages company ownership, approval, submission review, publication, withdrawal and selected-source collection. It can run without the matching/sentiment model. Swagger at `/docs` is the initial company/operator interface; a dedicated partner portal has not been built.

## Start the API

From the Upshift repository folder, using PowerShell:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
$env:UPSHIFT_FIREBASE_PROJECT_ID='YOUR_FIREBASE_PROJECT_ID'
$env:GOOGLE_APPLICATION_CREDENTIALS='C:\path\outside-repository\service-account.json'
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

The project must match the Android Firebase configuration and have Firestore enabled. Use server credentials outside Git; google-services.json is client configuration and cannot replace them. Prefer workload identity for deployment. Environment variables must be set before startup; `.env` files are not loaded automatically.

Open http://127.0.0.1:8000/docs. Authorize with a Firebase ID token, without another `Bearer` prefix. Obtain/refresh tokens using Firebase sign-in. Passwords and account sessions remain owned by Firebase.

For your operator account, use the trusted server-side command, then sign in again:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.listings_admin --uid YOUR_FIREBASE_ACCOUNT_UID
```

This grants the `upshift_admin: true` custom claim. Add `--revoke` to remove it. Existing unrelated claims are preserved. Ordinary accounts cannot grant themselves this privilege through the API.

## First end-to-end test

1. As a signed-in representative, `POST /listings/companies` with a name, HTTPS website, description and offerings (`vacancies`, `training`, `mentorship`). Ownership comes from the token; registration starts pending.
2. As an operator, independently verify the representative/company, then `POST /listings/admin/companies/{id}/review` with `{"approved":true}`. A registration does not establish a real partnership.
3. As the owner, `POST /listings/companies/{id}/vacancies` with an actual source URL, title, description, location, career_level, skills, eligibility and optional deadline/application_url. Supported levels: student_attachment, internship, graduate_trainee, entry_level. Use the same source URL to revise it.
4. Read `/listings/admin/submissions`. Correct any extracted fields with `PUT /listings/admin/submissions/{id}`, keeping the same source URL.
5. Publish with `POST /listings/admin/submissions/{id}/review`, body `{"revision":1,"decision":"publish","note":"Source and eligibility checked."}`. Use the actual current revision. Missing eligibility and past deadlines block publication; stale revisions return 409.
6. Confirm the vacancy appears in `/listings/vacancies` and in the signed-in Android app. Public projections include source and company background; private owner/review information stays server-side.
7. As the owner, `POST /listings/submissions/{id}/withdraw`. Confirm the advert disappears. Operator review decisions also support `reject` and `close`.

Changed submissions hide the public version until reviewed again. Identical submissions keep their existing status and ID. Company suspension withdraws its published projections; reapproval does not automatically republish them. Closing dates use the Africa/Nairobi calendar day, inclusive of that day.

Additional list routes: `/listings/companies/mine`, `/listings/companies`, `/listings/submissions/mine`, `/listings/admin/companies`, `/listings/admin/sources`. List endpoints accept `limit` (1–100) and `after`; follow `next_cursor` even if filtering leaves a page empty. All routes require authentication; `/admin/` routes require the operator claim.

## Configure collection

Before API/worker startup, allow only selected public HTTPS source hosts:

```powershell
$env:UPSHIFT_SOURCE_HOSTS='careers.selected-company.com,selected-company.applytojob.com'
```

Register a source using `POST /listings/admin/companies/{id}/sources` with a real `url`, `enabled:true` and `extractor:"jsonld"`. Sources default to disabled and the company must be approved before collection. Run one using `POST /listings/admin/sources/{id}/collect`.

The implemented extractor handles structured `JobPosting` JSON-LD and creates review drafts. It does not invent missing skills or eligibility and never publishes automatically. It recognises early-career titles, but an operator must check experience and study requirements. Repeated unchanged collection preserves operator corrections.

The fetcher checks robots restrictions, public DNS destinations, permitted hosts, timeouts and response size. Redirects and unsupported crawl delays require review. Use restricted network egress in deployment as an additional boundary against DNS changes. JavaScript-only pages, PDFs, unstructured text and ATS-specific feeds need further extraction adapters; unsupported pages report `needs_adapter`.

404/410 hides a publication only for the exact configured source advert as availability unverified. Disappearance from an index, 403 or a timeout does not prove closure. This worker checks configured pages; it does not yet crawl every discovered application URL or guarantee full company coverage.

Run once from an external scheduler, or use a dedicated polling process:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.listings_worker
.\backend\.venv\Scripts\python.exe -m backend.listings_worker --interval 21600
```

The second command runs every six hours; choose one approach and run only one worker initially. Each run also archives expired publications. An operator can call `POST /listings/admin/expire` separately. No scheduler, live company sources or deployment has been enabled automatically.

## Firestore and Android

Public projections are `companies` and `opportunities`. Private collections are `partner_companies`, `listing_submissions`, `vacancy_sources` and `listing_audit`. Deploy the repository Firestore rules to the intended project before live use. Clients cannot write these collections; API authorization protects Admin SDK operations, which bypass client rules.

Android already listens to `opportunities`. It accepts published adverts and hides pending-review, archived and availability-unverified records. Bundled research candidates still have unconfirmed labels. Matching URLs prevent a bundled/publication duplicate when IDs differ. A saved bundled role whose ID changes to a cloud ID may need saving again.

For local Firebase emulators, use project `demo-upshift`, `FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099` and `FIRESTORE_EMULATOR_HOST=127.0.0.1:8080`. Emulator configuration refuses live project IDs or nonlocal destinations. For production, configure restricted server IAM and ingress rate limits; the existing bounded process limiter is only a basic guard.

## Checks

```powershell
.\backend\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
```

API/unit tests use an injected memory store and simulated network responses. They do not prove real Firestore credentials, deployed rules or employer-site compatibility. Test the full submit → review → publish → withdraw journey in an emulator or separate development project before production.
