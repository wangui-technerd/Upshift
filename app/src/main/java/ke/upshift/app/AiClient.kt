package ke.upshift.app

import com.google.firebase.FirebaseNetworkException
import com.google.firebase.auth.FirebaseAuthException
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URI

internal enum class AiProblem { CONFIGURATION, SIGN_IN, TOKEN_REJECTED, ACCESS_DENIED, INVALID_INPUT, RATE_LIMIT, TIMEOUT, NETWORK, SERVICE, RESPONSE }

internal class AiFailure(val problem: AiProblem, val retryAfterSeconds: Long = 0) : Exception()

internal data class VacancyMatch(
    val id: String,
    val title: String,
    val company: String?,
    val location: String?,
    val deadline: String?,
    val description: String?,
    val requirements: List<String>,
    val eligibility: List<String>,
    val matchedSkills: List<String>,
    val missingSkills: List<String>,
    val similarity: Double?,
    val applicationUrl: String?,
)

internal fun profileRecommendationText(profile: StudentProfile): String =
    listOf(
        "Education" to profile.education, "Skills" to profile.skills, "Summary" to profile.summary,
        "Projects" to profile.projects, "Experience" to profile.experience, "Goal" to profile.goal,
    ).filter { it.second.isNotBlank() }.joinToString("\n") { (label, value) -> "$label: ${value.trim()}" }

internal fun hasRecommendationEvidence(profile: StudentProfile): Boolean =
    listOf(profile.education, profile.skills, profile.summary, profile.projects, profile.experience)
        .any { it.isNotBlank() }

internal fun apiAddress(base: String, path: String, debug: Boolean): URI {
    val uri = runCatching { URI(base.trim()) }.getOrNull()
    val local = debug && uri?.scheme == "http" && uri.host in setOf("10.0.2.2", "127.0.0.1", "localhost")
    if (uri == null || uri.host.isNullOrBlank() || (uri.scheme != "https" && !local) ||
        uri.rawUserInfo != null || uri.rawQuery != null || uri.rawFragment != null
    ) throw AiFailure(AiProblem.CONFIGURATION)
    return URI(uri.toASCIIString().trimEnd('/') + path)
}

internal fun applicationAddress(url: String?, allowed: Boolean): String? {
    if (!allowed || url.isNullOrBlank()) return null
    val uri = runCatching { URI(url) }.getOrNull() ?: return null
    return url.takeIf {
        uri.scheme.equals("https", ignoreCase = true) && !uri.host.isNullOrBlank() && uri.rawUserInfo == null
    }
}

internal data class AiHttpResult(val status: Int, val body: String, val retryAfter: String? = null)

internal suspend fun authorizedAiRequest(
    token: suspend (Boolean) -> String,
    send: suspend (String) -> AiHttpResult,
): AiHttpResult {
    val first = send(token(false))
    return if (first.status == 401) send(token(true)) else first
}

internal fun requireAiSuccess(result: AiHttpResult): String = when (result.status) {
    in 200..299 -> result.body
    401 -> throw AiFailure(AiProblem.TOKEN_REJECTED)
    403 -> throw AiFailure(AiProblem.ACCESS_DENIED)
    400, 422 -> throw AiFailure(AiProblem.INVALID_INPUT)
    408, 504 -> throw AiFailure(AiProblem.TIMEOUT)
    429 -> throw AiFailure(AiProblem.RATE_LIMIT, result.retryAfter?.toLongOrNull()?.coerceAtLeast(0) ?: 60)
    in 500..599 -> throw AiFailure(AiProblem.SERVICE)
    else -> throw AiFailure(AiProblem.RESPONSE)
}

private fun JSONObject.stringOrNull(key: String) =
    (opt(key) as? String)?.trim()?.takeIf { it.isNotEmpty() }

private fun JSONArray?.strings(): List<String> = if (this == null) emptyList() else
    (0 until length()).mapNotNull { (opt(it) as? String)?.trim()?.takeIf(String::isNotEmpty) }

private fun JSONObject.skillLabels(key: String, fallback: String): List<String> {
    val entries = optJSONArray(key) ?: return optJSONArray(fallback).strings()
    return (0 until entries.length()).mapNotNull { entries.optJSONObject(it)?.stringOrNull("label") }
}

