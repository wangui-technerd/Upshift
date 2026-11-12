# Team integration boundaries

The current local frontend runs without the backend/model. The following interfaces are replaceable:

- `OpportunitiesRepository`: employer listings and eligibility metadata.
- `MatchScorer`: skill-match percentages. Replace exact skills coverage with the agreed model interpretation; retain a clear score definition.
- `CoachRepository`: contextual guidance. Local responses are deterministic. The real adapter should expose asynchronous loading, retry, network errors and streamed results where supported.
- `AccountGateway`: sign-in, sign-up and reset. Current result is Unavailable and does not fabricate sessions. Never put real credentials in preferences. Use authenticated account access and secure token storage when connected.

These are proposals, not an existing API contract. Before live calls, move repositories into lifecycle-owned ViewModels with suspend operations and loading/success/empty/error states. Do not make HTTP calls in composables or block the main thread.

## Recommended opportunity payload

Stable ID, title, employer, description, required skill IDs, responsibilities, requirements, location, remote mode, eligible countries, work authorisation, study level, experience, deadline, source URL and application URL. Unknown eligibility must not be treated as confirmed eligibility. Current fixture listings intentionally have no application submission.

## Recommendations

Role ID, score plus definition, matched skills, missing skills, explanation and model version. A match score is not a hiring probability. Distinguish absent evidence from a demonstrated lack of skill.

## Suggested operations

GET /opportunities?query=&cursor=; GET /opportunities/{id}; GET/PATCH /me/profile; POST /recommendations; GET/PUT/DELETE /me/saved/{roleId}; GET/PATCH /me/plan; account sign-in/sign-up/reset endpoints.

Use HTTPS, request deadlines, account ownership checks and structured errors. Preserve drafts on failure. Send only necessary profile fields to the model; contact information is not required for skill matching.

## Learning and local data

Completion currently requires a short reflection, persists evidence and earns 25 XP per distinct completed skill. Completing a task never silently changes profile skills or a score. Streak dates use Africa/Nairobi. For production use stable taxonomy and task IDs instead of display labels, and define account-scoped migration, evidence sync and conflict handling. Existing profiles can continue locally while auth is unavailable.

CV export remains template-based and local, independent of AI. Open a validated HTTPS employer URL only after real opportunity data is connected.

Certificate-course mapping lives in `Courses.kt`. Preserve HTTPS provider links, group duplicate programme recommendations and do not equate in-app reflection completion with an externally verified credential. A future provider/backend completion integration should carry a verifiable credential URL or provider completion record with consent.
