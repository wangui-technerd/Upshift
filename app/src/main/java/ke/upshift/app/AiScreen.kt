package ke.upshift.app

import android.os.SystemClock
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.Locale

@Composable
internal fun RecommendationsScreen(state: AppState, editProfile: () -> Unit, signIn: () -> Unit, back: () -> Unit) {
    val profile = state.profile
    var filterLocation by rememberSaveable { mutableStateOf(false) }
    var experience by rememberSaveable { mutableStateOf("") }
    var matches by remember(profile) { mutableStateOf<List<VacancyMatch>?>(null) }
    var failure by remember(profile) { mutableStateOf<AiFailure?>(null) }
    var busy by remember { mutableStateOf(false) }
    var slow by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val client = remember(state.backend) { AiClient(state.backend) }
    val retry = rememberAiRetry()
    val months = experience.toIntOrNull()
    val invalidExperience = experience.isNotBlank() && (months == null || months !in 0..1200)
    val ready = hasRecommendationEvidence(profile)

    LaunchedEffect(busy) {
        slow = false
        if (busy) {
            delay(2500)
            slow = true
        }
    }

    AiPage("Job recommendations", "Find active vacancies using the skills and experience in your profile.", back) {
        when {
            state.userId == null -> {
                Text("You're browsing as a guest. Sign in to find recommendations for your student profile.")
                Button(onClick = signIn) { Text("Sign in") }
            }
            !ready -> {
                Text("Add your education, skills, projects or experience before searching.")
                Button(onClick = editProfile) { Text("Complete my profile") }
            }
            else -> {
                if (profile.location.isNotBlank()) {
                    Row {
                        Checkbox(checked = filterLocation, onCheckedChange = { filterLocation = it; matches = null }, enabled = !busy)
                        Text("Only match my profile location (${profile.location})", Modifier.padding(top = 12.dp))
                    }
                }
                OutlinedTextField(
                    value = experience,
                    onValueChange = {
                        if (it.length <= 4 && it.all { char -> char in '0'..'9' }) { experience = it; matches = null }
                    },
                    label = { Text("Experience in months (optional)") },
                    supportingText = { Text(if (invalidExperience) "Enter 0–1200 months." else "Leave blank if you’re unsure.") },
                    isError = invalidExperience,
                    enabled = !busy,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    enabled = !busy && !invalidExperience && retry.seconds == 0L && failure?.problem != AiProblem.SIGN_IN,
                    onClick = {
                        busy = true
                        failure = null
                        matches = null
                        scope.launch {
                            try {
                                matches = client.recommendations(
                                    profile,
                                    profile.location.trim().takeIf { filterLocation && it.isNotEmpty() },
                                    months,
                                )
                            } catch (e: CancellationException) {
                                throw e
                            } catch (e: AiFailure) {
                                retry.update(e)
                                failure = e
                            } finally {
                                busy = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(when {
                        retry.seconds > 0 -> "Retry in ${retry.seconds}s"
                        failure != null -> "Retry recommendations"
                        else -> "Find jobs"
                    })
                }
                if (busy) {
                    LinearProgressIndicator(Modifier.fillMaxWidth())
                    Text(if (slow) "Still looking for vacancies. You can go back and try later." else "Finding suitable vacancies…")
                }
                failure?.let { FailureMessage(it, "recommendations", signIn, editProfile) }
                val result = matches
                if (result != null && result.isEmpty()) {
                    Text("No active vacancies match your profile and filters.")
                    Text("Try removing the location filter, updating your profile, or checking again later.")
                }
                result?.forEach { vacancy -> key(vacancy.id) { RecommendationCard(vacancy) } }
            }
        }
    }
}

@Composable
internal fun FeedbackScreen(state: AppState, signIn: () -> Unit, back: () -> Unit) {
    var draft by rememberSaveable(state.userId) { mutableStateOf("") }
    var sentiment by remember { mutableStateOf<String?>(null) }
    var failure by remember { mutableStateOf<AiFailure?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val client = remember(state.backend) { AiClient(state.backend) }
    val retry = rememberAiRetry()

    AiPage("App feedback", "See the sentiment UpShift detects in your feedback.", back) {
        if (state.userId == null) {
            Text("Sign in to submit feedback for analysis.")
            Button(onClick = signIn) { Text("Sign in") }
        } else {
            OutlinedTextField(
                value = draft,
                onValueChange = {
                    if (it.length <= 10000) { draft = it; sentiment = null; failure = null }
                },
                enabled = !busy,
                label = { Text("Feedback about UpShift") },
                minLines = 3,
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                enabled = draft.isNotBlank() && !busy && retry.seconds == 0L && failure?.problem != AiProblem.SIGN_IN,
                onClick = {
                    busy = true
                    failure = null
                    scope.launch {
                        try {
                            sentiment = client.sentiment(draft.trim())
                        } catch (e: CancellationException) {
                            throw e
                        } catch (e: AiFailure) {
                            retry.update(e)
                            failure = e
                        } finally {
                            busy = false
                        }
                    }
                },
            ) { Text(if (retry.seconds > 0) "Retry in ${retry.seconds}s" else "Analyse feedback") }
            if (busy) { LinearProgressIndicator(Modifier.fillMaxWidth()); Text("Analysing feedback…") }
            sentiment?.let { Text("Feedback sentiment: ${it.replaceFirstChar { char -> char.uppercase() }}") }
            failure?.let { FailureMessage(it, "feedback", signIn) }
        }
    }
}

@Composable
private fun AiPage(title: String, description: String, back: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        TextButton(onClick = back) { Text("Back") }
        Heading(title, description)
        content()
    }
}

@Composable
private fun RecommendationCard(vacancy: VacancyMatch) {
    val uriHandler = LocalUriHandler.current
    var linkError by remember(vacancy.applicationUrl) { mutableStateOf(false) }
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(vacancy.title, style = MaterialTheme.typography.titleLarge)
            Text(listOfNotNull(vacancy.company, vacancy.location).joinToString(" · ").ifBlank { "Company and location unavailable" })
            Text(vacancy.deadline?.let { "Application deadline: $it" } ?: "Application deadline: Unknown")
            vacancy.similarity?.let { Text("Text similarity: ${String.format(Locale.ROOT, "%.3f", it)}") }
            vacancy.description?.let { Text(it) }
            SkillList("Skills shown in your profile", vacancy.matchedSkills, "No skill evidence identified in the profile.")
            SkillList("Required skills your profile doesn’t mention", vacancy.missingSkills, "No required skill gaps identified.")
            if (vacancy.requirements.isNotEmpty()) SkillList("Vacancy requirements", vacancy.requirements)
            if (vacancy.eligibility.isNotEmpty()) SkillList("Check eligibility with the employer", vacancy.eligibility)
            val url = vacancy.applicationUrl
            if (url == null) Text("Application link unavailable.")
            else Button(onClick = {
                linkError = try { uriHandler.openUri(url); false } catch (_: IllegalArgumentException) { true }
            }) { Text("Open application") }
            if (linkError) Text("Couldn’t open the application link. Try again or check that a browser is installed.")
        }
    }
}

@Composable
private fun SkillList(title: String, values: List<String>, empty: String = "") {
    Text(title, style = MaterialTheme.typography.titleSmall)
    Text(if (values.isEmpty()) empty else values.joinToString("\n") { "• $it" })
}

@Composable
private fun FailureMessage(failure: AiFailure, feature: String, signIn: () -> Unit, edit: (() -> Unit)? = null) {
    Text(when (failure.problem) {
        AiProblem.CONFIGURATION -> "This feature needs a build connected to the UpShift backend."
        AiProblem.SIGN_IN -> "Your sign-in session ended. Sign in again to continue."
        AiProblem.TOKEN_REJECTED -> "The backend couldn't verify your sign-in. Retry or sign in again. If this keeps happening, ask the team to check that the app and backend use the same Firebase project."
        AiProblem.ACCESS_DENIED -> "This account doesn't have access to $feature. Contact the UpShift team."
        AiProblem.INVALID_INPUT -> if (edit != null) "Check your profile and filters, then try again." else "Check your feedback and try again."
        AiProblem.RATE_LIMIT -> "Too many requests. Wait for the retry button to become available."
        AiProblem.TIMEOUT -> "The server took too long. Try again."
        AiProblem.NETWORK -> "Couldn’t reach the backend. Check your connection and try again."
        AiProblem.SERVICE -> "The $feature service is temporarily unavailable. Try again later."
        AiProblem.RESPONSE -> "The server sent an unexpected response. Try again."
    }, color = MaterialTheme.colorScheme.error)
    if (failure.problem in setOf(AiProblem.SIGN_IN, AiProblem.TOKEN_REJECTED)) {
        TextButton(onClick = signIn) { Text("Sign in again") }
    }
    if (failure.problem == AiProblem.INVALID_INPUT && edit != null) TextButton(onClick = edit) { Text("Edit profile") }
}

private class AiRetry {
    var deadline by mutableLongStateOf(0)
        private set
    var seconds by mutableLongStateOf(0)
        private set

    fun update(error: AiFailure) {
        if (error.problem == AiProblem.RATE_LIMIT) {
            seconds = error.retryAfterSeconds.coerceIn(0, 86400)
            deadline = SystemClock.elapsedRealtime() + seconds * 1000
        }
    }

    fun tick() {
        seconds = ((deadline - SystemClock.elapsedRealtime() + 999) / 1000).coerceAtLeast(0)
    }
}

@Composable
private fun rememberAiRetry(): AiRetry {
    val retry = remember { AiRetry() }
    LaunchedEffect(retry.deadline) {
        retry.tick()
        while (retry.seconds > 0) {
            delay(1000)
            retry.tick()
        }
    }
    return retry
}
