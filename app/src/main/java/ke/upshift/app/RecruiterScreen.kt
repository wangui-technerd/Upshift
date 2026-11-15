package ke.upshift.app

import android.content.Context
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

@Composable fun RecruiterWorkspace(state:AppState,student:()->Unit) {
    var uid by remember { mutableStateOf(state.backend.uid) }
    var authPage by rememberSaveable { mutableStateOf("login") }
    if(uid==null) {
        if(authPage=="welcome") {
            Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp),verticalArrangement=Arrangement.spacedBy(20.dp)) {
                BrandWordmark();StatusPill("FOR COMPANIES",BrandSoft,BrandDeep)
                Heading("Make room for potential","Create meaningful opportunities for the next generation.")
                InfoCard("One company. More possibilities.","Register your company, prepare a vacancy and follow its review — right here in UpShift.")
                Button(onClick={authPage="signup"},modifier=Modifier.fillMaxWidth()){Text("Create a recruiter account")}
                OutlinedButton(onClick={authPage="login"},modifier=Modifier.fillMaxWidth()){Text("Sign in")}
                TextButton(onClick=student){Text("I'm looking for opportunities")}
            }
        } else AccountScreen(authPage,{authPage=it},{_,_->},state.backend,{uid=state.backend.uid;uid!=null},recruiter=true)
        return
    }
    key(uid) { RecruiterSignedIn(state,uid!!,student,{state.leave();uid=null;authPage="welcome"}) }
}

