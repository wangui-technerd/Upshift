# Backend API

Setup: [backend/README.md](../backend/README.md). The running server exposes its complete request and response schemas at `/docs` and `/openapi.json`.

Firebase Authentication handles email/password, Google sign-in and password resets in Android. Profiles, saved roles and learning progress use the Firebase SDK and Firestore rules; these are not Python REST endpoints.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Service and optional model readiness |
| POST | `/recommendations` | Firebase-authenticated `{resume_text, top_k?, catalogue?, location?, experience_months?}`. Defaults to live vacancies and five results (1–20). |
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

### Recommendation catalogues

- `live` (default) ranks Firestore vacancies that are published for application by an approved company. Expiry uses the Africa/Nairobi calendar date, inclusive of the deadline. A reviewed vacancy may have an open deadline. An optional `location` matches the full advertised location or a comma-separated component, ignoring case and repeated whitespace. The API excludes known shortfalls against an explicit minimum experience threshold. It leaves missing or ambiguous experience evidence as `unknown`. A comparison of experience months does not verify an applicant's overall eligibility. Duplicate canonical source URLs appear once.
- `research` explicitly requests the historical demo catalogue. Omit `location` and `experience_months` for this mode. Research results have blank application and posting URLs and `ready_for_live_application: false`.
- With no eligible live matches the route returns `status: no_match` and `matches: []`. Firestore unavailability returns HTTP 503. Neither case falls back to research vacancies.

### Vacancy experience and recommendation fields

Recruiters or admins can set `minimum_experience_months` on a vacancy. Existing
vacancies can also supply a standalone explicit minimum in the requirements or
eligibility list. The API leaves ambiguous or role-specific experience text for
the student to review. A student can send zero months or omit
`experience_months` when it is unknown.

Live matches include the originating vacancy ID, location, expiry date,
application URL, requirements and eligibility text. The
`experience_requirement_status` field is either `meets_minimum` or `unknown`.
