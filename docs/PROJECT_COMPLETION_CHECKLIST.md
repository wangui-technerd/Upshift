# UpShift project completion checklist

This is our historical working checklist, not the current submission status. We keep our current setup and project overview in the [main README](../README.md).

Reviewed 19 November 2026. Owner names below describe roles; assign the three group members to them.

Use `[x]` only with the stated evidence. Open **P0** tasks block the connected final build; **P1** tasks are recommended submission-quality checks. **Scope** items are conditional, not assumed lecturer requirements. An implemented feature is not automatically verified end to end.

## Repository review

| Branch | Reviewed commit | Work present |
| --- | --- | --- |
| android-frontend | a577c32 | Student frontend and all-in-one AI notebook |
| android-backend | 52fa3bd | Firebase integration, AI adapter and moderated vacancy API |
| android-recruiter | b1f7b4a | Includes backend work plus native recruiter workspace |

The frontend pull was already up to date. Backend and recruiter branches were fetched and inspected without merging. The current working branch remains android-frontend. The recruiter branch already includes the backend commit. The user then supplied a newer successful Colab run; it is included with this checklist update.

**Confirmed blocker:** the latest local notebook artifact was passed to the current backend loader and returned `unavailable`. Its saved field layout differs from the loader requirements. This is an integration mismatch, not a reason to retrain everything.

**Evidence limits:** 20 backend unit tests passed in an isolated snapshot on this review. Live Firebase setup, a merged Android APK and real model-to-Android results were not established by those tests. The user confirms the Colab import error is fixed.

## Existing work with evidence

- [x] **C01 — Android:** Student UI implemented: splash, welcome, onboarding, Matches, details, Growth, You, menus and saved-role RecyclerView. Baseline emulator evidence is in docs/VERIFICATION.md.
- [x] **C02 — Android:** Prototype styling, score rings, learning streak, course links, editable CV and PDF export are implemented. Latest integrated build still needs regression testing.
- [x] **C03 — Backend:** Firebase email/password, reset, Google sign-in and account-scoped profile/progress sync code exist on the backend/recruiter branches. Live configuration is not confirmed by this review.
- [x] **C04 — Backend:** Company registration, approval, vacancy moderation, publication, withdrawal and selected-source collection code exist.
- [x] **C05 — Android:** Native recruiter workspace exists: sign-in, company registration, vacancy drafts, submission status and withdrawal. Full APK and live journey verification remain open.
- [x] **C06 — Backend:** 20 backend unit tests passed in a fresh isolated review snapshot. They use test doubles/memory storage and do not establish live Firebase or model integration.
- [x] **C07 — AI:** One notebook contains cleaning, EDA, model comparisons, evaluation, examples, saving and an API demonstration. The supplied final Colab run has 41 executed code cells with no saved errors.
- [x] **C08 — AI:** Trained exports and result tables exist locally. CV classification, job retrieval and sentiment are evaluated separately; sentiment is not an employability score.
- [x] **C09 — AI:** The Colab import error is resolved; confirmed by the user on 19 November 2026.
- [x] **C10 — Team:** A sourced opportunity research catalogue, project setup documents and a plain-language notebook walkthrough exist. Research records still need current-source review before live use.

## Remaining work

### 1 Combine the work

- [ ] **M01 [P0] — Integrator:** Merge the recruiter work into the final submission branch, preserving the AI notebook and frontend refinements. Recruiter already includes backend; resolve shared README and configuration changes, then build the combined app.
- [ ] **M02 [P0] — AI and Backend:** Make the final exported model file and backend loader agree. The notebook writes job_tfidf and has no schema_version/job_skills; the backend expects retriever, schema_version 1 and job_skills. Done when the actual export loads and predicts.
- [ ] **M03 [P0] — Integrator:** Agree one production API contract. Android currently calls POST /recommendations with resume_text and Firebase tokens; the teaching notebook demonstrates /recommend with cv_text and a local token. Document the adapter and test actual authenticated requests.
- [ ] **M04 [P0] — AI and Backend:** Make model results refer to the same current published job IDs used by Android. Define index refresh after publication, edits, expiry and withdrawal; keep historical research jobs out of any promised live feed.