@Composable private fun RecruiterSignedIn(state:AppState,uid:String,student:()->Unit,signOut:()->Unit) {
    val client=remember { RecruiterClient(state.backend) };val scope=rememberCoroutineScope()
    val context=LocalContext.current
    var companies by remember { mutableStateOf(emptyList<RecruiterCompany>()) }
    var vacancies by remember { mutableStateOf(emptyList<RecruiterVacancy>()) }
    var selected by rememberSaveable { mutableStateOf("") }
    var tab by rememberSaveable { mutableStateOf("Overview") }
    var editor by rememberSaveable { mutableStateOf<String?>(null) }
    var newCompany by rememberSaveable { mutableStateOf(false) }
    var menu by remember { mutableStateOf(false) };var chooseCompany by remember { mutableStateOf(false) }
    var reload by remember { mutableIntStateOf(0) };var loading by remember { mutableStateOf(true) }
    var busy by remember { mutableStateOf(false) };var error by remember { mutableStateOf("") }
    var message by remember { mutableStateOf("") };var withdrawal by remember { mutableStateOf<RecruiterVacancy?>(null) }
    val company=companies.find { it.id==selected };val rows=vacancies.filter { it.companyId==selected }
    LaunchedEffect(uid,reload) {
        loading=true;error=""
        try { companies=client.companies();vacancies=client.vacancies();if(companies.none { it.id==selected })selected=companies.firstOrNull()?.id.orEmpty() }
        catch(e:CancellationException){throw e}
        catch(e:Exception){error=e.message ?: "Could not load your company workspace."}
        finally { loading=false }
    }
    fun perform(block:suspend ()->Unit) { if(busy)return;busy=true;error="";scope.launch { try{block()}catch(e:CancellationException){throw e}catch(e:Exception){error=e.message ?: "Could not complete the request."}finally{busy=false} } }
    androidx.activity.compose.BackHandler(enabled=editor!=null || newCompany || tab!="Overview") { editor=null;newCompany=false;tab="Overview" }
    Scaffold(containerColor=Paper,topBar={
        Column(Modifier.statusBarsPadding().padding(horizontal=20.dp,vertical=8.dp)) {
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) {
                BrandWordmark();Box {
                    IconButton(onClick={menu=true}){Icon(painterResource(R.drawable.ic_menu),"Workspace menu",tint=BrandDeep)}
                    DropdownMenu(expanded=menu,onDismissRequest={menu=false}) {
                        DropdownMenuItem(text={Text("Student workspace")},onClick={menu=false;student()})
                        DropdownMenuItem(text={Text("Refresh company status")},onClick={menu=false;reload++})
                        DropdownMenuItem(text={Text("Sign out")},onClick={menu=false;signOut()})
                    }
                }
            }
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                Text("COMPANY WORKSPACE",color=Muted,style=MaterialTheme.typography.labelSmall)
                if(company!=null)Box { TextButton(onClick={chooseCompany=true}){Text(company.name+" ▾")};DropdownMenu(expanded=chooseCompany,onDismissRequest={chooseCompany=false}) { companies.forEach { row -> DropdownMenuItem(text={Text(row.name)},onClick={selected=row.id;chooseCompany=false;editor=null;newCompany=false;tab="Overview"}) } } }
            }
        }
    },bottomBar={
        if(editor==null && !newCompany) NavigationBar {
            listOf("Overview","Vacancies","Company").forEachIndexed { i,label -> NavigationBarItem(selected=tab==label,onClick={tab=label},icon={Icon(painterResource(listOf(R.drawable.ic_matches,R.drawable.ic_growth,R.drawable.ic_person)[i]),null)},label={Text(label)},colors=NavigationBarItemDefaults.colors(indicatorColor=BrandSoft,selectedIconColor=BrandDeep,selectedTextColor=BrandDeep)) }
        }
    }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).imePadding().verticalScroll(rememberScrollState()).padding(horizontal=20.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
            if(error.isNotBlank()) { InfoCard("Let's try that again",error,CoralSoft,OrangeInk);TextButton(onClick={reload++},enabled=!loading){Text("Retry")}}
            if(message.isNotBlank()) { Text(message,color=Teal,style=MaterialTheme.typography.bodySmall);TextButton(onClick={message=""}){Text("Dismiss")}}
            if(busy) { LinearProgressIndicator(modifier=Modifier.fillMaxWidth());Text("Saving your changes…",style=MaterialTheme.typography.bodySmall) }
            when {
                loading -> {CircularProgressIndicator();Text("Loading your company and opportunities…")}
                newCompany || (companies.isEmpty() && error.isBlank()) -> RecruiterCompanyForm({newCompany=false;tab="Overview"}) { body -> perform { selected=client.register(body);newCompany=false;tab="Company";message="Company submitted for review.";reload++ } }
                company==null -> Text("Choose a company or retry loading your workspace.")
                editor!=null -> {
                    val existing=rows.find { it.id==editor }
                    RecruiterVacancyForm(uid,company,existing,{editor=null},{row->withdrawal=row}) { body -> val slot="${company.id}/${existing?.id ?: "new"}";perform { editor=client.submit(company.id,body);context.getSharedPreferences("recruiter-drafts-$uid",Context.MODE_PRIVATE).edit().remove(slot).apply();message="Changes saved. Check the review status after refreshing.";reload++ } }
                }
                tab=="Company" -> {
                    Heading("The people behind the opportunity", "Your company, introduced.")
                    RecruiterStatus(company.status)
                    InfoCard(company.name,company.description.ifBlank { "No company description provided." })
                    Text(company.website,color=BrandDeep);Text("Interested in offering: ${company.offerings.joinToString()}")
                    InfoCard("Your company status",if(company.status=="approved")"Your company can submit vacancies. Every vacancy is reviewed before students see it." else if(company.status=="pending")"Your registration is in review. You can prepare drafts while the UpShift team verifies your company." else "Your company is suspended. Contact your UpShift operator.",CoralSoft,OrangeInk)
                    Text("Training and mentorship are company interests; programme management is not available yet.",color=Muted,style=MaterialTheme.typography.bodySmall)
                    OutlinedButton(onClick={reload++},modifier=Modifier.fillMaxWidth()){Text("Refresh approval status")}
                    TextButton(onClick={newCompany=true}){Text("Register another company")}
                }
                else -> {
                    if(tab=="Overview") {
                        StatusPill("SMALL OPPORTUNITIES. BIG BEGINNINGS.",BrandSoft,BrandDeep)
                        Heading("Their next chapter could start with you.", "Share an opportunity. Help someone take their next step.")
                        Surface(color=BrandSoft,shape=MaterialTheme.shapes.large) { Column(Modifier.padding(24.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                            Text("Hire for what's possible.",style=MaterialTheme.typography.headlineMedium,color=BrandDeep,fontStyle=FontStyle.Italic)
                            Text("Curious minds. Fresh perspectives. Potential worth making room for.",color=BrandDeep)
                            Button(onClick={editor="new"},modifier=Modifier.fillMaxWidth()){Text("Create an opportunity")}
                        } }
                        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                            listOf("Published" to "published","In review" to "pending","Changes" to "rejected").forEach { (label,status) -> Card(Modifier.weight(1f),colors=CardDefaults.cardColors(containerColor=androidx.compose.ui.graphics.Color.White)) { Column(Modifier.padding(14.dp)) {Text(rows.count { it.status==status }.toString(),style=MaterialTheme.typography.headlineMedium,color=BrandDeep);Text(label,style=MaterialTheme.typography.bodySmall,color=Muted)} } }
                        }
                    } else { Heading("Your opportunities","From a first draft to a real beginning.");Button(onClick={editor="new"},modifier=Modifier.fillMaxWidth()){Text("Create a vacancy")}}
                    if(company.status!="approved") InfoCard("Company ${recruiterStatus(company.status).lowercase()}","You can save drafts. Company approval is required before submitting vacancies.",CoralSoft,OrangeInk)
                    val context=LocalContext.current
                    val prefs=remember(uid) { context.getSharedPreferences("recruiter-drafts-$uid",Context.MODE_PRIVATE) }
                    if(prefs.contains("${company.id}/new")) OutlinedButton(onClick={editor="new"},modifier=Modifier.fillMaxWidth()){Text("Continue draft on this device")}
                    var filter by rememberSaveable(selected) { mutableStateOf("all") }
                    var query by rememberSaveable(selected) { mutableStateOf("") }
                    if(tab=="Vacancies") {
                        Field("Search title or location",query){query=it}
                        Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(8.dp)) { listOf("all","published","pending","rejected","closed").forEach { status -> FilterChip(selected=filter==status,onClick={filter=status},label={Text(if(status=="all")"All" else recruiterStatus(status))}) } }
                    }
                    val visible=rows.filter { (tab!="Vacancies" || filter=="all" || it.status==filter) && (tab!="Vacancies" || "${it.payload.optString("title")} ${it.payload.optString("location")}".contains(query,true)) }
                    if(visible.isEmpty()) InfoCard("A first step, a new possibility","Your submitted vacancies will appear here. Create a vacancy to get started.")
                    visible.take(if(tab=="Overview")3 else Int.MAX_VALUE).forEach { row -> OutlinedCard(onClick={editor=row.id},modifier=Modifier.fillMaxWidth(),colors=CardDefaults.outlinedCardColors(containerColor=androidx.compose.ui.graphics.Color.White)) { Column(Modifier.padding(20.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {RecruiterStatus(row.status);Text(row.payload.optString("title"),style=MaterialTheme.typography.titleLarge);Text(row.payload.optString("location"),color=Muted);Text("View opportunity →",color=BrandDeep,style=MaterialTheme.typography.labelLarge)} } }
                    Text("You manage opportunities here. Students discover them in their own UpShift workspace.",color=Muted,style=MaterialTheme.typography.bodySmall)
                }
            }
            Spacer(Modifier.height(24.dp))
        }
    }
    withdrawal?.let { row -> AlertDialog(onDismissRequest={withdrawal=null},title={Text("Close this opportunity?")},text={Text("Withdraw this vacancy from the student feed. Its record stays in your workspace.")},confirmButton={TextButton(onClick={withdrawal=null;perform {client.withdraw(row.id);editor=null;message="Vacancy withdrawn.";reload++}}){Text("Withdraw")}},dismissButton={TextButton(onClick={withdrawal=null}){Text("Keep vacancy")}}) }
}

