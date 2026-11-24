# Repeatable emulator checks

## Learning completion check

The isolated QA test covers both confirmation choices: adding SQL changes a two-skill job from 50% to 100% and persists the profile; saving progress only leaves the skills and percentage unchanged. Repeated completion does not duplicate skills. This test uses local guest data in `ke.upshift.app.qa`, not the demo account.

```powershell
.\gradlew.bat :app:testQaUnitTest :app:connectedQaAndroidTest -PinstrumentedBuildType=qa -PskipGoogleServices=true "-Pandroid.testInstrumentationRunnerArguments.class=ke.upshift.app.LearningCompletionTest"
```

Normal app builds still use the usual Firebase configuration and debug test target. These flags apply only to the isolated test build.

The full journey checks below run on Pixel 8a / Android 14 against `demo-upshift`. They use fictional accounts, employers and vacancies. They do not validate production Firebase, Google sign-in, course enrolment, or a physical phone.

## Start the local services

Use the repository root in PowerShell. The existing `.venv-ai` environment needs both the model requirements and `backend/requirements-dev.txt`. Keep the trusted schema-2 bundle, encoder and deployment configuration together.

Terminal 1:

```powershell
$env:JAVA_HOME = 'C:/Program Files/Android/Android Studio1/jbr'
$env:PATH = "$env:JAVA_HOME/bin;$env:PATH"
firebase.cmd emulators:start --only auth,firestore --project demo-upshift
```

Terminal 2:

```powershell
$env:UPSHIFT_FIREBASE_PROJECT_ID = 'demo-upshift'
$env:FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9099'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080'
$env:UPSHIFT_MODEL_PATH = (Resolve-Path 'output/member2_handoff/artifacts/upshift_bundle.joblib').Path
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
.\.venv-ai\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8122 --no-proxy-headers
```

Terminal 3:

```powershell
.\.venv-ai\Scripts\python.exe scripts/seed_member3_demo.py
$env:UPSHIFT_FIREBASE_PROJECT_ID = 'demo-upshift'
$env:FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9099'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8080'
.\.venv-ai\Scripts\python.exe -m uvicorn scripts.emulator_test_gateway:app --host 127.0.0.1 --port 8124
```

The test gateway forwards requests to the real local backend. It injects temporary slow/error/empty responses and supplies an emulator-only operator for the company/vacancy review steps. It refuses to start without the exact local demo project and emulator settings. Never deploy it. The main backend's authentication and approval checks are still exercised.

## Run the Android journeys

Start Pixel 8a from Android Studio Device Manager, then:

```powershell
$env:JAVA_HOME = 'C:/Program Files/Android/Android Studio1/jbr'
.\gradlew.bat :app:connectedDebugAndroidTest :app:testDebugUnitTest :app:lintDebug -PfirebaseEmulators=true -PaiBaseUrl=http://10.0.2.2:8124 --console=plain
```

`EmulatorJourneyTest` covers:

1. Real sign-up, invalid input, onboarding, profile persistence, wrong/correct passwords, sign-out and reset-email confirmation.
2. Real model recommendations, experience validation, requirements/gaps, the exact application intent, feedback and rotation state.
3. Empty results, service failure/retry, slow responses, timeout, rejected tokens and actual emulator network loss. Network settings are restored in `finally`.
4. Saving a role, a course intent, short/valid learning evidence, XP/streak, coach opening, long CV editing, PDF generation and reopening with Android's PDF renderer. The generated multi-page PDF is checked; the first export uses an intercepted picker result pointing to an app-cache test file.
5. Company registration, approval gating, draft recovery, actual operator approval/publication and recruiter withdrawal.
6. Larger text, landscape/portrait rotation and saving through the actual Android document picker. Font scale and rotation are restored. Generated PDFs have `Upshift-fictional-ui-` names.

Android Test Orchestrator isolates the journeys into separate test processes. It does not clear application data. New test accounts and company records stay in the local emulators until those emulators are stopped; no real accounts or project data are touched. Course/application intents are verified without submitting applications or enrolling in courses.

The HTML test and lint reports are below the configured Gradle build directory (`%TEMP%/upshift-build/<workspace-hash>/app/reports`). Do not interpret emulator timings as physical-phone benchmarks.

### Observed emulator recovery

During network-loss testing, Firestore Emulator 1.21.0 retained a cancelled listener and returned `499 call already cancelled` while notifying a publication. The local API consequently returned 500 even though the write could already be present. The recovered run executes the publication/withdrawal journey before disconnect tests. This is a recorded local-emulator limitation, not evidence of a production Firestore failure.

If this occurs, preserve emulator data with `firebase.cmd emulators:export output/qa/NEW_RECOVERY_FOLDER --project demo-upshift`, stop the emulators, then restart the first command with `--import=output/qa/NEW_RECOVERY_FOLDER`. Choose a new export folder. Read back the submission status/revision before retrying a publication whose result was ambiguous. Generated fixture records can remain archived; do not delete unrelated test data.

## Restore the ordinary interactive test app

After the suite, install the build that talks directly to the backend rather than the fault-injection gateway:

```powershell
.\gradlew.bat :app:installDebug -PfirebaseEmulators=true --console=plain
```

The default emulator configuration sends **both** student and recruiter requests to `http://10.0.2.2:8122`. Keep Firebase and the backend running. Use a fictional student with Python/SQL, Nairobi and six months' experience to find `Python Software Intern (Demo)`. Google sign-in requires separate live-project testing.