### 2 Finish the AI evidence

**22 November AI handoff update:** `output/UpShift_Member2_Handoff_AI_Assisted.zip` now contains the schema-2 export, offline encoder, selected-method config, a replacement backend loader, verified sample requests/responses and `UpShift_Final_AI_Assisted.ipynb`. One disclosed AI-assisted review covers 112 pairs; MiniLM won validation pooled NDCG@5. Its test P@5 is 0.333 and pooled NDCG@5 is 0.774 across six fictional profiles. This is not independent human validation. Twenty synthetic sentiment checks scored 16/20, with all errors retained. Actual exported-model API and replacement-loader checks passed offline, and 27 existing regression tests passed. Server deployment, live approved vacancy wiring and Android integration remain open. A04/A05 below remain open because AI-generated examples do not replace human/consented participant evidence.

- [x] **A01 [P1] — AI:** Verified the supplied full Colab run and saved it as the repository notebook: all 41 code cells ran in order without saved errors, semantic vectors were computed, 7 skill checks and 6 API checks passed, and model saving/reloading completed.
- [ ] **A02 [P0] — AI and Backend:** Freeze one final artifact with model versions, dependency versions and score definitions. Configure its trusted path on the server and verify reload, real recommendations and sentiment without a mocked model.
- [ ] **A03 [P0] — AI and Backend:** Use the same cleaning, skill identifiers and negation rules during training and serving. The older backend inference still differs from the notebook. Check Python aliases, C++, C#, .NET and no-experience/not-required examples.
- [ ] **A04 [P1] — AI:** Review a small documented sample of CV-job relevance and extracted requirements with people. Record sample size and disagreements; distinguish required, preferred and incidental skills. Report missing labels or unmeasured accuracy honestly.
- [ ] **A05 [P1] — AI and Team:** Check representative Kenyan student CVs and app feedback with consent. Document short-profile and sentiment errors, classifier limits and domain differences. Keep auxiliary career guesses out of eligibility and main ranking decisions.

### 3 Complete the Android connection

- [ ] **D01 [P0] — Android and Integrator:** Connect the main Matches cards and details to the agreed backend/model response. Currently they use SkillCoverageScorer; AI results appear on a separate AI tools screen. Prove the main journey uses the intended model output.
- [ ] **D02 [P0] — Android and AI:** Agree how ordering and percentage rings work. Preserve the requested descending percentage behaviour where that is the chosen ranking; label text similarity and required-skill coverage separately and never display either as hiring probability.
- [ ] **D03 [P1] — Android:** Display real descriptions, requirements, responsibilities, eligibility, source and deadline. Use honest unknown states. Show current availability clearly, and ensure expired, withdrawn and ineligible records follow the agreed filtering policy.
- [ ] **D04 [P1] — Android and AI:** Connect gaps to the Growth path using stable skill IDs/aliases. Expand course mappings for real job skills or provide a useful fallback. Keep reflections, streak/XP and external certificates distinct; course buttons must open valid provider pages.
- [ ] **D05 [P1] — Android:** Use the prototype logo/colours in the floating coach and connect it to the actual role, score and gaps. Decide whether it remains rule-based guidance. Sentiment endpoints do not create a generative chatbot; make the UI and report agree.
- [ ] **D06 [P1] — Android:** Retest forms, scroll areas, keyboard, Back, rotation, CV preview/PDF and saved-state behaviour after integration. Check long text, loading/empty/error/retry states, duplicate taps and account/guest isolation. Use Africa/Nairobi consistently for streaks and closing days.

### 4 Verify Firebase and the running backend

