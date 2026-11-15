# Recruiters inside the Kotlin app

Open **I'm hiring · Company workspace** on the welcome page, or **Company workspace** in the signed-in student's menu. This switches interface only; it never grants company approval or operator privileges. The last workspace choice stays on the device. The company workspace has its own sign-in/signup copy using the existing Firebase gateway; it does not require a student skills profile.

The native screens use the app's existing UpshiftTheme, Fraunces/Karla typography, Paper background, BrandSoft/Mint/Coral surfaces, rounded cards and bottom navigation. The web portal redesign on `recruiter-page` uses the same visual language.

## Connection

Set the existing vacancy API address in your untracked local Gradle configuration, or pass it as a Gradle property:

```powershell
.\gradlew.bat :app:assembleDebug -PvacancyBaseUrl=http://10.0.2.2:8000
```

The debug emulator uses `10.0.2.2` to reach the host. Release builds require HTTPS. If vacancyBaseUrl is absent, the app falls back to aiBaseUrl because both routes share the same FastAPI server. Firebase Authentication must be configured for the same project as that server. No server credentials belong in the Android app.

## Test journey

1. Choose the company workspace and create/sign into a Firebase account, using email or Google.
2. Register the company with its name, official HTTPS site, description and offering interests.
3. A trusted operator verifies and approves the company through the existing backend. Refresh the company status in Android.
4. Create a vacancy, add eligibility and an official source link, then submit it for review. Before company approval, a local draft can be prepared and saved but submission is disabled.
5. An operator publishes the submission. Refresh and confirm its status in Android, then check the student workspace.
6. Edit or withdraw the vacancy. Changes need review again; withdrawal closes the public advert. Requests remain protected by Firebase bearer tokens and server ownership checks.

The native client uses `/listings/companies/mine`, `/submissions/mine`, `/companies`, `/companies/{id}/vacancies` and `/submissions/{id}/withdraw`. Pagination is followed; review notes and company status are retained. Workspace selection only shows returned owned companies.

Drafts are private to the signed-in account on this device, with one slot per company/new vacancy or existing vacancy. Saving a draft does not publish it. Submission persists a recovery draft before networking and clears that draft only after success. Do not put candidate CVs or other sensitive personal information in adverts.

Training/mentorship are interest fields only. Applicant tracking, recruiter access to student CVs, company profile editing and administrator screens are not included.

## Verification limits

Run `:app:testDebugUnitTest :app:assembleDebug` in Android Studio/the project terminal. Native URL, status and draft-validation tests are included. Kotlin compilation completed in an isolated local build. The connection ended before final unit-test results were available; APK assembly and the real Firebase/API journey still require verification. Existing backend unit tests and web-only tests do not establish that the Android integration works.
