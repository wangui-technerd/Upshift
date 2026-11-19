# Upshift

## AI notebook

The main AI notebook is [UpShift_Clear_Steps.ipynb](ai/notebooks/UpShift_Clear_Steps.ipynb). It contains the problem, loading and cleaning, EDA, model training, evaluation, an end-to-end example, model saving and an AI-service interface in one file. It includes executed outputs and short explanations. Open it in Colab and run from top to bottom using the three original CSVs. See [the AI guide](ai/README.md) for the engineering handoff.

## Android frontend

Open this folder in Android Studio, sync Gradle and run `app` (Android 8/API 26+, compile SDK 37). Android Studio's bundled JBR is supported. Build output is under the system temporary directory in `upshift-build/<workspace-hash>/app` to avoid recurring Windows locks in the synced workspace. The recommended optimized APK is `output/apk/Upshift-preview.apk`. Select the preview build variant for performance checks.

## Complete frontend journey

- Branded splash → welcome → three short introduction screens.
- Sign-up, login and password-reset forms with validation. Account services are an injectable boundary and are not connected; forms never invent a successful account or retain passwords. Continue on this device provides a working local journey.
- Profile onboarding: student information → skills → placement goal.
- Matches: percentage rings, descending percentage ranking, search, saved filter and actual learning streak.
- Role details: responsibilities, requirements, eligibility, current skills, missing skills, save, target growth path and CV preparation.
- Growth: grouped Google/Meta certificate programmes on Coursera, external provider links, target-role focus and separate learning evidence, XP and level progress.
- You: profile identity, average skills match, skills, completed steps, streak, level, CV, saved roles and editing.
- Floating coach: a contextual bottom sheet with quick prompts and conversation. The local implementation gives deterministic guidance from the current role/profile; it is not a connected AI service.
- CV: editable form → one-column preview → native PDF save picker; printing is also available. Empty optional sections are omitted and long text wraps onto new pages.

## Data and integration

All employer listings are fictional fixtures, retained in the development repository. Product screens do not contain developer-status banners. Replace `OpportunitiesRepository`, `MatchScorer`, `CoachRepository` and `AccountGateway` with agreed backend/model adapters. See `docs/INTEGRATION.md`.

The temporary match formula is the percentage of listed required skills present in the user's entered profile (case-insensitive exact matching), not a hiring probability. An empty profile has no invented percentage. Skills are not added automatically when an activity is completed. Learning activity earns 25 XP per completed skill; levels advance each 150 XP. Streaks use consecutive activity days in Africa/Nairobi and remain active through the day after the last activity.

Profile drafts, saved roles, target role, evidence and progress persist locally. Passwords do not persist. Existing profiles are retained by app updates. Cloud auth/sync, real applications and trained model outputs require the other teammates' integrations.

## Course components

Kotlin; Activity lifecycle; Fragment with an XML Compose host; Compose layouts and state; startup SplashScreen; menu; screen navigation and Android Back; RecyclerView for saved opportunities; forms and local persistence. Main content screens use bounded scrolling lists or scrollable forms, with bottom padding for the coach button and keyboard-aware layouts.

## Design

Fraunces headings, Karla body text, blue/deep blue, cream, orange/peach, mint/teal and lavender/plum. Font files are bundled offline with OFL licences. Colour supports textual labels rather than replacing them. Primary controls retain large touch targets.

## Verification

`gradlew :app:assemblePreview :app:testDebugUnitTest :app:lintDebug`

Unit coverage protects percentage-vs-count ranking, empty profiles, duplicate skill handling and streak boundaries. The `qa` build uses the separate `ke.upshift.app.qa` application ID for isolated emulator tests without overwriting a user's profile. Build it with `:app:assembleQa`.

Manual/device checks: fresh welcome; all auth/onboarding screens; scrolling to the bottom of requirements, eligibility, growth and You; score ranking; saving and selecting a target; evidence validation/completion/undo; streak/XP persistence; floating coach and keyboard; CV validation/preview/export; Back and rotation; large text and TalkBack. Production accessibility and performance still require physical-device review.
## Course links, scrolling and PDF export update

Growth now groups related missing skills under Google/Meta certificate programmes on Coursera. Official programme pages were checked on 10 November 2026. View programme opens the provider in the browser; it does not enrol, pay or award a certificate. Recording a learning reflection is separate.

Screen scroll state is retained across tabs and role navigation with a SaveableStateHolder. Long lists show a scroll-position indicator, drawn without rebuilding the list on every scroll offset. The floating coach uses the shared gradient BrandMark. Intro pages label their illustrative score as an example and keep navigation at the bottom.

CV export now has a direct Save CV as PDF action using Android's CreateDocument picker. Rendering/writing happens on an IO dispatcher; printing remains a secondary action. The saved app-generated QA PDF was pulled from the emulator, checked for its entered contact/education/skills text and rendered for visual inspection.

For speed checks, select the **preview** build variant in Android Studio or install `output/apk/Upshift-preview.apk`. It uses R8 optimization and resource shrinking, with a development signing key. It is not the production/store signing setup. The debug variant remains available for debugging; its timing is not a release-performance benchmark. QA is an isolated optimized package with a separate app ID. Fonts load asynchronously and normalized profile skills are cached per immutable profile. The extra timed Compose splash was removed; Android's native branded splash remains.