@Composable private fun RecruiterStatus(status:String) { StatusPill(recruiterStatus(status),if(status in listOf("approved","published"))Mint else if(status in listOf("pending","rejected","suspended"))CoralSoft else BrandSoft,if(status in listOf("approved","published"))Teal else if(status in listOf("pending","rejected","suspended"))OrangeInk else BrandDeep) }

@Composable private fun RecruiterCompanyForm(back:()->Unit,submit:(JSONObject)->Unit) {
    var name by rememberSaveable { mutableStateOf("") };var website by rememberSaveable { mutableStateOf("") };var description by rememberSaveable { mutableStateOf("") }
    var offerings by rememberSaveable { mutableStateOf(listOf("vacancies")) };var error by remember { mutableStateOf("") }
    Heading("Let's meet your company.","Tell us who you are and how you'd like to open doors.")
    Field("Company name",name){name=it.take(160)};Field("Company website · https://",website){website=it.take(2048)};Field("About your company",description,false){description=it.take(3000)}
    Text("How would you like to contribute?",style=MaterialTheme.typography.titleMedium)
    listOf("vacancies","training","mentorship").forEach { value -> Row(verticalAlignment=Alignment.CenterVertically) {Checkbox(checked=value in offerings,onCheckedChange={checked->offerings=if(checked)offerings+value else offerings-value});Text(value.replaceFirstChar { it.uppercase() })} }
    InfoCard("A request for verification","Your company will be linked to your signed-in account. Registration does not confirm a partnership.",CoralSoft,OrangeInk)
    if(error.isNotBlank())Text(error,color=OrangeInk)
    Button(onClick={error=when {name.trim().length<2->"Enter your company name.";!recruiterHttps(website.trim())->"Use a full https:// company website.";offerings.isEmpty()->"Choose at least one offering.";else->""};if(error.isBlank())submit(JSONObject().put("name",name.trim()).put("website",website.trim()).put("description",description.trim()).put("offerings",JSONArray(offerings)))},modifier=Modifier.fillMaxWidth()){Text("Submit company for review")}
    TextButton(onClick=back){Text("Back to workspace")}
}

