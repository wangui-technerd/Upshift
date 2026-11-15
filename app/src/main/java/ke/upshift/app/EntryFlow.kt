package ke.upshift.app

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.*
import androidx.compose.ui.unit.dp

@Composable fun EntryFlow(state: AppState, recruiter: () -> Unit = {}) {
    var screen by rememberSaveable { mutableStateOf(if (state.userId != null && state.cloudReady) "onboarding" else "welcome") }
    var intro by rememberSaveable { mutableIntStateOf(0) }
    var onboarding by rememberSaveable { mutableIntStateOf(0) }
    LaunchedEffect(state.cloudReady) { if(state.cloudReady && state.userId != null) screen = "onboarding" }
    androidx.activity.compose.BackHandler(enabled = screen != "welcome") {
        when { screen == "onboarding" && onboarding > 0 -> onboarding--; screen == "intro" && intro > 0 -> intro--; else -> screen = "welcome" }
    }
    if (state.userId != null && !state.cloudReady && !state.connecting) {
        Column(Modifier.fillMaxSize().safeDrawingPadding().padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            BrandWordmark()
            TextButton(onClick = recruiter) { Text("I'm hiring · Company workspace") }
            Text("Could not load your account")
            Text(state.syncMessage.ifBlank { "Check your connection and try again." })
            Button(onClick = { state.retrySync() }) { Text("Retry") }
            TextButton(onClick = { state.leave(); screen = "welcome" }) { Text("Sign out") }
        }
        return
    }
    when (screen) {
        "welcome" -> Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
            Spacer(Modifier.height(28.dp))
            BrandWordmark()
            TextButton(onClick=recruiter) { Text("I'm hiring · Company workspace") }
            Surface(color = BrandSoft, shape = MaterialTheme.shapes.large, modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    BrandMark(60.dp)
                    Text("Find roles that actually fit you", style = MaterialTheme.typography.headlineLarge, color = BrandDeep)
                    Text("Understand your skills. Find your next opportunity. Grow one step at a time.", color = BrandDeep)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { StatusPill("Your skills", Mint, Teal); StatusPill("Your next step", CoralSoft, OrangeInk) }
                }
            }
            InfoCard("A little progress goes a long way", "Discover suitable roles, build a practical growth path and create your CV.", CoralSoft, OrangeInk)
            Button(onClick = { screen = "intro" }, modifier = Modifier.fillMaxWidth()) { Text("Get started") }
            OutlinedButton(onClick = { screen = "login" }, modifier = Modifier.fillMaxWidth()) { Text("Log in") }
            TextButton(onClick = { if (state.profile.skills.isNotBlank()) state.enter() else screen = "onboarding" }, modifier = Modifier.fillMaxWidth()) { Text("Continue on this device") }
        }
        "intro" -> {
            val titles=listOf("Know where you stand","Gaps, not verdicts","One step at a time")
            val descriptions=listOf("Compare your skills with a role’s requirements. Add your profile next to see your own matches.","Keep the skills you have in view, then choose a skill to develop. You don’t have to learn everything at once.","Choose a target role, explore a certificate programme and keep a record of your learning.")
            Column(Modifier.fillMaxSize().safeDrawingPadding()) {
                Row(Modifier.fillMaxWidth().padding(horizontal=24.dp,vertical=8.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
                    BrandWordmark();TextButton(onClick={screen="signup"}){Text("Skip")}
                }
                BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
                    val viewport=maxHeight
                    key(intro) {
                        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState())) {
                            Column(Modifier.fillMaxWidth().heightIn(min=viewport).padding(24.dp),verticalArrangement=Arrangement.spacedBy(24.dp,Alignment.CenterVertically)) {
                                Surface(color=listOf(BrandSoft,CoralSoft,Mint)[intro],shape=MaterialTheme.shapes.large) {
                                    Column(Modifier.fillMaxWidth().heightIn(min=200.dp).padding(24.dp),verticalArrangement=Arrangement.spacedBy(14.dp,Alignment.CenterVertically)) {
                                        StatusPill("EXAMPLE",Color.White,Muted)
                                        when(intro) {
                                            0 -> {
                                                Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(16.dp)) {
                                                    MatchRing(75,80.dp)
                                                    Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                                                        Text("Frontend intern",style=MaterialTheme.typography.titleLarge,color=BrandDeep)
                                                        Text("3 of 4 required skills",style=MaterialTheme.typography.bodyMedium,color=BrandDeep)
                                                    }
                                                }
                                                Text("A skills comparison, not a hiring prediction.",style=MaterialTheme.typography.bodySmall,color=Muted)
                                            }
                                            1 -> {
                                                Text("Already have",style=MaterialTheme.typography.titleMedium,color=Teal)
                                                SkillChips(listOf("HTML","CSS","Git"))
                                                Text("One skill to develop",style=MaterialTheme.typography.titleMedium,color=OrangeInk)
                                                SkillChips(listOf("JavaScript"),true)
                                            }
                                            else -> {
                                                Text("01  Choose your role",style=MaterialTheme.typography.titleMedium,color=Teal)
                                                Text("02  Learn with Google or Meta",style=MaterialTheme.typography.titleMedium,color=Teal)
                                                Text("03  Track progress & build your CV",style=MaterialTheme.typography.titleMedium,color=Teal)
                                            }
                                        }
                                    }
                                }
                                Heading(titles[intro],descriptions[intro])
                            }
                        }
                    }
                }
                Surface(color=Paper) {
                    Column(Modifier.fillMaxWidth().padding(horizontal=24.dp,vertical=16.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                        Text("${intro+1} / 3",color=BrandDeep,style=MaterialTheme.typography.labelMedium)
                        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(12.dp),verticalAlignment=Alignment.CenterVertically) {
                            if(intro>0)OutlinedButton(onClick={intro--}){Text("Back")}
                            Button(onClick={if(intro<2)intro++ else screen="signup"},modifier=Modifier.weight(1f)){Text(if(intro<2)"Next" else "Create my profile")}
                        }
                    }
                }
            }
        }
        "signup", "login", "reset" -> AccountScreen(screen, { screen = it }, { name, email ->
            if (state.userId != null || state.backend.uid != null) state.leave()
            state.update(state.profile.copy(name = name.ifBlank { state.profile.name }, email = email.ifBlank { state.profile.email }))
            screen = "onboarding"
        }, state.backend, { name ->
            val connected = state.connectAccount(name)
            if (connected) screen = "onboarding"
            connected
        })
        else -> Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).imePadding().padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
            BrandWordmark()
            StatusPill("YOUR PROFILE · ${onboarding + 1} OF 3", BrandSoft, BrandDeep)
            when (onboarding) {
                0 -> { Heading("Let’s start with you", "Your profile is saved as you go.")
                    Field("Full name",state.profile.name) { state.update(state.profile.copy(name=it)) }
                    Field("Education / programme",state.profile.education) { state.update(state.profile.copy(education=it)) }
                    Field("Location",state.profile.location) { state.update(state.profile.copy(location=it)) }
                }
                1 -> { Heading("What can you do today?", "Choose skills you can demonstrate. You can change these later.")
                    SkillSelector(state)
                }
                else -> { Heading("What are you aiming for?", "We’ll keep your goal in view as you explore.")
                    listOf("Internship", "Industrial attachment", "Entry-level role").forEach { goal ->
                        FilterChip(selected = state.profile.goal == goal, onClick = { state.update(state.profile.copy(goal = goal)) }, label = { Text(goal) }, modifier = Modifier.fillMaxWidth())
                    }
                    InfoCard("Your path belongs to you", "Start with the skills you have. Add projects and experience whenever you’re ready.", Mint, Teal)
                }
            }
            Button(onClick = { if (onboarding < 2) onboarding++ else state.enter() }, enabled = onboarding != 0 || state.profile.name.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text(if (onboarding == 2) "See my matches" else "Continue") }
            TextButton(onClick = { if (onboarding > 0) onboarding-- else screen = "welcome" }) { Text("← Back") }
        }
    }
}
@Composable fun AccountScreen(mode: String, navigate: (String) -> Unit, local: (String, String) -> Unit, gateway: AccountGateway, authenticated: suspend (String) -> Boolean, recruiter: Boolean = false) {
    var name by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var reveal by remember { mutableStateOf(false) }
    var feedback by remember { mutableStateOf("") }
    var request by remember { mutableStateOf(false) }
    var googleRequest by remember { mutableStateOf(false) }
    val context = LocalContext.current
    LaunchedEffect(mode) { feedback = ""; password = ""; reveal = false }
    LaunchedEffect(request) {
        if (request) {
            try {
                when (val result = if (googleRequest) gateway.signInWithGoogle(context) else when (mode) { "signup" -> gateway.signUp(name,email,password); "reset" -> gateway.resetPassword(email); else -> gateway.signIn(email,password) }) {
                    AccountResult.Success -> {
                        password = ""
                        if (!authenticated(if (mode == "signup" && !googleRequest) name else "")) feedback = "Signed in, but your data could not load. Check your connection and retry."
                    }
                    AccountResult.Cancelled -> feedback = ""
                    AccountResult.ResetSent -> feedback = "If an account exists for this email, a password reset link has been sent. Check your inbox."
                    is AccountResult.Error -> feedback = result.message
                }
            } finally { request = false; googleRequest = false }
        }
    }
    androidx.activity.compose.BackHandler(enabled = request) { }
    Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).imePadding().padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        TextButton(enabled = !request, onClick = { navigate("welcome") }) { Text("← Back") }
        BrandWordmark()
        if(recruiter) StatusPill("COMPANY WORKSPACE",BrandSoft,BrandDeep)
        Heading(when(mode) { "signup" -> if(recruiter) "Open a door to talent" else "Your next chapter starts here"; "reset" -> "Reset your password"; else -> "Welcome back" }, if(mode == "reset") "Enter the email associated with your account." else if(recruiter) "Register your company and create meaningful opportunities. Company approval is required before submission." else if(mode == "signup") "Create an account to keep your progress together." else "Pick up where you left off.")
        if (mode == "signup") Field("Full name",name) { name=it }
        OutlinedTextField(email,{ email=it; feedback="" }, label={Text("Email address")},singleLine=true,keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Email),modifier=Modifier.fillMaxWidth())
        if (mode != "reset") OutlinedTextField(password,{password=it; feedback=""},label={Text("Password")},singleLine=true,visualTransformation=if(reveal) VisualTransformation.None else PasswordVisualTransformation(),trailingIcon={TextButton(onClick={reveal=!reveal}){Text(if(reveal) "Hide" else "Show")}},keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Password),modifier=Modifier.fillMaxWidth())
        if(mode=="signup") Text("Use at least 8 characters. Firebase securely manages your password.",style=MaterialTheme.typography.bodySmall,color=Muted)
        if(feedback.isNotBlank()) InfoCard("Before you continue",feedback,CoralSoft,OrangeInk)
        Button(enabled=!request,onClick={
            feedback=when {
                mode=="signup" && name.isBlank() -> "Enter your name."
                !android.util.Patterns.EMAIL_ADDRESS.matcher(email.trim()).matches() -> "Enter a valid email address."
                mode!="reset" && password.isBlank() -> "Enter your password."
                mode=="signup" && password.length<8 -> "Choose a password with at least 8 characters."
                else -> ""
            }
            if(feedback.isEmpty()) { googleRequest=false; request=true }
        },modifier=Modifier.fillMaxWidth()) { Text(if(request) "Please wait…" else when(mode){"signup"->"Create account";"reset"->"Send reset link";else->"Log in"}) }
        if(mode != "reset") {
            Text("or",style=MaterialTheme.typography.bodySmall,color=Muted)
            OutlinedButton(enabled=!request,onClick={feedback="";password="";googleRequest=true;request=true},modifier=Modifier.fillMaxWidth()) {
                Text(if(request && googleRequest) "Connecting to Google..." else "Continue with Google")
            }
        }
        if(mode=="login") TextButton(enabled=!request,onClick={navigate("reset")}){Text("Forgot password?")}
        TextButton(enabled=!request,onClick={navigate(if(mode=="signup") "login" else "signup")}){Text(if(mode=="signup") "Already have an account? Log in" else "New here? Create an account")}
        if(!recruiter) {
            HorizontalDivider(color=Line)
            TextButton(enabled=!request,onClick={local(name,email)},modifier=Modifier.fillMaxWidth()){Text("Continue on this device")}
        }
    }
}
