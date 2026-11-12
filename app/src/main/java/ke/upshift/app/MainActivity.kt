package ke.upshift.app

import android.os.Bundle
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

class MainActivity : FragmentActivity() {
    lateinit var state: AppState
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        state = AppState(applicationContext)
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
    androidx.activity.compose.BackHandler(enabled = state.entered && (coach || practice != null || detail != null || page.isNotEmpty() || tab != "Matches")) {
        when { coach -> coach = false; practice != null -> practice = null; preview -> preview = false; page.isNotEmpty() -> page = ""; detail != null -> detail = null; else -> tab = "Matches" }
    }
    UpshiftTheme {
        Box(Modifier.fillMaxSize()) {
            if (!state.entered) Surface(color=Paper,modifier=Modifier.fillMaxSize()) { EntryFlow(state) }
            else Scaffold(
                topBar = {
                    Surface(color=Paper) {
                        Row(Modifier.fillMaxWidth().statusBarsPadding().padding(horizontal=20.dp,vertical=6.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
                            BrandWordmark()
                            Box {
                                IconButton(onClick={menu=true}) { Icon(painterResource(R.drawable.ic_menu),contentDescription="Open menu",tint=BrandDeep) }
                                DropdownMenu(expanded=menu,onDismissRequest={menu=false}) {
                                    DropdownMenuItem(text={Text("Saved roles")},onClick={page="saved";detail=null;menu=false})
                                    DropdownMenuItem(text={Text("Edit profile")},onClick={page="edit";detail=null;menu=false})
                                    DropdownMenuItem(text={Text("About Upshift")},onClick={about=true;menu=false})
                                    DropdownMenuItem(text={Text("Return to welcome")},onClick={menu=false;page="";detail=null;tab="Matches";state.leave()})
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
                Box(Modifier.fillMaxSize().padding(padding).imePadding()) {
                    screenStates.SaveableStateProvider(if(page.isNotEmpty()) "page/$page" else detail?.let { "role/$it" } ?: "tab/$tab") {
                    when {
                        page=="cv" -> CvScreen(state,preview,{preview=it},{page=""})
                        page=="edit" -> EditProfileScreen(state){page=""}
                        page=="saved" -> SavedRolesScreen(state,{page=""},{detail=it;page=""})
                        role!=null -> RoleScreen(state,role,{detail=null},{state.target(role);detail=null;tab="Growth"},{page="cv"},{coach=true})
                        tab=="Growth" -> GrowthScreen(state,{detail=it},{practice=it})
                        tab=="You" -> YouScreen(state,{page="edit"},{page="cv"},{tab="Growth"},{page="saved"})
                        else -> MatchesScreen(state,{detail=it},{page="edit"})
                    }
                    }
                }
            }
        }
        if(coach && state.entered) CoachSheet(state,role){coach=false}
        practice?.let { skill -> LearningLibrary.find { it.skill==skill }?.let { step -> PracticeSheet(state,step){practice=null} } }
        if(about) AlertDialog(onDismissRequest={about=false},title={Text("Your career copilot")},text={Text("Discover opportunities, understand your skill gaps and take one practical step at a time. Your profile and learning drafts stay on this device until you connect an account.")},confirmButton={TextButton(onClick={about=false}){Text("Got it")}})
    }
}
