# Backend API

Setup: [backend/README.md](../backend/README.md). The running server exposes its complete request and response schemas at `/docs` and `/openapi.json`.

Firebase Authentication handles email/password, Google sign-in and password resets in Android. Profiles, saved roles and learning progress use the Firebase SDK and Firestore rules; these are not Python REST endpoints.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Service and optional model readiness |
| POST | `/recommendations` | Firebase-authenticated `{resume_text, top_k}`; top_k defaults to 5 (1–20) |
| POST | `/sentiment` | Firebase-authenticated `{text}` |
| POST | `/listings/companies` | Register a company for review |
| GET | `/listings/companies/mine` | Owned company registrations |
| GET | `/listings/companies` | Approved companies |
| POST | `/listings/companies/{company_id}/vacancies` | Submit or revise an owned vacancy |
| GET | `/listings/submissions/mine` | Owned submissions |
| POST | `/listings/submissions/{listing_id}/withdraw` | Withdraw an owned submission |
| GET | `/listings/vacancies` | Publicly eligible published vacancies |

All routes except `/health` require `Authorization: Bearer <Firebase ID token>`. Administrator routes under `/listings/admin/` additionally require the verified `upshift_admin` custom claim. Company ownership, approval, revision checks, collection controls and administrator operations are described in [VACANCY_BACKEND.md](VACANCY_BACKEND.md). Responses use `Cache-Control: no-store`.

Model endpoints return 503 when the required trusted notebook artifact/model is unavailable. Recommendation scores represent text similarity, not hiring probability. The API does not train a model or automatically publish collected adverts.

The schema-2 recommendation response includes its selected ranking method and catalogue status. With the Member 2 handoff installed, the catalogue is historical research data. Live vacancies are served separately by the listings routes.
