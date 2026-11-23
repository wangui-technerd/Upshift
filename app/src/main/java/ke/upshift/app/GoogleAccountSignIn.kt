package ke.upshift.app

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.GetCredentialCancellationException
import androidx.credentials.exceptions.GetCredentialException
import androidx.credentials.exceptions.NoCredentialException
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.google.android.libraries.identity.googleid.GoogleIdTokenParsingException
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.GoogleAuthProvider
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.tasks.await

private fun Context.activity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.takeIf { it !== this }?.activity()
    else -> null
}

/** Explicit button flow: offers account selection for new and returning Google users. */
internal suspend fun googleAccountSignIn(context: Context, auth: FirebaseAuth): AccountResult {
    val activity = context.activity()
        ?: return AccountResult.Error("Open the sign-in screen again to choose a Google account.")
    // This resource is generated only when google-services.json contains a WEB OAuth client.
    // Resolve it dynamically so email login still builds before Google is configured.
    val resource = context.resources.getIdentifier("default_web_client_id", "string", context.packageName)
    val clientId = if (resource != 0) context.getString(resource) else ""
    if (clientId.isBlank()) return AccountResult.Error("Google sign-in is not configured yet. Enable Google in Firebase and replace app/google-services.json with the updated file.")
    return try {
        val option = GetSignInWithGoogleOption.Builder(clientId).build()
        val request = GetCredentialRequest.Builder().addCredentialOption(option).build()
        val credential = CredentialManager.create(activity).getCredential(activity, request).credential
        if (credential !is CustomCredential || credential.type != GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL) {
            AccountResult.Error("Google returned an unsupported credential. Please try again.")
        } else {
            val token = GoogleIdTokenCredential.createFrom(credential.data).idToken
            auth.signInWithCredential(GoogleAuthProvider.getCredential(token, null)).await()
            AccountResult.Success
        }
    } catch (_: GetCredentialCancellationException) {
        AccountResult.Cancelled
    } catch (_: NoCredentialException) {
        AccountResult.Error("No Google account is available. Add one to this device and check that Google Play services are enabled.")
    } catch (_: GoogleIdTokenParsingException) {
        AccountResult.Error("Could not read the Google sign-in response. Update Google Play services and try again.")
    } catch (_: GetCredentialException) {
        AccountResult.Error("Google sign-in could not start. Check your connection and the Firebase Google provider configuration.")
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        AccountResult.Error(accountError(e))
    }
}
