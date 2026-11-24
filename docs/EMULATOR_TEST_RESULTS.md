# Emulator verification and responsiveness fixes

Final packaging check: 24 November 2026. The complete UI run passed on 23 November using Pixel 8a, Android 14/API 34, local Firebase `demo-upshift`, and the actual saved model. All accounts and vacancies were fictional.

| Check | Result |
|---|---|
| Recruiter registration, draft recovery, approval, publication and withdrawal | Passed; the Android recommendation client included the published vacancy and excluded it after withdrawal. |
| Student sign-up, validation, onboarding, persistence, login/logout and reset confirmation | Passed. |
| Recommendations, skill evidence, exact application intent, feedback and rotation | Passed. |
| Empty results, slow response, service failure, timeout, rejected tokens and network loss | Passed; retry and entered data were checked. |
| Saved role, course intent, learning evidence, XP/streak, coach opening and long CV | Passed; the generated multi-page PDF reopened with Android's PDF renderer. |
| Larger text, portrait/landscape rotation and actual Android document picker | Passed. |
| Android unit tests | 22 passed, zero failures/errors. |
| Backend regression tests | 27 passed. |
| Android lint | Passed with warnings; no blocking errors. |

The UI report contains six tests, zero failures, zero errors and zero skipped tests. Reproduction steps and the observed Firestore emulator recovery are in [EMULATOR_TESTING.md](EMULATOR_TESTING.md). The local XML evidence is saved at `output/qa/emulator-journeys-passed.xml`.

## Changes

- Fixed the missing default recruiter API address in emulator builds.
- Moved bundled-catalogue loading/parsing off the main UI thread.
- Debounced profile serialization/local saves while typing; lifecycle changes and Done still flush pending edits.
- Bounded multiline fields to six visible lines, with internal scrolling for long CV/vacancy text.
- Retained recommendation results through rotation in the account-owned ViewModel state; changing profiles/accounts invalidates them. Feedback sentiment also survives rotation.
- Added a repeatable, isolated Android UI suite and a strictly local fault-injection/operator gateway. The gateway is not part of the production backend.
- Added skill tags to the fictional demo vacancy so its saved-role and growth flows can be exercised.

## Performance evidence and limits

### 24 November navigation and guidance follow-up

Further feedback/explanation checks on 24 November: recommendation cards now use a collapsed **Why this job?** explanation with everyday wording and expandable requirements. Feedback uses authenticated `POST /feedback` with a retry-safe submission ID and persists messages in Firestore, rather than just classifying their tone. An emulator-submitted fictional message was read back from the local database exactly once. The real recommendations/explanation/application-link/feedback journey and the service-error/timeout/sign-in-error/offline/retry journey both passed as focused emulator runs. All 28 backend tests and 25 Android JVM tests passed. Service failures use native dialogs; feedback success uses a snackbar and receipt text. Authentication and company errors also use dialogs. A device connectivity check was added after the first offline test revealed that the emulator could still reach localhost without Wi-Fi. No cloud deployment was performed; deploy the updated backend together with the app for non-local use.

- Removed the Print CV action and its print adapter; PDF saving remains available.
- Replaced the unexplained home recommendation button with Browse / For you choices and a short explanation.
- Added visible return actions to Growth, You, introductory and company screens; company navigation no longer falls through to the student back handler. Password reset returns to login.
- Expanded the local guided coach to distinguish greetings, eligibility, CVs, courses/cost, applications, learning, skills coverage and unknown questions. This is not a conversational-model integration.
- All 25 JVM tests passed, including three coach-response checks. A focused Android emulator test passed for home choices, Growth/You back navigation and opening/leaving the CV builder. Existing full journey selectors were updated for the For you label; the full six-journey suite was not rerun in this follow-up.
- The first focused attempts encountered a sleeping emulator and test wait/label issues; the final corrected test passed. The debug app was built and installed on Pixel_8a. Lint passed before the final small reset/back-handler adjustments.

Three cold activity starts on the final direct-backend debug build took **4,849 ms, 5,444 ms and 4,749 ms** (median **4,849 ms**). A pre-change observation was 5,989 ms. These are activity-first-frame measurements from ADB on this PC, not fully-loaded-screen or physical-phone benchmarks; host load and debug compilation affect them. Do not present the difference as a controlled speed benchmark. Startup still takes roughly five seconds on this emulator.

Long text entry, scrolling through the tested forms, PDF writing and navigation were exercised without a blocking UI failure in the successful run. This does not establish a universal frame-rate or latency guarantee.

Google sign-in against the live Firebase project, live deployment, physical-phone performance, accessibility with TalkBack and independent model relevance validation remain separate checks. Application/course intents were checked without submitting applications or enrolling in courses. One cancelled-listener failure in the local Firestore emulator required an export/restart/import recovery; the data and recovery instructions were preserved.
