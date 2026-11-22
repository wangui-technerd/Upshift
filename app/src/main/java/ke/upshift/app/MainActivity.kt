package ke.upshift.app

import android.os.Bundle
import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModelProvider
import android.view.*
import androidx.fragment.app.*
import androidx.compose.ui.platform.*
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.ui.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

class UpShiftViewModel(application: Application) : AndroidViewModel(application) {
    val state = AppState(application)
    override fun onCleared() { state.close() }
}
class MainActivity : FragmentActivity() {
    lateinit var state: AppState
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        state = ViewModelProvider(this)[UpShiftViewModel::class.java].state
        val host = FragmentContainerView(this).apply { id = R.id.main_fragment_host }
        setContentView(host)
        if (savedInstanceState == null) supportFragmentManager.beginTransaction().replace(R.id.main_fragment_host, AppFragment()).commit()
    }
    override fun onStop() { state.flushProfile(); super.onStop() }
}
class AppFragment : Fragment() {
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val host = inflater.inflate(R.layout.fragment_host, container, false) as ComposeView
        host.setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
        host.setContent { Upshift((requireActivity() as MainActivity).state) }
        return host
    }
}
@OptIn(ExperimentalMaterial3Api::class)
@Composable fun Upshift(state: AppState) {
    val workspaceContext=LocalContext.current
    val workspacePrefs=remember { workspaceContext.getSharedPreferences("upshift-workspace",android.content.Context.MODE_PRIVATE) }
    var recruiterMode by rememberSaveable { mutableStateOf(workspacePrefs.getString("last","student")=="recruiter") }
    val workspaceScope=rememberCoroutineScope()
    fun openRecruiter() { recruiterMode=true;workspacePrefs.edit().putString("last","recruiter").apply() }
    var tab by rememberSaveable { mutableStateOf("Matches") }
    var detail by rememberSaveable { mutableStateOf<String?>(null) }
    var page by rememberSaveable { mutableStateOf("") }
    var preview by rememberSaveable { mutableStateOf(false) }
    var about by remember { mutableStateOf(false) }
    var menu by remember { mutableStateOf(false) }
    var coach by rememberSaveable { mutableStateOf(false) }
    var practice by rememberSaveable { mutableStateOf<String?>(null) }
    val role = state.roles.find { it.id == detail }
    val screenStates = rememberSaveableStateHolder()
    val returnToSignIn: () -> Unit = {
        screenStates.removeState("page/feedback")
        page = ""
        detail = null
        tab = "Matches"
        state.leave()
    }
    androidx.activity.compose.BackHandler(enabled = state.entered && (coach || practice != null || detail != null || page.isNotEmpty() || tab != "Matches")) {
        when { coach -> coach = false; practice != null -> practice = null; preview -> preview = false; page == "edit-recommendations" -> page = "recommendations"; page.isNotEmpty() -> page = ""; detail != null -> detail = null; else -> tab = "Matches" }
    }
    UpshiftTheme {
        Box(Modifier.fillMaxSize()) {
            if(recruiterMode) RecruiterWorkspace(state) { workspaceScope.launch { if(state.backend.uid!=null)state.connectAccount();recruiterMode=false;workspacePrefs.edit().putString("last","student").apply() } }
            else if (state.restoring) Surface(color=Paper,modifier=Modifier.fillMaxSize()) {
                Column(Modifier.fillMaxSize(),verticalArrangement=Arrangement.Center,horizontalAlignment=Alignment.CenterHorizontally) {
                    CircularProgressIndicator(); Text("Loading your account")
                }
            } else if (!state.entered) Surface(color=Paper,modifier=Modifier.fillMaxSize()) { EntryFlow(state,recruiter={openRecruiter()}) }
            else Scaffold(
                topBar = {
                    Surface(color=Paper) {
                        Row(Modifier.fillMaxWidth().statusBarsPadding().padding(horizontal=20.dp,vertical=6.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
                            BrandWordmark()
                            Box {
                                IconButton(onClick={menu=true}) { Icon(painterResource(R.drawable.ic_menu),contentDescription="Open menu",tint=BrandDeep) }
                                DropdownMenu(expanded=menu,onDismissRequest={menu=false}) {
                                    DropdownMenuItem(text={Text("Company workspace")},onClick={menu=false;openRecruiter()})
                                    DropdownMenuItem(text={Text("Saved roles")},onClick={page="saved";detail=null;menu=false})
                                    DropdownMenuItem(text={Text("Edit profile")},onClick={page="edit";detail=null;menu=false})
                                    DropdownMenuItem(text={Text("Feedback")},onClick={page="feedback";detail=null;menu=false})
                                    DropdownMenuItem(text={Text("About Upshift")},onClick={about=true;menu=false})
                                    DropdownMenuItem(text={Text(if(state.userId != null) "Sign out" else "Return to welcome")},onClick={menu=false;coach=false;practice=null;preview=false;returnToSignIn()})
                                }
                            }
                        }
                    }
                },
                bottomBar={
                    NavigationBar(containerColor=Color.White) {
                        listOf("Matches","Growth","You").forEachIndexed { i,label -> NavigationBarItem(selected=tab==label,onClick={tab=label;detail=null;page="";preview=false},icon={Icon(painterResource(listOf(R.drawable.ic_matches,R.drawable.ic_growth,R.drawable.ic_person)[i]),contentDescription=null)},label={Text(label)},colors=NavigationBarItemDefaults.colors(selectedIconColor=BrandDeep,selectedTextColor=BrandDeep,indicatorColor=BrandSoft)) }
                    }
                },
                floatingActionButton={ if(page.isEmpty()) CoachLauncher { coach=true } }
            ) { padding ->
                Column(Modifier.fillMaxSize().padding(padding).imePadding()) {
                    if (state.userId != null) {
                        Text(if(state.syncMessage.isNotBlank()) state.syncMessage else if(state.saving) "Saving to your account..." else "Signed in as ${state.profile.email}", modifier=Modifier.padding(horizontal=20.dp,vertical=6.dp),style=MaterialTheme.typography.bodySmall)
                        if(state.syncMessage.isNotBlank()) TextButton(onClick={state.retrySync()}){Text("Retry cloud save")}
                    } else Text("Guest preview - sample opportunities",modifier=Modifier.padding(horizontal=20.dp,vertical=6.dp),style=MaterialTheme.typography.bodySmall)
                    Box(Modifier.weight(1f)) {
                    screenStates.SaveableStateProvider(if(page.isNotEmpty()) "page/$page" else detail?.let { "role/$it" } ?: "tab/$tab") {
                    when {
                        page=="recommendations" -> key(state.userId) {
                            RecommendationsScreen(state, { page = "edit-recommendations" }, returnToSignIn) { page = "" }
                        }
                        page=="edit-recommendations" -> EditProfileScreen(state) { page = "recommendations" }
                        page=="feedback" -> key(state.userId) {
                            FeedbackScreen(state, returnToSignIn) { page = "" }
                        }
                        page=="cv" -> CvScreen(state,preview,{preview=it},{page=""})
                        page=="edit" -> EditProfileScreen(state){page=""}
                        page=="saved" -> SavedRolesScreen(state,{page=""},{detail=it;page=""})
                        role!=null -> RoleScreen(state,role,{detail=null},{state.target(role);detail=null;tab="Growth"},{page="cv"},{coach=true})
                        tab=="Growth" -> GrowthScreen(state,{detail=it},{practice=it})
                        tab=="You" -> YouScreen(state,{page="edit"},{page="cv"},{tab="Growth"},{page="saved"})
                        else -> MatchesScreen(state,{detail=it},{page="edit"},{page="recommendations"})
                    }
                    }
                    }
                }
            }
        }
        if(coach && state.entered) CoachSheet(state,role){coach=false}
        practice?.let { skill -> LearningLibrary.find { it.skill==skill }?.let { step -> PracticeSheet(state,step){practice=null} } }
        if(about) AlertDialog(onDismissRequest={about=false},title={Text("Your career copilot")},text={Text("Discover opportunities, understand your skill gaps and take one practical step at a time. Guest drafts stay on this device. Signed-in profiles and learning progress are saved to your Firebase account.")},confirmButton={TextButton(onClick={about=false}){Text("Got it")}})
    }
}
