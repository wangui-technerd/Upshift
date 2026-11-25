# UpShift

We built UpShift to help university students find internships and entry-level jobs, understand skill requirements and choose what to learn next.

## Our app

- We support sign-up, login, student profiles and a CV builder with PDF export.
- We show job requirements, eligibility, saved roles and profile-based recommendations.
- We link missing skills to learning resources. Students can record learning and choose to add a skill to their profile, which updates their skills-match percentage.
- We include a guided career chatbot and feedback submission.

We built the Android app with Kotlin and Jetpack Compose. We use Firebase for accounts and saved data, and a Python backend for recommendations. Our chatbot uses prepared rules, not a conversational AI model. Match percentages do not predict hiring success.

## Run the app

1. Open this folder in Android Studio and sync Gradle.
2. Follow our [Firebase sign-in setup](docs/GOOGLE_SIGN_IN.md).
3. Follow our [backend setup](backend/README.md), or our [local emulator guide](docs/EMULATOR_TESTING.md).
4. Run the `app` configuration on an emulator or Android device running Android 8 or later.

We provide guest browsing. Sign-in, cloud saves and personalised recommendations need their configured services. Installing the APK does not start the backend.

## Our code

- [`app/`](app/) — Android screens, navigation and student features.
- [`backend/`](backend/) — authentication checks, vacancies, feedback and model access.
- [`upshift_ai/`](upshift_ai/) — model functions used by the backend.
- [`ai/`](ai/) — final notebook, original base notebook and model requirements.
- [`data/listings/`](data/listings/) — bundled research listings and their source notes.
- [`docs/`](docs/) — setup and testing guides.
- [`archive/ai-development/`](archive/ai-development/) — earlier AI experiments and handover records.

## Our AI work

We kept our original CV-classification work and compared word matching with semantic job matching. We use a pretrained text model for semantic matching. Our [final notebook](ai/notebooks/SemanticMatching_Final.ipynb) includes the full workflow, saved charts and app-model code.

[AI repository](https://github.com/CoIlins/SemProject_MLEngine) · [Model downloads](https://drive.google.com/drive/folders/1tfmOnYKapGidW1i8TDKwe2CIQjgVpxpX)

## Our checks

We verified the learning update with 27 unit tests and two emulator tests, and compared the rebuilt model with the backend across 20 checks. We describe the limits in the notebook; independent human relevance review remains pending. Our [test guide](docs/EMULATOR_TESTING.md) explains how to repeat the emulator checks.
