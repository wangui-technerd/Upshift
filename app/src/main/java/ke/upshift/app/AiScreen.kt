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
import java.util.UUID

@Composable
internal fun RecommendationsScreen(state: AppState, editProfile: () -> Unit, signIn: () -> Unit, back: () -> Unit) {
    val profile = state.profile
    var filterLocation by rememberSaveable { mutableStateOf(false) }
    var experience by rememberSaveable { mutableStateOf("") }
    var matches by remember(profile) { state.recommendationsFor(profile) }
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

    AiPage("For you", "Find active vacancies using the skills and experience in your profile.", back) {
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
    var submissionId by rememberSaveable(state.userId) { mutableStateOf(UUID.randomUUID().toString()) }
    var sent by rememberSaveable(state.userId) { mutableStateOf(false) }
    val snackbar = remember { SnackbarHostState() }
    var failure by remember { mutableStateOf<AiFailure?>(null) }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val client = remember(state.backend) { AiClient(state.backend) }
    val retry = rememberAiRetry()

    LaunchedEffect(sent) { if(sent) snackbar.showSnackbar("Feedback sent. Thank you!") }
    Box(Modifier.fillMaxSize()) {
    AiPage("App feedback", "Tell us what worked and what you’d improve. Please leave out personal details.", back) {
        if (state.userId == null) {
            Text("Sign in to send feedback.")
            Button(onClick = signIn) { Text("Sign in") }
        } else {
            OutlinedTextField(
                value = draft,
                onValueChange = {
                    if (it.length <= 10000) { draft = it; sent = false; submissionId = UUID.randomUUID().toString(); failure = null }
                },
                enabled = !busy,
                label = { Text("Feedback about UpShift") },
                minLines = 3,
                maxLines = 6,
                modifier = Modifier.fillMaxWidth(),
            )
            Button(
                enabled = draft.isNotBlank() && !sent && !busy && retry.seconds == 0L && failure?.problem != AiProblem.SIGN_IN,
                onClick = {
                    busy = true
                    failure = null
                    scope.launch {
                        try {
                            client.sendFeedback(draft.trim(), submissionId)
                            sent = true
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
            ) { Text(if (retry.seconds > 0) "Retry in ${retry.seconds}s" else if(busy) "Sending…" else if(sent) "Sent" else "Send feedback") }
            if (busy) { LinearProgressIndicator(Modifier.fillMaxWidth()); Text("Sending feedback…") }
            if(sent) Text("Thank you. Your feedback has been received.",color=Teal)
            failure?.let { FailureMessage(it, "feedback", signIn) }
        }
    }
    SnackbarHost(snackbar,Modifier.align(androidx.compose.ui.Alignment.BottomCenter).imePadding().padding(16.dp))
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
    var explain by rememberSaveable(vacancy.id) { mutableStateOf(false) }
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(vacancy.title, style = MaterialTheme.typography.titleLarge)
            Text(listOfNotNull(vacancy.company, vacancy.location).joinToString(" · ").ifBlank { "Company and location unavailable" })
            Text(vacancy.deadline?.let { "Application deadline: $it" } ?: "Application deadline: Unknown")

            vacancy.description?.let { Text(it,maxLines=if(explain) Int.MAX_VALUE else 3,overflow=androidx.compose.ui.text.style.TextOverflow.Ellipsis) }
            TextButton(onClick={explain=!explain}) { Text(if(explain) "Hide explanation ↑" else "Why this job? ↓") }
            if(explain) {
                Text("We compared your profile with what this job asks for. Jobs closer to your profile appear first.")
                SkillList("Skills that match",vacancy.matchedSkills,"No matching skills were found in your profile.")
                SkillList("Check these skills",vacancy.missingSkills,"No missing required skills were found.")
                Text("If you have a skill listed here, add it to your profile. A match does not guarantee a job.",style=MaterialTheme.typography.bodySmall)
                if (vacancy.requirements.isNotEmpty()) SkillList("What the job asks for", vacancy.requirements)
                if (vacancy.eligibility.isNotEmpty()) SkillList("Who can apply", vacancy.eligibility)
            }
            val url = vacancy.applicationUrl
            if (url == null) Text("Application link unavailable.")
            else Button(onClick = {
                linkError = try { uriHandler.openUri(url); false } catch (_: IllegalArgumentException) { true }
            }) { Text("Open application") }
            if (linkError) AlertDialog(onDismissRequest={linkError=false},title={Text("Couldn’t open link")},text={Text("Check that a browser is installed, then try again.")},confirmButton={TextButton(onClick={linkError=false}){Text("OK")}})
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
    var visible by remember(failure) { mutableStateOf(true) }
    if(visible) AlertDialog(
        onDismissRequest={visible=false},
        title={Text("Let’s try again")},
        text={Text(when(failure.problem) {
            AiProblem.SIGN_IN, AiProblem.TOKEN_REJECTED -> "Please sign in again to continue. Your text is still here."
            AiProblem.INVALID_INPUT -> "Check your details and try again."
            AiProblem.RATE_LIMIT -> "Please wait a moment before trying again."
            AiProblem.NETWORK -> "Check your internet connection and try again. Your text is still here."
            AiProblem.TIMEOUT -> "This is taking longer than usual. Please try again."
            AiProblem.ACCESS_DENIED -> "Your account can’t use this feature. Contact the Upshift team."
            else -> "We couldn’t complete that just now. Please try again shortly."
        })},
        confirmButton={TextButton(onClick={visible=false; if(failure.problem in setOf(AiProblem.SIGN_IN,AiProblem.TOKEN_REJECTED))signIn()}) { Text(if(failure.problem in setOf(AiProblem.SIGN_IN,AiProblem.TOKEN_REJECTED))"Sign in" else "OK") }},
        dismissButton={if(failure.problem==AiProblem.INVALID_INPUT && edit!=null)TextButton(onClick={visible=false;edit()}){Text("Edit profile")}}
    )
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