- [ ] **B01 [P0] — Backend and Android:** Confirm the intended Firebase project, Android client configuration and enabled providers. For Google, verify Web OAuth client, build SHA fingerprints and support email. Register the QA package separately if using it; test chooser cancellation and successful sign-in.
- [ ] **B02 [P0] — Backend and Android:** Prove real sign-up, login, password reset, logout and token refresh. Test profile, saved jobs, targets, evidence and progress after restarting and switching accounts; confirm offline retry does not lose drafts or expose another account’s data.
- [ ] **B03 [P0] — Backend:** Deploy and test Firestore rules in the intended development environment. Prove ownership restrictions and operator permissions with positive and negative cases. Keep server credentials out of Git and Android; a configuration file alone is not proof of setup.
- [ ] **B04 [P0] — Backend and Integrator:** Run the authenticated API at a reachable address and configure AI_BASE_URL/VACANCY_BASE_URL. Use the emulator host address for emulator tests and a reachable HTTPS endpoint for a phone. Verify healthy auth and actual model readiness, not only HTTP 200.
- [ ] **B05 [P1] — Backend and Data owner:** Review candidate opportunities against current primary sources and Kenyan/student eligibility before publication. Separate mandatory and preferred skills. The 62-record research set and 10 bundled candidates are not already a verified live feed.

### 5 Verify the recruiter journey

- [ ] **R01 [P1] — Android and Backend:** On the integrated APK, sign in as a recruiter, register a company and save/recover a vacancy draft. Confirm pending company approval blocks submission and the workspace does not require a student skills profile.
- [ ] **R02 [P1] — Backend and Integrator:** Use a trusted operator to approve the company, review a real submission and publish it. Confirm that the same vacancy appears in the student feed. Existing authenticated operator API/Swagger is sufficient unless a separate admin UI is required.
- [ ] **R03 [P1] — Android and Backend:** Edit the vacancy, test re-review and stale revisions, then withdraw it. Confirm source duplicates are not shown twice and closed/withdrawn adverts disappear from the student feed and model candidates.
- [ ] **R04 [P1] — Backend:** Test a second recruiter account and suspended/rejected companies. A company must not edit another company’s adverts, approve itself or see private student CV data. Record evidence of both allowed and denied requests.

### 6 Run final project checks

- [ ] **Q01 [P0] — Android:** On the merged branch, run :app:testDebugUnitTest, :app:lintDebug and :app:assemblePreview (or the agreed submission variant). The recruiter branch documents partial compilation, not a verified final APK; retain the actual results.
- [ ] **Q02 [P1] — AI and Backend:** Run both the AI regression tests and backend tests on the final merged code, plus a real exported-model/API test. The 20 tests passed during this review use simulated dependencies and do not replace that integration check.
- [ ] **Q03 [P1] — Backend:** Run the real Auth/Firestore emulator smoke tests or equivalent controlled development-project tests, then test the configured project. Verify rules, ownership, persistence, publish/withdraw and token behaviour beyond memory-store tests.
- [ ] **Q04 [P1] — Android and Team:** Install the final APK on a physical Android phone. Check startup, typing and scrolling speed, large fonts, contrast, TalkBack labels, touch targets, network loss/recovery and permissions. Record the build and device; old emulator timings are not phone benchmarks.
- [ ] **Q05 [P0] — Whole team:** Rehearse one complete student journey and one recruiter-to-student publication journey using the final setup. Check that AI results, cloud persistence, course links and saved PDF work together, with understandable recovery when the service is unavailable.

### 7 Prepare the submission

