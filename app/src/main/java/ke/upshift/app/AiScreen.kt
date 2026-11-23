package ke.upshift.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class AiClient(private val backend: FirebaseBackend) {
    suspend fun call(path: String, body: JSONObject): JSONObject {
        val base = BuildConfig.AI_BASE_URL.trimEnd('/')
        require(base.isNotBlank()) { "AI service is not configured yet." }
        val url = URL(base + path)
        require(url.protocol == "https" || (BuildConfig.DEBUG && url.protocol == "http" && url.host in setOf("10.0.2.2", "127.0.0.1", "localhost"))) { "Use an HTTPS AI service address." }
        val token = backend.idToken()
        return withContext(Dispatchers.IO) {
            val connection = url.openConnection() as HttpURLConnection
            try {
                connection.instanceFollowRedirects = false
                connection.requestMethod = "POST"
                connection.connectTimeout = 10000; connection.readTimeout = 30000
                connection.setRequestProperty("Authorization", "Bearer $token")
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.doOutput = true
                connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
                val status = connection.responseCode
                val raw = (if (status in 200..299) connection.inputStream else connection.errorStream)
                    ?.bufferedReader()?.use { it.readText() }.orEmpty()
                val result = runCatching { JSONObject(raw) }.getOrDefault(JSONObject())
                if (status !in 200..299) error(result.optJSONObject("error")?.optString("message")?.takeIf { it.isNotBlank() }
                    ?: "AI request could not finish ($status). Please retry.")
                result
            } finally { connection.disconnect() }
        }
    }
}

@Composable fun AiScreen(state: AppState, back: () -> Unit) {
    var feedback by rememberSaveable { mutableStateOf("") }
    var reply by rememberSaveable { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    fun request(path: String, body: JSONObject) {
        busy = true; reply = ""
        scope.launch {
            try {
                val result = AiClient(state.backend).call(path, body)
                reply = if (path == "/sentiment") "Feedback sentiment: ${result.optString("label")}" else {
                    val matches = result.optJSONArray("matches")
                    if (matches == null || matches.length() == 0) "No relevant research jobs were found for this profile."
                    else (0 until matches.length()).joinToString("\n\n") { i ->
                        val match = matches.getJSONObject(i)
                        val absent = match.optJSONArray("skills_not_mentioned")
                        "${match.optString("title")} - ${match.optString("company_name")}\nText similarity: ${"%.3f".format(match.optDouble("similarity"))}" +
                            if (absent != null && absent.length() > 0) "\nSkills not mentioned: ${(0 until absent.length()).joinToString { absent.getString(it) }}" else ""
                    }
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { reply = e.message ?: "Could not reach the AI service. Retry when connected." }
            finally { busy = false }
        }
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp), verticalArrangement=Arrangement.spacedBy(16.dp)) {
        TextButton(onClick=back) { Text("Back") }
        Heading("AI tools", "Explore research job matches and feedback sentiment.")
        Text("Research job results may be expired or outside Kenya. Text similarity is separate from the skills match shown elsewhere in the app.")
        Button(enabled=!busy && state.userId != null, onClick={
            val p=state.profile
            val text=listOf(p.education,p.skills,p.summary,p.projects,p.experience).filter { it.isNotBlank() }.joinToString("\n")
            if(text.isBlank()) reply="Add skills or project details to your profile first."
            else request("/recommendations",JSONObject().put("resume_text",text).put("top_k",5))
        }, modifier=Modifier.fillMaxWidth()) { Text("Find research job matches") }
        OutlinedTextField(value=feedback,onValueChange={if(it.length<=10000)feedback=it},label={Text("Feedback about UpShift")},modifier=Modifier.fillMaxWidth())
        OutlinedButton(enabled=!busy && feedback.isNotBlank() && state.userId != null,onClick={request("/sentiment",JSONObject().put("text",feedback.trim()))},modifier=Modifier.fillMaxWidth()) { Text("Analyse feedback sentiment") }
        Text("Only the text needed for the selected request is sent. Your contact fields are excluded from job matching.",style=MaterialTheme.typography.bodySmall)
        if(busy) CircularProgressIndicator()
        if(reply.isNotBlank()) Text(reply)
        Spacer(Modifier.height(80.dp))
    }
}
