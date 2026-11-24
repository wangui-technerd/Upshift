package ke.upshift.app

import android.content.Context
import androidx.compose.runtime.*
import org.json.JSONObject
import java.time.LocalDate
import java.time.ZoneId
import kotlin.math.roundToInt
import com.google.firebase.firestore.ListenerRegistration
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class Role(
    val id: String, val title: String, val company: String, val location: String,
    val skills: List<String>, val description: String,
    val responsibilities: List<String> = listOf("Work with your team to deliver small, well-tested improvements.", "Document your work and communicate progress."),
    val requirements: List<String> = listOf("Evidence of relevant coursework or a personal project.", "Clear communication and willingness to learn."),
    val eligibility: List<String> = listOf("Applicants based in Kenya.", "Students or recent graduates; no previous paid experience required."),
    val arrangement: String = "Internship · 3 months",
    val sourceUrl: String = "",
    val availabilityStatus: String = "unconfirmed",
    val collectedDate: String = "",
    val deadline: String = "",
    val researchNotes: String = "",
    val skillInterpretation: String = "",
    val companyWebsite: String = "",
    val companyDescription: String = "",
    val companyOfferings: List<String> = emptyList()
)
interface OpportunitiesRepository { fun roles(): List<Role> }
class DemoOpportunitiesRepository : OpportunitiesRepository {
    override fun roles() = listOf(
        Role("frontend", "Frontend engineering intern", "Acacia Studio", "Nairobi · Hybrid", listOf("HTML", "CSS", "JavaScript", "Git"), "Turn designs into clear, accessible interfaces for everyday users.", listOf("Build responsive pages from design files.", "Test layouts on mobile and desktop.", "Review changes with a developer and respond to feedback."), listOf("Working knowledge of HTML and CSS.", "A small web project you can walk us through.", "Basic JavaScript and Git."), listOf("Based in Kenya and available for two on-site days in Nairobi.", "Undergraduate or recent graduate in computing or a related field.", "Available for a three-month internship.")),
        Role("data", "Data analyst intern", "Mawingu Insights", "Kenya · Remote", listOf("Excel", "SQL", "Python", "Statistics"), "Find useful patterns in data and explain them through clear reports.", listOf("Clean and validate spreadsheet data.", "Write queries and summarise findings.", "Present a short weekly report."), listOf("Comfort with spreadsheets and basic statistics.", "An example of a data analysis project.", "Access to a computer for remote work.")),
        Role("marketing", "Digital marketing assistant", "Coast Creative", "Mombasa · On-site", listOf("Writing", "Canva", "Excel"), "Help a creative team plan campaigns and communicate with their audience.", listOf("Draft and schedule social content.", "Create simple campaign visuals.", "Track engagement in a spreadsheet."), listOf("Clear written communication.", "Examples of content or designs, including coursework."), listOf("Able to work on-site in Mombasa.", "Students and recent graduates in marketing, media or related fields.")),
        Role("android", "Junior Android developer", "Open Savannah", "Remote · Kenya", listOf("Kotlin", "Git", "Android", "Testing", "REST APIs"), "Build thoughtful Android features with a team that values usable mobile experiences.", listOf("Implement and test Android screens.", "Connect UI state to application data.", "Investigate bugs and explain your fixes."), listOf("A Kotlin Android project, academic or personal.", "Understanding of the Activity lifecycle.", "Basic source control and testing."), listOf("Remote applications from Kenya accepted.", "Final-year student or graduate with a relevant project portfolio."), "Entry level · Full time"),
        Role("design", "Product design intern", "Kijani Digital", "Nairobi · Hybrid", listOf("Figma", "Accessibility", "Writing", "Research"), "Help make services easier to understand and use.", listOf("Sketch user journeys and prototype screens.", "Observe usability sessions and record findings.", "Improve designs using feedback."), listOf("A short portfolio or coursework case study.", "Interest in accessibility and user research.")),
        Role("support", "IT support trainee", "Pamoja Systems", "Nairobi · On-site", listOf("Networking", "Communication", "Excel", "Git"), "Support colleagues with everyday technical problems and keep clear records.", listOf("Record and triage support requests.", "Help configure devices with supervision.", "Write short troubleshooting notes."), listOf("Basic networking and operating-system knowledge.", "Patient communication and careful documentation."))
    )
}
data class StudentProfile(val name: String = "", val email: String = "", val phone: String = "", val education: String = "", val skills: String = "", val summary: String = "", val projects: String = "", val experience: String = "", val location: String = "", val goal: String = "Internship") {
    private val normalisedSkills by lazy { skills.split(",").map { it.trim().lowercase() }.filter { it.isNotEmpty() }.toSet() }
    fun skillSet() = normalisedSkills
}
interface MatchScorer { fun percentage(role: Role, profile: StudentProfile): Int? }
class SkillCoverageScorer : MatchScorer {
    override fun percentage(role: Role, profile: StudentProfile): Int? {
        if (profile.skillSet().isEmpty() || role.skills.isEmpty()) return null
        return (100.0 * role.skills.count { it.lowercase() in profile.skillSet() } / role.skills.size).roundToInt()
    }
}
fun learningStreak(days: Set<LocalDate>, today: LocalDate): Int {
    var cursor = if (today in days) today else today.minusDays(1)
    var count = 0
    while (cursor in days) { count++; cursor = cursor.minusDays(1) }
    return count
}
data class LearningStep(val skill: String, val title: String, val brief: String, val minutes: Int = 30)
val LearningLibrary = listOf(
    LearningStep("HTML", "Build a page with a clear structure", "Create a page with a heading, navigation, main content and a labelled contact form. Explain why each element belongs there."),
    LearningStep("CSS", "Make a layout work on a small screen", "Build a card layout that adapts from a narrow phone to a desktop. Check readable text and comfortable spacing."),
    LearningStep("JavaScript", "Make a form respond to input", "Validate a small form and show useful messages. Check empty, valid and invalid inputs."),
    LearningStep("Git", "Practise a small reviewable change", "Create a branch, make one focused change and write a clear commit message. Explain how you would undo it safely."),
    LearningStep("SQL", "Find answers with joins and groups", "Create two related tables. Write a join and an aggregate query, then explain what each result means."),
    LearningStep("Python", "Clean and summarise a small dataset", "Read a CSV, handle missing values and calculate a useful summary. Record your assumptions."),
    LearningStep("Excel", "Turn a spreadsheet into a useful summary", "Clean a small table, use a formula and create a summary chart. Check the result by hand."),
    LearningStep("Statistics", "Explain an average and its limits", "Compare mean and median on a small dataset. Identify an outlier and explain its effect."),
    LearningStep("Kotlin", "Model and validate a student profile", "Write a data class and a validation function. Try empty, valid and incomplete profiles."),
    LearningStep("Android", "Build a screen that survives rotation", "Create an Android screen with editable state. Rotate the device and check that progress is preserved."),
    LearningStep("Testing", "Test a meaningful edge case", "Pick a function from a project. Test its normal behaviour, an empty input and an important boundary."),
    LearningStep("REST APIs", "Handle a request and its failure", "Sketch loading, success, empty and error states for a list fetched from an API. Explain a safe retry action."),
    LearningStep("Writing", "Write a clear opportunity summary", "Describe a project in three short paragraphs: problem, your contribution and result. Ask someone to check clarity."),
    LearningStep("Canva", "Design a readable campaign card", "Create a visual with one clear message. Check contrast, text size and a single call to action."),
    LearningStep("Figma", "Prototype one complete task", "Create a short clickable journey with an entry point, completion state and a way back."),
    LearningStep("Accessibility", "Review a screen for access barriers", "Check contrast, labels, touch targets, text resizing and screen-reader order. Record three improvements."),
    LearningStep("Research", "Run a short usability session", "Ask someone to complete one task without hints. Record where they hesitate and propose one improvement."),
    LearningStep("Networking", "Explain a connection from device to server", "Draw the path of a web request. Explain DNS, IP addresses and HTTP in your own words."),
    LearningStep("Communication", "Write a useful support response", "Respond to a sample support request with a clear question, next step and expected outcome.")
)
interface CoachRepository { fun reply(question: String, role: Role?, state: AppState): String }
class LocalCoachRepository : CoachRepository {
    override fun reply(question: String, role: Role?, state: AppState): String {
        val target = role ?: state.rankedRoles().firstOrNull()
        val namedRole = state.rankedRoles().firstOrNull { question.contains(it.title, true) || question.contains(it.company, true) }
        val selected = namedRole ?: target
        return careerReply(question, selected, selected?.let { state.gaps(it) }.orEmpty(), selected?.let { state.score(it) }, state.profile)
    }
}
class AppState(context: Context, val repository: OpportunitiesRepository = RealOpportunitiesRepository(context), private val scorer: MatchScorer = SkillCoverageScorer(), val coach: CoachRepository = LocalCoachRepository()) {
    private val context = context.applicationContext
    val backend = FirebaseBackend(this.context)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var listeners = listOf<ListenerRegistration>()
    private val handler = android.os.Handler(android.os.Looper.getMainLooper())
    private val persistDraft = Runnable { persistProfile() }
    private var prefs = this.context.getSharedPreferences("upshift", Context.MODE_PRIVATE)
    var userId by mutableStateOf<String?>(null); private set
    var connecting by mutableStateOf(false); private set
    var restoring by mutableStateOf(backend.uid != null); private set
    var syncMessage by mutableStateOf(""); private set
    var cloudReady by mutableStateOf(false); private set
    private var bundledRoles = emptyList<Role>()
    private var cloudRoles = emptyList<Role>()
    var roles by mutableStateOf(emptyList<Role>()); private set
    var profile by mutableStateOf(StudentProfile()); private set
    var entered by mutableStateOf(false); private set
    var saved by mutableStateOf(emptySet<String>()); private set
    var completed by mutableStateOf(emptySet<String>()); private set
    var activityDays by mutableStateOf(emptySet<String>()); private set
    private var evidence by mutableStateOf("{}")
    var targetId by mutableStateOf<String?>(null); private set
    private var profileDirty = false
    private val pendingSaved = mutableMapOf<String, Boolean>()
    private val pendingLearning = mutableMapOf<String, PendingLearning>()
    private var recommendationProfile: StudentProfile? = null
    private var recommendationResults = mutableStateOf<List<VacancyMatch>?>(null)
    internal fun recommendationsFor(profile: StudentProfile): MutableState<List<VacancyMatch>?> {
        if (recommendationProfile != profile) {
            recommendationProfile = profile
            recommendationResults = mutableStateOf(null)
        }
        return recommendationResults
    }
    private fun clearRecommendations() {
        recommendationProfile = null
        recommendationResults = mutableStateOf(null)
    }
    private var targetDirty = false
    private var pendingTarget = ""
    private var pendingWrites = 0
    var saving by mutableStateOf(false); private set
    init {
        loadLocal()
        scope.launch {
            bundledRoles = withContext(Dispatchers.IO) { repository.roles() }
            roles = mergeOpportunities(bundledRoles, cloudRoles)
        }
        if (backend.uid != null) scope.launch { try { connectAccount() } finally { restoring = false } }
    }
    private fun loadLocal() {
        val json = runCatching { JSONObject(prefs.getString("profile", "{}")!!) }.getOrDefault(JSONObject())
        profile = profileFromCloud(json.keys().asSequence().associateWith { json.optString(it) })
        entered = prefs.getBoolean("entered", false)
        saved = prefs.getStringSet("saved", emptySet())!!.toSet()
        completed = prefs.getStringSet("completed", emptySet())!!.toSet()
        activityDays = prefs.getStringSet("activityDays", emptySet())!!.toSet()
        evidence = prefs.getString("evidence", "{}") ?: "{}"
        targetId = prefs.getString("target", null)
    }
    suspend fun connectAccount(name: String = ""): Boolean {
        val uid = backend.uid ?: return false
        handler.removeCallbacks(persistDraft)
        connecting = true; cloudReady = false; entered = false; syncMessage = ""
        clearRecommendations()
        listeners.forEach { it.remove() }; listeners = emptyList()
        // Never carry another account's or a guest's data into a cloud account.
        userId = uid; pendingWrites = 0; saving = false
        prefs = context.getSharedPreferences("upshift-account-$uid", Context.MODE_PRIVATE)
        profile = StudentProfile(); saved = emptySet(); completed = emptySet()
        activityDays = emptySet(); evidence = "{}"; targetId = null; cloudRoles = emptyList(); roles = bundledRoles
        profileDirty = prefs.getBoolean("profilePending", false)
        val localProfile = runCatching { JSONObject(prefs.getString("profile", "{}")!!) }.getOrDefault(JSONObject())
        if (profileDirty) profile = profileFromCloud(localProfile.keys().asSequence().associateWith { localProfile.optString(it) })
        pendingSaved.clear(); pendingLearning.clear(); targetDirty = prefs.getBoolean("targetPending", false)
        pendingTarget = prefs.getString("pendingTarget", "").orEmpty()
        val savedQueue = runCatching { JSONObject(prefs.getString("savedQueue", "{}")!!) }.getOrDefault(JSONObject())
        savedQueue.keys().forEach { pendingSaved[it] = savedQueue.optBoolean(it) }
        val learningQueue = runCatching { JSONObject(prefs.getString("learningQueue", "{}")!!) }.getOrDefault(JSONObject())
        learningQueue.keys().forEach { skill -> learningQueue.optJSONObject(skill)?.let {
            pendingLearning[skill] = PendingLearning(it.optString("notes"), it.optBoolean("completed"), it.optString("day"))
        } }
        return try {
            val data = backend.loadUser(uid)
            if (backend.uid != uid) return false
            applyCloud(data)
            if (profile.name.isBlank() && name.isNotBlank()) profile = profile.copy(name = name.trim())
            profile = profile.copy(email = backend.auth?.currentUser?.email.orEmpty())
            cloudReady = true
            listeners = listOf(
                backend.listenUser(uid, { if (userId == uid) applyCloud(it) }, { if (userId == uid) syncMessage = accountError(it) }),
                backend.listenLearning(uid, { rows -> if (userId == uid) {
                    val merged = rows.associateBy { it.skill }.toMutableMap()
                    pendingLearning.forEach { (skill, pending) -> merged[skill] = CloudLearning(skill, pending.notes, pending.completed) }
                    completed = merged.values.filter { it.completed }.map { it.skill }.toSet()
                    evidence = JSONObject(merged.values.associate { it.skill to it.notes }).toString()
                    prefs.edit().putStringSet("completed", completed).putString("evidence", evidence).apply()
                } }, { if (userId == uid) syncMessage = accountError(it) }),
                backend.listenRoles({ if (userId == uid) { cloudRoles = it; roles = mergeOpportunities(bundledRoles, cloudRoles) } }, { if (userId == uid) syncMessage = accountError(it) })
            )
            if (name.isNotBlank()) update(profile.copy(name = name.trim()))
            retrySync()
            entered = profile.name.isNotBlank() && profile.skills.isNotBlank()
            true
        } catch (e: TimeoutCancellationException) { syncMessage = "Loading timed out. Check your connection and retry."; false }
        catch (e: CancellationException) { throw e }
        catch (e: Exception) { syncMessage = accountError(e); false }
        finally { connecting = false }
    }
    private fun applyCloud(data: Map<String, Any>) {
        if (!profileDirty) (data["profile"] as? Map<*, *>)?.let { profile = profileFromCloud(it) }
        var cloudSaved = (data["saved"] as? List<*>)?.filterIsInstance<String>()?.toSet().orEmpty()
        pendingSaved.forEach { (id, remove) -> cloudSaved = if(remove) cloudSaved-id else cloudSaved+id }
        saved = cloudSaved
        targetId = (if(targetDirty) pendingTarget else data["targetId"] as? String)?.ifBlank { null }
        activityDays = (data["activityDays"] as? List<*>)?.filterIsInstance<String>()?.toSet().orEmpty() + pendingLearning.values.filter { it.completed }.map { it.day }
        cacheProfile()
        prefs.edit().putStringSet("saved", saved).putStringSet("activityDays", activityDays).putString("target", targetId).apply()
    }
    private fun callback(uid: String): (Exception?) -> Unit {
        pendingWrites++; saving = true
        return { error -> if (userId == uid) {
            pendingWrites = (pendingWrites - 1).coerceAtLeast(0); saving = pendingWrites > 0
            if (error != null) syncMessage = "Cloud save failed. Your local draft is retained. Retry after checking your connection."
        } }
    }
    private fun persistQueues() {
        val learning = JSONObject()
        pendingLearning.forEach { (skill, item) -> learning.put(skill, JSONObject().put("notes",item.notes).put("completed",item.completed).put("day",item.day)) }
        prefs.edit().putBoolean("profilePending",profileDirty).putBoolean("targetPending",targetDirty)
            .putString("pendingTarget",pendingTarget).putString("savedQueue",JSONObject(pendingSaved.toMap()).toString())
            .putString("learningQueue",learning.toString()).apply()
    }
    private fun sendSaved(uid: String, id: String, remove: Boolean) {
        val done=callback(uid)
        backend.save(uid,id,remove) { error ->
            if(userId==uid && error==null && pendingSaved[id]==remove) { pendingSaved.remove(id); persistQueues() }
            done(error)
        }
    }
    private fun sendTarget(uid: String, value: String) {
        val done=callback(uid)
        backend.write(uid,mapOf("targetId" to value)) { error ->
            if(userId==uid && error==null && pendingTarget==value) { targetDirty=false; persistQueues() }
            done(error)
        }
    }
    private fun sendLearning(uid: String, skill: String, item: PendingLearning) {
        val done=callback(uid)
        backend.record(uid,skill,item.notes,item.completed,item.day) { error ->
            if(userId==uid && error==null && pendingLearning[skill]==item) { pendingLearning.remove(skill); persistQueues() }
            done(error)
        }
    }
    fun retrySync() {
        val uid = userId ?: return
        if (!cloudReady) { scope.launch { connectAccount() }; return }
        syncMessage = ""
        if(profileDirty) persistProfile()
        pendingSaved.toMap().forEach { (id,remove) -> sendSaved(uid,id,remove) }
        if(targetDirty) sendTarget(uid,pendingTarget)
        pendingLearning.toMap().forEach { (skill,item) -> sendLearning(uid,skill,item) }
    }
    fun score(role: Role) = scorer.percentage(role, profile)
    fun rankedRoles() = roles.sortedWith(compareByDescending<Role> { score(it) ?: -1 }.thenBy { it.title })
    fun gaps(role: Role) = role.skills.filter { it.lowercase() !in profile.skillSet() }
    fun growthSteps(): List<LearningStep> {
        val targets = targetId?.let { id -> roles.filter { it.id == id } }?.takeIf { it.isNotEmpty() } ?: roles
        val needed = targets.flatMap { gaps(it) }.toSet()
        return LearningLibrary.filter { it.skill in needed || it.skill in completed }.sortedWith(compareByDescending<LearningStep> { step -> targets.count { step.skill in gaps(it) } }.thenBy { it.skill })
    }
    fun evidenceFor(skill: String) = runCatching { JSONObject(evidence).optString(skill) }.getOrDefault("")
    fun recordStep(skill: String, notes: String) {
        if (notes.trim().length !in 20..2000) { syncMessage = "Use a reflection of 20 to 2000 characters."; return }
        if (userId != null && !cloudReady) return
        evidence = JSONObject(evidence).apply { put(skill, notes.trim()) }.toString()
        completed = completed + skill
        val day = LocalDate.now(ZoneId.of("Africa/Nairobi")).toString()
        activityDays = activityDays + day
        prefs.edit().putString("evidence", evidence).putStringSet("completed", completed).putStringSet("activityDays", activityDays).apply()
        userId?.let { uid ->
            val item=PendingLearning(notes.trim(),true,day); pendingLearning[skill]=item; persistQueues(); sendLearning(uid,skill,item)
        }
    }
    fun undoStep(skill: String) {
        completed = completed - skill; prefs.edit().putStringSet("completed", completed).apply()
        userId?.let { uid ->
            val item=PendingLearning(evidenceFor(skill),false,""); pendingLearning[skill]=item; persistQueues(); sendLearning(uid,skill,item)
        }
    }
    fun streak() = learningStreak(activityDays.mapNotNull { runCatching { LocalDate.parse(it) }.getOrNull() }.toSet(), LocalDate.now(ZoneId.of("Africa/Nairobi")))
    fun xp() = completed.size * 25
    fun enter() { entered = true; prefs.edit().putBoolean("entered", true).apply(); flushProfile() }
    fun leave() { flushProfile(); backend.signOut(); scope.launch { backend.clearCredentialState() }; detach(); userId = null; cloudReady = false
        clearRecommendations()
        prefs = context.getSharedPreferences("upshift", Context.MODE_PRIVATE); loadLocal()
        pendingSaved.clear(); pendingLearning.clear(); targetDirty=false; pendingWrites=0; saving=false
        cloudRoles = emptyList(); roles = bundledRoles; entered = false; syncMessage = ""
        prefs.edit().putBoolean("entered", false).apply()
    }
    private fun detach() { handler.removeCallbacks(persistDraft); listeners.forEach { it.remove() }; listeners = emptyList(); profileDirty = false }
    fun close() { flushProfile(); detach(); scope.coroutineContext[kotlinx.coroutines.Job]?.cancel() }
    fun target(role: Role) { targetId = role.id; if (role.id !in saved) toggleSaved(role.id); prefs.edit().putString("target", targetId).apply()
        userId?.let { targetDirty=true; pendingTarget=role.id; persistQueues(); sendTarget(it,role.id) }
    }
    fun clearTarget() { targetId = null; prefs.edit().remove("target").apply()
        userId?.let { targetDirty=true; pendingTarget=""; persistQueues(); sendTarget(it,"") }
    }
    fun update(p: StudentProfile) {
        if (userId != null && !cloudReady) return
        profile = if (userId == null) p else p.copy(email = backend.auth?.currentUser?.email.orEmpty())
        // Keep keystrokes in Compose state; serialize and save once typing pauses.
        // onStop/Done/enter/sign-out still flush synchronously before leaving.
        profileDirty = true; handler.removeCallbacks(persistDraft); handler.postDelayed(persistDraft, 700)
    }
    fun flushProfile() { handler.removeCallbacks(persistDraft); if (profileDirty) persistProfile() }
    private fun cacheProfile() { prefs.edit().putString("profile", JSONObject(profile.cloudMap()).toString()).apply() }
    private fun persistProfile() {
        cacheProfile()
        val uid = userId
        if (uid != null) persistQueues()
        if (uid != null && cloudReady) {
            val snapshot = profile
            val done = callback(uid)
            backend.write(uid, mapOf("profile" to snapshot.cloudMap())) { error ->
                if (userId == uid && error == null && profile == snapshot) { profileDirty = false; persistQueues() }
                done(error)
            }
        } else if (uid == null) profileDirty = false
    }
    fun toggleSaved(id: String) {
        val remove = id in saved
        saved = if (remove) saved - id else saved + id; prefs.edit().putStringSet("saved",saved).apply()
        userId?.let { pendingSaved[id]=remove; persistQueues(); sendSaved(it,id,remove) }
    }
}

private data class PendingLearning(val notes: String, val completed: Boolean, val day: String)