@Composable private fun RecruiterVacancyForm(uid:String,company:RecruiterCompany,existing:RecruiterVacancy?,back:()->Unit,withdraw:(RecruiterVacancy)->Unit,submit:(JSONObject)->Unit) {
    val context=LocalContext.current;val prefs=remember(uid) { context.getSharedPreferences("recruiter-drafts-$uid",Context.MODE_PRIVATE) }
    val draftKey="${company.id}/${existing?.id ?: "new"}"
    var draft by rememberSaveable(draftKey) { mutableStateOf(prefs.getString(draftKey,null) ?: (existing?.payload?.let { original -> JSONObject().apply { original.keys().forEach { key -> val value=original.opt(key);put(key,when(value){is JSONArray->value.texts().joinToString(if(key=="skills")", " else "\n");JSONObject.NULL->"";else->value}) } } } ?: JSONObject().put("career_level","internship")).toString()) }
    var feedback by remember { mutableStateOf("") }
    val fields=JSONObject(draft)
    fun set(key:String,value:String){draft=JSONObject(draft).put(key,value).toString()}
    TextButton(onClick=back){Text("← All opportunities")}
    Heading(if(existing==null)"Create a meaningful opportunity." else "Give potential a place to grow.","Clear requirements. Honest expectations. A chance to learn.")
    existing?.let { RecruiterStatus(it.status);if(it.note.isNotBlank())InfoCard("Review feedback",it.note,CoralSoft,OrangeInk);if(it.status=="published")Text("Submitting edits hides this vacancy until the changes are reviewed.",color=OrangeInk) }
    Text("The opportunity",style=MaterialTheme.typography.titleLarge)
    listOf("title" to "Role title","location" to "Location","arrangement" to "Work arrangement").forEach { (key,label)->Field(label,fields.optString(key)){set(key,it.take(if(key=="arrangement")160 else 200))} }
    Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(8.dp)) { listOf("internship","student_attachment","graduate_trainee","entry_level").forEach { level -> FilterChip(selected=fields.optString("career_level")==level,onClick={set("career_level",level)},label={Text(level.replace('_',' '))}) } }
    Field("Describe the role",fields.optString("description"),false){set("description",it.take(20000))}
    Field("Skills · comma separated",fields.optString("skills")){set("skills",it.take(4000))}
    listOf("responsibilities" to "Responsibilities · one per line","requirements" to "Requirements · one per line","eligibility" to "Who can apply? · one condition per line").forEach { (key,label)->Field(label,fields.optString(key),false){set(key,it.take(20000))} }
    Text("The next step for candidates",style=MaterialTheme.typography.titleLarge)
    OutlinedTextField(value=fields.optString("source_url"),onValueChange={set("source_url",it.take(2048))},readOnly=existing!=null,label={Text("Official advert URL · https://")},modifier=Modifier.fillMaxWidth())
    Field("Application URL · optional",fields.optString("application_url")){set("application_url",it.take(2048))}
    Field("Closing date · YYYY-MM-DD · optional",fields.optString("deadline")){set("deadline",it.take(10))}
    InfoCard("A thoughtful review before publication",if(company.status=="approved")"Your vacancy goes to the UpShift team for review. It is not published immediately." else "Company approval is required before submission. You can save your draft on this device.",CoralSoft,OrangeInk)
    if(feedback.isNotBlank())Text(feedback,color=OrangeInk)
    Button(enabled=company.status=="approved",onClick={try {val payload=recruiterPayload(JSONObject(draft).let { json -> json.keys().asSequence().associateWith {json.optString(it)} });prefs.edit().putString(draftKey,draft).apply();submit(payload)}catch(e:IllegalArgumentException){feedback=e.message.orEmpty()}},modifier=Modifier.fillMaxWidth()){Text("Submit for review")}
    OutlinedButton(onClick={prefs.edit().putString(draftKey,draft).apply();feedback="Draft saved on this device. It has not been submitted."},modifier=Modifier.fillMaxWidth()){Text("Save draft on this device")}
    if(existing!=null && existing.status!="closed")TextButton(onClick={withdraw(existing)}){Text("Withdraw vacancy")}
}
