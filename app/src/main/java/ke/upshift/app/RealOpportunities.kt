package ke.upshift.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.URI
import java.time.LocalDate

/** Bundled source-backed research; no fabricated fallback and no client-side publishing. */
class RealOpportunitiesRepository(context: Context) : OpportunitiesRepository {
    private val applicationContext = context.applicationContext
    private val catalogue by lazy { applicationContext.assets.open("opportunities.json").bufferedReader().use { reader ->
        val rows = JSONArray(reader.readText())
        (0 until rows.length()).mapNotNull { index ->
            val row = rows.getJSONObject(index)
            roleFromFields(row.getString("id"), row.keys().asSequence().associateWith { key ->
                when (val value = row.opt(key)) {
                    JSONObject.NULL -> null
                    is JSONArray -> (0 until value.length()).map { value.opt(it) }
                    else -> value
                }
            })
        }
    } }
    override fun roles() = catalogue.filter { it.isDiscoverable() }
}

fun roleFromFields(id: String, fields: Map<String, Any?>): Role? {
    fun text(key: String) = (fields[key] as? String).orEmpty().trim()
    fun strings(key: String) = (fields[key] as? List<*>)?.filterIsInstance<String>()
        ?.map { it.trim() }?.filter { it.isNotEmpty() }.orEmpty()
    val title = text("title")
    val company = text("company")
    if (id.isBlank() || title.isBlank() || company.isBlank()) return null
    return Role(id, title, company, text("location"), strings("skills").distinctBy { it.lowercase() },
        text("description"), strings("responsibilities"), strings("requirements"),
        strings("eligibility").ifEmpty { listOf("Eligibility is unconfirmed. Check the source advert.") },
        text("arrangement"), text("source_url"), text("availability_status"),
        text("collected_date"), text("deadline"), text("research_notes"), text("skill_interpretation"),
        text("company_website"), text("company_description"), strings("company_offerings"))
}

fun Role.hasSource(): Boolean = runCatching {
    val uri = URI(sourceUrl)
    uri.scheme == "https" && !uri.host.isNullOrBlank() && uri.userInfo == null
}.getOrDefault(false)

fun Role.isDiscoverable(today: LocalDate = LocalDate.now()): Boolean {
    if (!hasSource() || availabilityStatus !in setOf("published", "needs_primary_review", "listed_on_source")) return false
    if (deadline.isBlank()) return true
    // Keep date-only deadlines visible through their final calendar day.
    val closing = runCatching { LocalDate.parse(deadline.take(10)) }.getOrNull() ?: return false
    return !closing.isBefore(today)
}

/** Cloud records override matching bundle IDs, including withdrawals and archived status. */
fun mergeOpportunities(bundled: List<Role>, cloud: List<Role>, today: LocalDate = LocalDate.now()): List<Role> =
    (bundled + cloud).associateBy { it.id }.values.associateBy { role ->
        // Cloud publication/withdrawal replaces a research copy even if its ID differs.
        if (role.hasSource()) URI(role.sourceUrl).let { "${it.host.lowercase()}${it.rawPath.orEmpty().trimEnd('/')}?${it.rawQuery.orEmpty()}" }
        else role.id
    }.values.filter { it.isDiscoverable(today) }
