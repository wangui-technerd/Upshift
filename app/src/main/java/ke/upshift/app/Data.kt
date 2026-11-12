package ke.upshift.app

import android.content.Context
import androidx.compose.runtime.*
import org.json.JSONObject
import java.time.LocalDate
import java.time.ZoneId
import kotlin.math.roundToInt

data class Role(
    val id: String, val title: String, val company: String, val location: String,
    val skills: List<String>, val description: String,
    val responsibilities: List<String> = listOf("Work with your team to deliver small, well-tested improvements.", "Document your work and communicate progress."),
    val requirements: List<String> = listOf("Evidence of relevant coursework or a personal project.", "Clear communication and willingness to learn."),
    val eligibility: List<String> = listOf("Applicants based in Kenya.", "Students or recent graduates; no previous paid experience required."),
    val arrangement: String = "Internship · 3 months"
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
        val gaps = target?.let { state.gaps(it) }.orEmpty()
        return when {
            question.contains("cv", true) || question.contains("experience", true) -> "Start with education, projects and the skills you can demonstrate. For each project, describe the problem, your contribution and the result. Paid experience is optional. You can build your CV from the You page."
            question.contains("score", true) || question.contains("match", true) || question.contains("why", true) -> if (target == null || state.score(target) == null) "Add your skills in You to see a comparison with each role’s requirements." else "${target.title} has a ${state.score(target)}% skills match: ${target.skills.size - gaps.size} of ${target.skills.size} required skills are in your profile. ${if (gaps.isEmpty()) "Review the eligibility requirements before preparing your application." else "Skills to develop: ${gaps.joinToString()}."} The percentage describes skills coverage, not your chance of being hired."
            question.contains("eligib", true) -> target?.eligibility?.joinToString("\n\n") ?: "Open a role to check its location, study level and availability requirements. Skills fit and eligibility are separate."
            question.contains("learn", true) || question.contains("next", true) || question.contains("week", true) || question.contains("gap", true) -> if (gaps.isEmpty()) "Choose a target role, review its requirements and prepare a project example for your CV. Your growth path contains practical activities for missing skills." else "For ${target?.title}, begin with ${gaps.first()}. ${LearningLibrary.firstOrNull { it.skill == gaps.first() }?.brief.orEmpty()} Open Growth to save evidence and track your progress."
            else -> "I can help explain a skills match, identify a next learning step, review eligibility or help you structure your CV. Which would you like to explore?"
        }
    }
}
class AppState(context: Context, val repository: OpportunitiesRepository = DemoOpportunitiesRepository(), private val scorer: MatchScorer = SkillCoverageScorer(), val coach: CoachRepository = LocalCoachRepository()) {
    val roles = repository.roles()
    private val handler = android.os.Handler(android.os.Looper.getMainLooper())
    private val persistDraft = Runnable { persistProfile() }
    private val prefs = context.getSharedPreferences("upshift", Context.MODE_PRIVATE)
    private val json = runCatching { JSONObject(prefs.getString("profile", "{}")!!) }.getOrDefault(JSONObject())
    var profile by mutableStateOf(StudentProfile(json.optString("name"), json.optString("email"), json.optString("phone"), json.optString("education"), json.optString("skills"), json.optString("summary"), json.optString("projects"), json.optString("experience"), json.optString("location"), json.optString("goal", "Internship"))); private set
    var entered by mutableStateOf(prefs.getBoolean("entered", false)); private set
    var saved by mutableStateOf(prefs.getStringSet("saved", emptySet())!!.toSet()); private set
    var completed by mutableStateOf(prefs.getStringSet("completed", emptySet())!!.toSet()); private set
    var activityDays by mutableStateOf(prefs.getStringSet("activityDays", emptySet())!!.toSet()); private set
    private var evidence by mutableStateOf(prefs.getString("evidence", "{}") ?: "{}")
    var targetId by mutableStateOf(prefs.getString("target", null)); private set
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
        evidence = JSONObject(evidence).apply { put(skill, notes.trim()) }.toString()
        completed = completed + skill
        activityDays = activityDays + LocalDate.now(ZoneId.of("Africa/Nairobi")).toString()
        prefs.edit().putString("evidence", evidence).putStringSet("completed", completed).putStringSet("activityDays", activityDays).apply()
    }
    fun undoStep(skill: String) { completed = completed - skill; prefs.edit().putStringSet("completed", completed).apply() }
    fun streak() = learningStreak(activityDays.mapNotNull { runCatching { LocalDate.parse(it) }.getOrNull() }.toSet(), LocalDate.now(ZoneId.of("Africa/Nairobi")))
    fun xp() = completed.size * 25
    fun enter() { entered = true; prefs.edit().putBoolean("entered", true).apply() }
    fun leave() { entered = false; prefs.edit().putBoolean("entered", false).apply() }
    fun target(role: Role) { targetId = role.id; if (role.id !in saved) toggleSaved(role.id); prefs.edit().putString("target", targetId).apply() }
    fun clearTarget() { targetId = null; prefs.edit().remove("target").apply() }
    fun update(p: StudentProfile) { profile = p; handler.removeCallbacks(persistDraft); handler.postDelayed(persistDraft, 500) }
    fun flushProfile() { handler.removeCallbacks(persistDraft); persistProfile() }
    private fun persistProfile() {
        val p = profile
        val j = JSONObject().apply { put("name",p.name); put("email",p.email); put("phone",p.phone); put("education",p.education); put("skills",p.skills); put("summary",p.summary); put("projects",p.projects); put("experience",p.experience); put("location",p.location); put("goal",p.goal) }
        prefs.edit().putString("profile",j.toString()).apply()
    }
    fun toggleSaved(id: String) { saved = if (id in saved) saved - id else saved + id; prefs.edit().putStringSet("saved",saved).apply() }
}
