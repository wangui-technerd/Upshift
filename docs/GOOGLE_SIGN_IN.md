# Email/password and Google sign-in

The login and sign-up screens now offer both the email form and **Continue with
Google**. The Google button uses Android Credential Manager's explicit Google
account chooser and exchanges the Google ID token for a Firebase session. Both
methods use the existing UID-scoped Firestore profile/onboarding flow. Cancelling
the chooser returns to the form without creating a fake session or an error.
Logout clears Firebase and the credential-provider sign-in state. Google tokens
and passwords are not written to the app's profile/preferences or logs.

The Google button does not require the email/password form to be filled in.
First-time Google users are created by Firebase and continue through onboarding;
returning users load their existing Firestore data. A Google user name is taken
from the authenticated Firebase user, not the unsubmitted email-signup name.

## Required Firebase setup

1. Open Firebase Console > Authentication > Sign-in method. Keep Email/Password
   enabled and enable Google as well. Select the project support email and save.
2. Open Project settings > General > Your apps > Android (`ke.upshift.app`).
   Add the SHA-1 certificate fingerprint of the signing key used for your build.
   You can also add its SHA-256 fingerprint.
3. Download the updated `google-services.json` and replace the file in `app/`.
   It must contain a Web OAuth client (`client_type: 3`). The Gradle Google
   Services plugin turns this into `default_web_client_id`. Do not use an Android
   OAuth client ID in its place. Do not edit generated resources by hand.
4. Sync Gradle and run the debug app on a Google Play-enabled emulator or a phone
   with an available Google account and Google Play services.

The existing config was checked before this change and did not contain a Web
OAuth client. Google sign-in cannot be verified against the live project until
you finish the steps above. The app gives a configuration message while that
resource is absent, and email/password remains available.

Debug signing certificate found on this machine:

```text
SHA-1:   26:14:29:E3:5F:53:79:99:EA:A2:CE:BA:45:4C:70:8C:C7:A6:1B:28
SHA-256: FD:6E:A2:9E:84:4D:E2:71:80:90:7C:21:3C:D4:FB:EB:5A:7C:0D:BB:88:C0:50:2E:7C:47:7A:27:66:52:0D:6D
```

Confirm the selected build's certificate with `gradlew.bat :app:signingReport`.
Release/store signing needs its own certificate registered. The `qa` build has
application ID `ke.upshift.app.qa` and needs a separate Firebase Android app.
The local Firebase demo-emulator build supports email/password; Google chooser
testing uses the real configured Firebase project.

## Test on device

- Create a new email/password account; confirm its Firebase UID and Firestore doc.
- Sign out, sign back in with that email/password, and confirm progress returns.
- Sign out and choose Continue with Google with the email form left blank.
- Cancel the chooser: stay on the account screen, with controls re-enabled.
- Complete Google sign-in: check the Google provider in Firebase Authentication,
  complete onboarding, then sign out and back in to confirm the same UID/profile.
- Try a second Google account: previous user's profile and progress must not appear.
- Test offline/error handling and retry after reconnecting.

Provider linking for an existing email/password account is governed by Firebase's
account/provider rules. If Firebase reports a credential conflict, the UI asks
the user to use their existing sign-in method; it never merges profiles solely
because two email strings match. A manual link/unlink-account screen is not part
of this change.

Official integration references:
- https://firebase.google.com/docs/auth/android/google-signin
- https://developer.android.com/identity/sign-in/credential-manager-siwg
