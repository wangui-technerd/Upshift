package ke.upshift.app

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URI
import java.time.LocalDate

data class RecruiterCompany(val id:String,val name:String,val website:String,val description:String,val status:String,val offerings:List<String>)
data class RecruiterVacancy(val id:String,val companyId:String,val status:String,val revision:Int,val note:String,val payload:JSONObject)
fun JSONArray.texts() = (0 until length()).mapNotNull { opt(it) as? String }
fun recruiterStatus(status:String) = when(status) { "approved" -> "Approved"; "published" -> "Published"; "pending" -> "In review"; "rejected" -> "Changes requested"; "closed" -> "Closed"; "suspended" -> "Suspended"; else -> "Unconfirmed" }
fun recruiterHttps(value:String):Boolean = runCatching { URI(value).let { it.scheme=="https" && !it.host.isNullOrBlank() && it.userInfo==null && it.port in listOf(-1,443) } }.getOrDefault(false)
fun recruiterPayload(draft:Map<String,String>):JSONObject {
    fun value(key:String)=draft[key].orEmpty().trim()
    require(value("title").length in 3..200) { "Enter a role title of 3–200 characters." }
    require(value("location").length in 2..200) { "Enter a location." }
    require(value("description").length in 20..20000) { "Describe the role in at least 20 characters." }
    require(recruiterHttps(value("source_url"))) { "Enter the official advert's full https:// address." }
    require(value("application_url").isBlank() || recruiterHttps(value("application_url"))) { "Use an https:// application address." }
    require(value("career_level") in listOf("internship","student_attachment","graduate_trainee","entry_level")) { "Choose a career stage." }
    val body=JSONObject()
    listOf("title","location","description","source_url","career_level","arrangement").forEach { body.put(it,value(it)) }
    listOf("skills","responsibilities","requirements","eligibility").forEach { key ->
        val parts=value(key).split(if(key=="skills") "," else "\n").map { it.trim() }.filter { it.isNotEmpty() }.distinct()
        require(parts.size <= if(key=="skills")40 else 30) { "Too many entries in $key." }
        require(parts.all { it.length<=2000 }) { "Keep each $key entry under 2,000 characters." }
        require(key!="eligibility" || parts.isNotEmpty()) { "Explain who can apply." }
        body.put(key,JSONArray(parts))
    }
    val deadline=value("deadline")
    require(deadline.isBlank() || runCatching { LocalDate.parse(deadline) }.isSuccess) { "Enter the closing date as YYYY-MM-DD." }
    body.put("deadline",deadline.ifBlank { null } ?: JSONObject.NULL)
    body.put("application_url",value("application_url").ifBlank { null } ?: JSONObject.NULL)
    return body
}

class RecruiterClient(private val backend:FirebaseBackend) {
    private suspend fun request(path:String,method:String="GET",body:JSONObject?=null):JSONObject {
        val base=BuildConfig.VACANCY_BASE_URL.trimEnd('/')
        require(base.isNotBlank()) { "Company service is not configured. Set vacancyBaseUrl in your local Gradle configuration." }
        val url=URL("$base/listings$path")
        require(url.protocol=="https" || (BuildConfig.DEBUG && url.protocol=="http" && url.host in listOf("10.0.2.2","127.0.0.1","localhost"))) { "Use HTTPS for the company service." }
        val token=backend.idToken()
        return withContext(Dispatchers.IO) {
            val connection=url.openConnection() as HttpURLConnection
            try {
                connection.requestMethod=method;connection.instanceFollowRedirects=false
                connection.connectTimeout=10000;connection.readTimeout=20000
                connection.setRequestProperty("Authorization","Bearer $token")
                if(body!=null) { connection.setRequestProperty("Content-Type","application/json; charset=utf-8");connection.doOutput=true;connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) } }
                val code=connection.responseCode
                val stream=if(code in 200..299)connection.inputStream else connection.errorStream
                val raw=stream?.bufferedReader()?.use { it.readText() }.orEmpty()
                val result=runCatching { JSONObject(raw) }.getOrDefault(JSONObject())
                if(code !in 200..299)error(result.optJSONObject("error")?.optString("message")?.takeIf { it.isNotBlank() } ?: "Company request failed ($code). Check your connection and retry.")
                result
            } finally { connection.disconnect() }
        }
    }
    private suspend fun pages(path:String):List<JSONObject> {
        val rows=mutableListOf<JSONObject>();val seen=mutableSetOf<String>();var cursor=""
        do {
            val page=request("$path?limit=100"+if(cursor.isBlank())"" else "&after=$cursor")
            val items=page.optJSONArray("items") ?: JSONArray()
            (0 until items.length()).forEach { rows.add(items.getJSONObject(it)) }
            cursor=if(page.isNull("next_cursor"))"" else page.optString("next_cursor")
            require(cursor.isBlank() || (cursor.matches(Regex("[A-Za-z0-9_-]{1,100}")) && seen.add(cursor))) { "The service returned an invalid page cursor. Retry." }
        } while(cursor.isNotBlank())
        return rows
    }
    suspend fun companies()=pages("/companies/mine").map { RecruiterCompany(it.getString("id"),it.getString("name"),it.optString("website"),it.optString("description"),it.optString("status"),it.optJSONArray("offerings")?.texts().orEmpty()) }
    suspend fun vacancies()=pages("/submissions/mine").map { RecruiterVacancy(it.getString("id"),it.getString("company_id"),it.optString("status"),it.optInt("revision"),it.optString("review_note"),it.getJSONObject("payload")) }
    suspend fun register(body:JSONObject)=request("/companies","POST",body).getString("id")
    suspend fun submit(companyId:String,body:JSONObject)=request("/companies/$companyId/vacancies","POST",body).getString("id")
    suspend fun withdraw(id:String) { request("/submissions/$id/withdraw","POST") }
}
