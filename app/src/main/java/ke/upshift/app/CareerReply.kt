package ke.upshift.app

/** Local guidance: no conversational model or hiring predictions. */
internal fun careerReply(question: String, role: Role?, gaps: List<String>, score: Int?, profile: StudentProfile): String {
    val q = question.lowercase().replace(Regex("[^a-z0-9 ]"), " ")
    fun has(vararg words: String) = words.any { Regex("\\b${Regex.escape(it)}\\b").containsMatchIn(q) }
    val title = role?.title ?: "your target role"
    val skill = LearningLibrary.firstOrNull { q.contains(it.skill.lowercase()) }
    return when {
        has("hello", "hi", "hey") -> "Hi ${profile.name.substringBefore(' ').ifBlank { "there" }}! Ask about a role, a missing skill, courses, your CV or applying. I use your saved profile and role requirements."
        has("thank", "thanks") -> "You're welcome. Choose one small next step and save your progress in Growth."
        has("eligible", "eligibility", "qualify", "qualified", "requirements") -> role?.let { "For ${it.title}: ${it.eligibility.joinToString("; ")}. Check the full requirements and deadline on the role page; the employer decides eligibility." } ?: "Open a role first so I can show its eligibility requirements."
        has("cv", "resume", "experience") -> "For $title, include education, demonstrable skills and projects. ${if(profile.projects.isBlank()) "Add a coursework or personal project: describe your contribution and result." else "Use a project from your profile and describe what you built, your contribution and how you checked it."} You → Build your CV lets you preview and save a PDF. Never invent experience."
        has("cost", "free", "afford", "expensive", "certificate", "certification", "coursera", "udemy") -> "Growth links to recognised course providers. Check the provider's current price, certificate fee and financial-aid options before enrolling. Free study access does not always include a free certificate."
        has("apply", "application", "deadline") -> role?.let { "Open ${it.title}, check requirements and availability, then use its application link. Tailor your CV to skills you can demonstrate. ${if(it.deadline.isNotBlank()) "Listed deadline: ${it.deadline}." else "Confirm the closing date on the employer's site."} Upshift does not submit applications for you." } ?: "Open a role to review its requirements and application link."
        has("learn", "learning", "next", "week", "gap", "gaps", "improve", "study") || skill != null -> {
            val step = skill ?: LearningLibrary.firstOrNull { it.skill in gaps }
            if(step != null) "For ${step.skill}: ${step.brief} Find its course in Growth, then save a reflection or project as evidence. ${if(step.skill in gaps) "This is a gap listed for $title." else "Check whether this skill supports your chosen role."}"
            else if(gaps.isNotEmpty()) "For $title, start with ${gaps.first()}. Review the requirement, find introductory learning and practise it in a small project."
            else "No listed skill gaps for $title are available here. Choose a role, check eligibility and strengthen a project example; matching skills does not guarantee a job."
        }
        has("score", "percentage", "percent", "match", "matches", "why", "fit") -> if(role == null || score == null) "Add your skills in You, then open a role to compare its listed skills with your profile." else "$title: $score% listed-skills coverage. ${if(gaps.isEmpty()) "Your profile includes all its listed skills." else "Skills not listed in your profile: ${gaps.joinToString()}."} This circle is skills coverage, not hiring probability. For you uses a separate text-similarity model."
        has("job", "jobs", "internship", "internships", "recommendations") -> "Browse shows role requirements and skills coverage. For you compares your profile with active vacancies; complete your skills, education and projects first. Check employer eligibility before applying."
        else -> "I couldn't identify a career question in that message. I'm a guided helper, not an open-ended AI chat. Try ‘How do I learn SQL?’, ‘Am I eligible?’, ‘Help with my CV’ or ‘Explain my match’."
    }
}