- [ ] **S01 [P1] — Whole team:** Confirm the complete lecturer rubric, deadline and required formats. The supplied screenshot explicitly checks a repository base model, all data-mining stages and clear explanations. Do not assume that slides, a video, an admin app or a store release are mandatory without confirmation.
- [ ] **S02 [P0] — AI:** Submit one readable, fully executed notebook containing every required data-mining stage and final model saving/interface code. Include data locations, dependencies, outputs, sources and honest metric definitions. Remove stale failed-run output from the final submitted copy.
- [ ] **S03 [P1] — Whole team:** Finish the required project write-up: problem/users, requirements, architecture, Firebase data design, AI methods, HCI choices, course-component map, tests, results, limitations and references. The personal notebook walkthrough is a study aid, not automatically the final project report.
- [ ] **S04 [P0] — Android and Integrator:** Package the final installable APK with agreed version/build and server configuration. Test that exact file on the demonstration phone. Store signing is needed only if publishing to a store; do not put private signing keys or server secrets in the repository.
- [ ] **S05 [P0] — Integrator:** Publish the final integrated source revision and update README setup instructions. Link the notebook, model-artifact location, backend configuration and tests. Confirm lecturer/team access, and verify a clean setup from those instructions; large model files need a clear download path.
- [ ] **S06 [P1] — Whole team:** Prepare the required demonstration/presentation and individual explanations. Keep screenshots, test evidence and a truthful fallback plan. Each person should explain their contribution and the difference between classification accuracy, sentiment accuracy and the job-relevance proxy.

### 8 Only if included in the final scope

- [ ] **O01 [Scope] — Team:** If claiming a generative AI coach, implement and validate that separately. Otherwise demonstrate contextual rule-based guidance honestly; an LLM and paid API are not automatically required.
- [ ] **O02 [Scope] — Backend:** If claiming automatic vacancy collection, configure approved sources, adapters, review, expiry handling and a scheduled worker, then test them. Manual reviewed publication can serve the demo if that is the agreed scope.
- [ ] **O03 [Scope] — Team:** Applicant tracking, employer access to CVs, company profile editing, dedicated admin screens, notifications and Google Play release are additional scope unless the lecturer or group explicitly requires them.

## Mobile development components to demonstrate

The implementations below are present in the reviewed code. Demonstrate them on the final merged build; do not mark the whole mobile submission complete from source inspection alone.

| Course area | Code evidence |
| --- | --- |
| Kotlin and Android structure | Kotlin source, manifest, Gradle project and SDK settings |
| Activities and lifecycle | MainActivity plus UpShiftViewModel on the recruiter/backend branch |
| Fragments and Views | AppFragment, FragmentContainerView and fragment_host.xml Compose host |
| Jetpack Compose and layouts | Composable student/recruiter screens and responsive scroll containers |
| Splash screen | Native SplashScreen API and branded drawable/theme |
| Menus and navigation | Dropdown menus, bottom navigation, workspace switching and Back handling |
| RecyclerView | Saved roles screen with RecyclerView adapter |
| Forms and persistence | Validated fields, local drafts, CV PDF and Firebase sync implementation |

## Final submission check

- [ ] All P0 tasks are complete with evidence, and every P1 task is completed or explicitly recorded as a limitation accepted for the submission.
- [ ] One integrated revision produces the submitted APK and loads the submitted model artifact.
- [ ] Student and recruiter demonstration journeys work with the intended account, jobs and server.
- [ ] Notebook, source, setup instructions, required report and build files are accessible to the lecturer.
- [ ] The group can explain what is implemented, what was tested and what remains a limitation.

Update each task with completion date, evidence path/test result and final commit. Checklist count is not a project-completion percentage.

## Main evidence sources

- `origin/android-recruiter:backend/models.py`, `backend/upshift_inference.py`, `app/src/main/java/ke/upshift/app/AiScreen.kt` and `Data.kt` establish the model-format and main-feed integration gaps.
- `origin/android-recruiter:docs/BACKEND_API.md`, `GOOGLE_SIGN_IN.md`, `VACANCY_BACKEND.md` and `RECRUITER_ANDROID.md` document configuration and verification boundaries.
- `archive/ai-development/notebooks/UpShift_Clear_Steps.ipynb`, the actual local exported model, `docs/VERIFICATION.md` and the isolated backend test run support the completed-work entries.
- `origin/android-recruiter:data/listings/README.md` documents research-catalogue status; no new availability verification was performed in this review.