internal fun parseVacancies(body: JSONObject): List<VacancyMatch> {
    val array = body.getJSONArray("matches")
    if (body.optString("status") == "no_match" && array.length() == 0) return emptyList()
    if (body.optString("status") != "matches_found" || array.length() == 0) throw AiFailure(AiProblem.RESPONSE)
    return (0 until array.length()).map { index ->
        val item = array.getJSONObject(index)
        VacancyMatch(
            id = item.stringOrNull("job_id") ?: throw AiFailure(AiProblem.RESPONSE),
            title = item.stringOrNull("title") ?: throw AiFailure(AiProblem.RESPONSE),
            company = item.stringOrNull("company_name"),
            location = item.stringOrNull("location"),
            deadline = item.stringOrNull("expiry_date"),
            description = item.stringOrNull("description"),
            requirements = item.optJSONArray("requirements").strings(),
            eligibility = item.optJSONArray("eligibility").strings(),
            matchedSkills = item.skillLabels("matched_skills", "skills_mentioned"),
            missingSkills = item.skillLabels("required_skills_not_mentioned", "skills_not_mentioned"),
            similarity = (item.opt("similarity") as? Number)?.toDouble()?.takeIf { it.isFinite() && it in -1.0..1.0 },
            applicationUrl = applicationAddress(
                item.stringOrNull("application_url"), item.opt("ready_for_live_application") == true,
            ),
        )
    }.distinctBy { it.id }
}

internal class AiClient(private val backend: FirebaseBackend) {
    suspend fun recommendations(profile: StudentProfile, location: String?, months: Int?): List<VacancyMatch> {
        val text = profileRecommendationText(profile)
        if (!hasRecommendationEvidence(profile) || text.length > 50000) throw AiFailure(AiProblem.INVALID_INPUT)
        val payload = JSONObject().put("resume_text", text).put("catalogue", "live").put("top_k", 5)
        location?.let { payload.put("location", it) }
        months?.let { payload.put("experience_months", it) }
        return parse { parseVacancies(call("/recommendations", payload)) }
    }

    suspend fun sentiment(feedback: String): String {
        if (feedback.isBlank() || feedback.length > 10000) throw AiFailure(AiProblem.INVALID_INPUT)
        return parse {
            val label = call("/sentiment", JSONObject().put("text", feedback)).stringOrNull("label")
            label?.takeIf { it in setOf("negative", "neutral", "positive") } ?: throw AiFailure(AiProblem.RESPONSE)
        }
    }

    private suspend fun <T> parse(block: suspend () -> T): T =
        try { block() } catch (_: JSONException) { throw AiFailure(AiProblem.RESPONSE) }

    private suspend fun call(path: String, payload: JSONObject): JSONObject {
        val address = apiAddress(BuildConfig.AI_BASE_URL, path, BuildConfig.DEBUG)
        try {
            val result = authorizedAiRequest(
                token = { refresh ->
                    if (backend.uid == null) throw AiFailure(AiProblem.SIGN_IN)
                    try {
                        withTimeout(15000) { backend.idToken(refresh) }
                    } catch (e: IllegalStateException) {
                        if (backend.uid == null) throw AiFailure(AiProblem.SIGN_IN)
                        throw e
                    }
                },
                send = { token -> withContext(Dispatchers.IO) { post(address, token, payload.toString()) } },
            )
            return JSONObject(requireAiSuccess(result))
        } catch (_: TimeoutCancellationException) {
            throw AiFailure(AiProblem.TIMEOUT)
        } catch (e: CancellationException) {
            throw e
        } catch (_: FirebaseNetworkException) {
            throw AiFailure(AiProblem.NETWORK)
        } catch (e: FirebaseAuthException) {
            val invalidSession = e.errorCode in setOf(
                "ERROR_USER_TOKEN_EXPIRED", "ERROR_INVALID_USER_TOKEN", "ERROR_USER_DISABLED", "ERROR_USER_NOT_FOUND",
            )
            throw AiFailure(if (invalidSession || backend.uid == null) AiProblem.SIGN_IN else AiProblem.SERVICE)
        } catch (_: SocketTimeoutException) {
            throw AiFailure(AiProblem.TIMEOUT)
        } catch (_: IOException) {
            throw AiFailure(AiProblem.NETWORK)
        }
    }

    private fun post(address: URI, token: String, payload: String): AiHttpResult {
        val connection = address.toURL().openConnection() as HttpURLConnection
        try {
            connection.instanceFollowRedirects = false
            connection.requestMethod = "POST"
            connection.connectTimeout = 10000
            connection.readTimeout = 30000
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            connection.setRequestProperty("Accept", "application/json")
            connection.doOutput = true
            connection.outputStream.use { it.write(payload.toByteArray(Charsets.UTF_8)) }
            val status = connection.responseCode
            val body = if (status in 200..299) {
                connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            } else ""
            return AiHttpResult(status, body, connection.getHeaderField("Retry-After"))
        } finally {
            connection.disconnect()
        }
    }
}
