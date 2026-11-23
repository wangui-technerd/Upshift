# Member 3 student journey

The Android app sends the signed-in Firebase user's ID token to
`POST /recommendations` and `POST /sentiment`. Use **Matches → Get job
recommendations** and **menu → Feedback**. The recommendation request sends
education, skills, summary, projects, work experience and goal. Location and
months of experience are optional. Enter zero only for a student with no
experience. Keep the phone and email fields out of recommendation text.

## Use the team backend

The Android branch starts from `android-recruiter` so it retains the company
workspace. Run the current Member 2 backend separately from
[the backend branch](https://github.com/wangui-technerd/Upshift/tree/member2/backend-deployment)
or [commit bc83cf3](https://github.com/wangui-technerd/Upshift/commit/bc83cf320e3e95276ebc00f8ebd4a02ca35e8911).
The older Android checkout's Python backend predates the live recommendation
contract. For a local demo, start the trusted model, Auth and Firestore emulators
with the Member 2 local launcher and confirm
[API health](http://127.0.0.1:8122/health) reports model readiness.
Use a fictional student and a known approved, active vacancy.
The backend smoke-test script withdraws its own fixture before exiting.
To keep a fictional vacancy available for phone testing, run the following
using the Python environment of the running backend. Execute the script from
this Android checkout:

```powershell
& 'C:\path\to\backend\.venv\Scripts\python.exe' scripts\seed_member3_demo.py
```

For this fixture, use a fictional student with Python and SQL skills,
Nairobi, and six months of experience. Expect **Python Software Intern (Demo)**
and inspect the Docker gap. The demo Apply button should open the
`example.org` test destination. Run the seeder with `--close` to archive the
fixture, then request recommendations again. This verifies the phone's next
request, while the Member 2 smoke test covers withdrawal via the recruiter API.

### Android Studio emulator

Use Android Studio 9.3 with the repository's Gradle wrapper. Install Android
SDK 37 if Studio asks for it. From PowerShell in this checkout, build and install
the debug app onto the running emulator:

```powershell
.\gradlew.bat :app:installDebug -PfirebaseEmulators=true
```

The debug build uses `demo-upshift` with Auth on 9099, Firestore on 8080 and
the backend at `http://10.0.2.2:8122`. Sign up with a fictional test account
using email/password. If launching with the Run button in Android Studio,
set `firebaseEmulators=true` in your user Gradle properties before syncing.

### Physical Android phone over USB

With USB debugging enabled and only the intended phone selected, run these
commands on the laptop while the backend and both Firebase emulators are
running. If adb is missing from PATH, use `adb.exe` under the Android SDK's
`platform-tools` directory.

```powershell
adb devices
adb reverse tcp:8122 tcp:8122
adb reverse tcp:9099 tcp:9099
adb reverse tcp:8080 tcp:8080
.\gradlew.bat :app:installDebug -PfirebaseEmulators=true -PfirebaseEmulatorHost=127.0.0.1
```

Open the installed app with the phone still attached. The debug build routes
these calls through USB to the laptop. With multiple devices connected, use
`adb -s DEVICE_SERIAL reverse …` and select the intended device for installation.

### Shared HTTPS backend

Once Member 2 supplies a verified URL, place the team's `google-services.json`
locally under `app/` for Firebase project `upshift-a3dbd`. Build against that
project and the matching service:

```powershell
.\gradlew.bat :app:installDebug -PfirebaseEmulators=false -PaiBaseUrl=https://YOUR-BACKEND
```

The same HTTPS URL can be set via `aiBaseUrl` in user Gradle properties.
Use only a team-controlled backend. The local demo URL cannot be shared as a
staging endpoint.

## Verification to record

| Check | Expected on the phone |
|---|---|
| Sign in and complete a fictional student profile | Profile saves and the recommendations screen opens from Matches. |
| Request recommendations for the approved fixture | The title, employer, location, deadline, and skill evidence appear. Record the elapsed time from Find jobs to the first result. |
| Inspect a missing skill and tap Open application | Skill gaps are labelled as skills the profile does not mention. A verified application link opens in the browser. |
| Withdraw the fixture via the recruiter | The next request omits it. A query with no matching vacancy shows an empty state. |
| Use a blank profile | Complete my profile opens the editor. |
| Simulate slow response, offline connection, expired sign-in and backend outage | A loading message, retry action or reauthentication prompt appears. Use a test backend or the handoff's API fixtures for controlled status responses. |
| Send realistic feedback | The returned sentiment is visible under Feedback. It does not change job results. |

Record the date, phone model, Android version, app commit, backend revision,
test account type, result, latency, and any failure. Keep fixture credentials
and real CV content out of shared test notes. Physical-phone results and pilot
observations are pending until the team runs them.

## Small student pilot

When the phone flow passes, ask a few volunteers using fictional profiles to
try the same journey. Ask which vacancies were relevant, whether the skill
explanations were clear, and whether they knew what to do next. Record the
scenario, observed behaviour, expected behaviour, severity, owner and retest
result for each issue. Route ranking or model feedback to Member 1, vacancy or
API failures to Member 2, and Android screen or navigation issues to Member 3.
