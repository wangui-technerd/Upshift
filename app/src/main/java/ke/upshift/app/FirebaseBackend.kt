package ke.upshift.app

import android.content.Context
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseNetworkException
import com.google.firebase.FirebaseOptions
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthException
import com.google.firebase.auth.UserProfileChangeRequest
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.FirebaseFirestoreException
import com.google.firebase.firestore.ListenerRegistration
import com.google.firebase.firestore.SetOptions
import com.google.firebase.firestore.Source
import com.google.firebase.firestore.FieldValue
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withTimeout

sealed interface AccountResult {
    data object Success : AccountResult
    data object ResetSent : AccountResult
    data object Cancelled : AccountResult
    data class Error(val message: String) : AccountResult
}
interface AccountGateway {
    suspend fun signIn(email: String, password: String): AccountResult
    suspend fun signUp(name: String, email: String, password: String): AccountResult
    suspend fun resetPassword(email: String): AccountResult
    suspend fun signInWithGoogle(context: Context): AccountResult
}

fun accountError(error: Exception): String = when (error) {
    is FirebaseNetworkException -> "Could not connect. Check your internet connection and try again."
    is FirebaseAuthException -> when (error.errorCode) {
        "ERROR_EMAIL_ALREADY_IN_USE" -> "An account already uses this email. Log in or reset your password."
        "ERROR_WEAK_PASSWORD" -> "Choose a stronger password that meets the project's password policy."
        "ERROR_OPERATION_NOT_ALLOWED" -> "This sign-in method is not enabled for this Firebase project."
        "ERROR_TOO_MANY_REQUESTS" -> "Too many attempts. Wait a moment before trying again."
        "ERROR_ACCOUNT_EXISTS_WITH_DIFFERENT_CREDENTIAL", "ERROR_CREDENTIAL_ALREADY_IN_USE" -> "This email already has an account using another sign-in method. Use that method to sign in."
        else -> "Could not authenticate. Check your email and password, then try again."
    }
    is FirebaseFirestoreException -> "Could not access your cloud data. Check your connection and try again."
    else -> "The request could not finish. Please try again."
}

class FirebaseBackend(context: Context) : AccountGateway {
    private val applicationContext = context.applicationContext
    companion object { private val emulatorApps = mutableSetOf<String>() }
    private val app: FirebaseApp? = if (BuildConfig.DEBUG && BuildConfig.FIREBASE_EMULATORS) {
        FirebaseApp.getApps(context).find { it.name == "upshift-emulator" }
            ?: FirebaseApp.initializeApp(context, FirebaseOptions.Builder()
                .setApplicationId("1:123456789:android:upshift-emulator")
                .setApiKey("fake-api-key-for-emulator-only")
                .setProjectId("demo-upshift").build(), "upshift-emulator")
    } else FirebaseApp.getApps(context).find { it.name == FirebaseApp.DEFAULT_APP_NAME }
        ?: FirebaseApp.initializeApp(context)
    val auth: FirebaseAuth? = app?.let { FirebaseAuth.getInstance(it) }
    val db: FirebaseFirestore? = app?.let { FirebaseFirestore.getInstance(it) }
    init {
        if (BuildConfig.DEBUG && BuildConfig.FIREBASE_EMULATORS && app != null && emulatorApps.add(app.name)) {
            auth?.useEmulator("10.0.2.2", 9099)
            db?.useEmulator("10.0.2.2", 8080)
        }
    }
    val configured get() = auth != null
    val uid get() = auth?.currentUser?.uid
    private suspend fun attempt(block: suspend (FirebaseAuth) -> Unit): AccountResult {
        val current = auth ?: return AccountResult.Error("Firebase is not configured yet. Add your project's google-services.json to the app folder.")
        return try { block(current); AccountResult.Success }
        catch (e: CancellationException) { throw e }
        catch (e: Exception) { AccountResult.Error(accountError(e)) }
    }
    override suspend fun signIn(email: String, password: String) = attempt {
        it.signInWithEmailAndPassword(email.trim(), password).await()
    }
    override suspend fun signUp(name: String, email: String, password: String) = attempt {
        val user = it.createUserWithEmailAndPassword(email.trim(), password).await().user
        // Account creation already succeeded. A failed optional name update must not
        // invite creating the same account again; onboarding also stores the name.
        try { user?.updateProfile(UserProfileChangeRequest.Builder().setDisplayName(name.trim()).build())?.await() }
        catch (e: CancellationException) { throw e }
        catch (_: Exception) { }
    }
    override suspend fun resetPassword(email: String): AccountResult {
        val result = attempt { it.sendPasswordResetEmail(email.trim()).await() }
        return if (result == AccountResult.Success) AccountResult.ResetSent else result
    }
    override suspend fun signInWithGoogle(context: Context): AccountResult {
        val current = auth ?: return AccountResult.Error("Firebase is not configured yet. Add google-services.json to the app folder.")
        if (BuildConfig.FIREBASE_EMULATORS) return AccountResult.Error("Use email/password for local emulator accounts. Test Google sign-in against your configured Firebase project.")
        return googleAccountSignIn(context, current)
    }
    fun signOut() { auth?.signOut() }
    suspend fun clearCredentialState() {
        try {
            androidx.credentials.CredentialManager.create(applicationContext)
                .clearCredentialState(androidx.credentials.ClearCredentialStateRequest())
        } catch (e: CancellationException) { throw e }
        catch (_: androidx.credentials.exceptions.ClearCredentialException) { /* Firebase session is already signed out. */ }
    }
    suspend fun idToken(): String = auth?.currentUser?.getIdToken(false)?.await()?.token
        ?: error("Sign in before requesting AI recommendations.")

    suspend fun loadUser(uid: String): Map<String, Any> = withTimeout(20000) {
        val ref = requireNotNull(db).collection("users").document(uid)
        val snapshot = ref.get(Source.SERVER).await()
        if (snapshot.exists()) snapshot.data.orEmpty() else {
            val profile = StudentProfile(name = auth?.currentUser?.displayName.orEmpty(), email = auth?.currentUser?.email.orEmpty())
            val data: Map<String, Any> = mapOf("profile" to profile.cloudMap(), "saved" to emptyList<String>(), "targetId" to "", "activityDays" to emptyList<String>())
            ref.set(data).await()
            data
        }
    }
    fun listenUser(uid: String, update: (Map<String, Any>) -> Unit, failure: (Exception) -> Unit): ListenerRegistration =
        requireNotNull(db).collection("users").document(uid).addSnapshotListener { snapshot, error ->
            if (error != null) failure(error) else snapshot?.data?.let(update)
        }
    fun listenLearning(uid: String, update: (List<CloudLearning>) -> Unit, failure: (Exception) -> Unit): ListenerRegistration =
        requireNotNull(db).collection("users").document(uid).collection("learning").addSnapshotListener { snapshot, error ->
            if (error != null) failure(error) else if (snapshot != null) update(snapshot.documents.mapNotNull { doc ->
                val skill = LearningLibrary.find { skillId(it.skill) == doc.id }?.skill ?: return@mapNotNull null
                CloudLearning(skill, doc.getString("notes").orEmpty(), doc.getBoolean("completed") == true)
            })
        }
    fun listenRoles(update: (List<Role>) -> Unit, failure: (Exception) -> Unit): ListenerRegistration =
        requireNotNull(db).collection("opportunities").addSnapshotListener { snapshot, error ->
            if (error != null) failure(error) else if (snapshot != null) update(snapshot.documents.mapNotNull { doc ->
                roleFromFields(doc.id, doc.data.orEmpty())
            })
        }
    fun write(uid: String, fields: Map<String, Any>, complete: (Exception?) -> Unit) {
        requireNotNull(db).collection("users").document(uid).set(fields, SetOptions.merge())
            .addOnSuccessListener { complete(null) }.addOnFailureListener { complete(it) }
    }
    fun save(uid: String, id: String, remove: Boolean, complete: (Exception?) -> Unit) =
        write(uid, mapOf("saved" to if (remove) FieldValue.arrayRemove(id) else FieldValue.arrayUnion(id)), complete)
    fun record(uid: String, skill: String, notes: String, completed: Boolean, day: String, complete: (Exception?) -> Unit) {
        val firestore = requireNotNull(db)
        val user = firestore.collection("users").document(uid)
        val batch = firestore.batch()
        batch.set(user.collection("learning").document(skillId(skill)), mapOf("notes" to notes, "completed" to completed))
        if (completed) batch.update(user, "activityDays", FieldValue.arrayUnion(day))
        batch.commit().addOnSuccessListener { complete(null) }.addOnFailureListener { complete(it) }
    }
}
data class CloudLearning(val skill: String, val notes: String, val completed: Boolean)
fun skillId(label: String) = label.lowercase().replace(" ", "-")
fun StudentProfile.cloudMap(): Map<String, String> = mapOf("name" to name, "email" to email, "phone" to phone,
    "education" to education, "skills" to skills, "summary" to summary, "projects" to projects,
    "experience" to experience, "location" to location, "goal" to goal)
fun profileFromCloud(data: Map<*, *>): StudentProfile {
    fun field(key: String) = data[key] as? String ?: ""
    return StudentProfile(field("name"), field("email"), field("phone"), field("education"), field("skills"),
        field("summary"), field("projects"), field("experience"), field("location"), field("goal").ifBlank { "Internship" })
}
