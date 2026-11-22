package ke.upshift.app

import android.view.*
import android.widget.TextView
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import androidx.compose.ui.viewinterop.AndroidView
import androidx.recyclerview.widget.*
import kotlinx.coroutines.launch
import androidx.compose.ui.platform.LocalUriHandler

@Composable fun MatchesScreen(state:AppState,open:(String)->Unit,profile:()->Unit,recommendations:()->Unit) {
    var query by rememberSaveable{mutableStateOf("")}
    var savedOnly by rememberSaveable{mutableStateOf(false)}
    val roles=state.rankedRoles().filter{(!savedOnly||it.id in state.saved)&&("${it.title} ${it.company} ${it.location} ${it.skills.joinToString()}").contains(query,true)}
    ScreenList(Modifier.fillMaxSize(),contentPadding=PaddingValues(start=20.dp,end=20.dp,top=12.dp,bottom=104.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
        item {
            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(5.dp)) {
                    Text(if(state.profile.name.isBlank())"LET’S FIND YOUR NEXT STEP" else "Good to see you, ${state.profile.name.substringBefore(' ')}",color=Muted,style=MaterialTheme.typography.bodySmall)
                    Text("Explore real opportunities",style=MaterialTheme.typography.headlineMedium)
                }
                StatusPill("🔥 ${state.streak()}",CoralSoft,OrangeInk)
            }
        }
        item {
            val next=state.growthSteps().firstOrNull{it.skill !in state.completed}
            Card(colors=CardDefaults.cardColors(containerColor=BrandSoft,contentColor=BrandDeep)) {
                Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    Text(if(state.profile.skills.isBlank())"START WITH YOUR SKILLS" else "ONE SMALL STEP",style=MaterialTheme.typography.labelSmall)
                    Text(if(state.profile.skills.isBlank())"Find what fits you" else next?.title ?: "Keep your profile growing",style=MaterialTheme.typography.titleLarge)
                    Text(if(state.profile.skills.isBlank())"Add your skills to see percentages and personalised gaps." else "Open Growth to practise a skill and save what you learn.",style=MaterialTheme.typography.bodyMedium)
                    if(state.profile.skills.isBlank())TextButton(onClick=profile){Text("Add my skills →")}
                }
            }
        }
        item {
            Button(onClick = recommendations, modifier = Modifier.fillMaxWidth()) {
                Text("Get job recommendations")
            }
        }
        item {OutlinedTextField(query,{query=it},label={Text("Search jobs, skills or location")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(12.dp))}
        item {
            Row(horizontalArrangement=Arrangement.spacedBy(8.dp),verticalAlignment=Alignment.CenterVertically) {
                FilterChip(selected=savedOnly,onClick={savedOnly=!savedOnly},label={Text("Saved roles")})
                Text(if(state.profile.skills.isBlank())"${roles.size} opportunities" else "Highest skills match first",style=MaterialTheme.typography.labelMedium,color=Muted)
            }
        }
        if(roles.isEmpty())item{InfoCard("No roles found",if(state.roles.isEmpty() && state.userId != null) "No opportunities have been published yet. Your profile and progress are still available." else "Try another search or turn off the saved filter.",CoralSoft,OrangeInk)}
        itemsIndexed(roles,key={_,role->role.id}) { index,role ->
            if(index==0)Text(if(state.profile.skills.isBlank())"EXPLORE OPPORTUNITIES" else "CLOSEST TO YOU RIGHT NOW",style=MaterialTheme.typography.labelSmall,color=BrandDeep,modifier=Modifier.padding(bottom=8.dp))
            RoleCard(state,role){open(role.id)}
        }
        item{Text("Source-backed adverts. Availability needs confirmation. Skills coverage includes preferred tools and alternatives; check eligibility separately.",style=MaterialTheme.typography.bodySmall,color=Muted)}
    }
}
@Composable fun RoleCard(state:AppState,role:Role,open:()->Unit) {
    val score=state.score(role)
    val gapCount=state.gaps(role).size
    OutlinedCard(onClick=open,modifier=Modifier.fillMaxWidth(),border=BorderStroke(1.dp,Line),colors=CardDefaults.outlinedCardColors(containerColor=Color.White)) {
        Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(16.dp)) {
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(5.dp)) {
                    Text(role.company,style=MaterialTheme.typography.labelLarge,color=BrandDeep)
                    Text(role.title,style=MaterialTheme.typography.titleLarge)
                    Text(role.location,style=MaterialTheme.typography.bodySmall,color=Muted)
                    Text(if(role.availabilityStatus=="published") "Reviewed listing - confirm details with employer" else "Confirm availability with employer",style=MaterialTheme.typography.labelSmall,color=OrangeInk)
                }
                MatchRing(score)
            }
            Row(horizontalArrangement=Arrangement.spacedBy(8.dp),verticalAlignment=Alignment.CenterVertically) {
                StatusPill(when{score==null->"Build your match";score>=70->"Close match";score>=40->"Stretch role";else->"Room to grow"},when{score==null->BrandSoft;score>=70->Mint;score>=40->CoralSoft;else->Lavender},when{score==null->BrandDeep;score>=70->Teal;score>=40->OrangeInk;else->Plum})
                if(score!=null)Text("$gapCount ${if(gapCount==1)"skill" else "skills"} to develop",style=MaterialTheme.typography.bodySmall,color=Muted)
            }
            Text("View role & requirements →",style=MaterialTheme.typography.labelLarge,color=BrandDeep)
        }
    }
}
@Composable fun RoleScreen(state:AppState,role:Role,back:()->Unit,plan:()->Unit,cv:()->Unit,coach:()->Unit) {
    val listState=rememberLazyListState()
    val scope=rememberCoroutineScope()
    val uriHandler=LocalUriHandler.current
    var sourceError by remember(role.id){mutableStateOf("")}
    ScreenList(state=listState,modifier=Modifier.fillMaxSize(),contentPadding=PaddingValues(start=20.dp,end=20.dp,top=8.dp,bottom=104.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
        item{TextButton(onClick=back){Text("← All matches")}}
        item{Heading(role.title,"${role.company}\n${role.location}")}
        item{
            Surface(color=BrandSoft,shape=MaterialTheme.shapes.medium) {
                Row(Modifier.fillMaxWidth().padding(20.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(18.dp)) {
                    MatchRing(state.score(role),88.dp)
                    Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(6.dp)){Text("Your skills coverage",style=MaterialTheme.typography.titleMedium,color=BrandDeep);Text(role.arrangement,style=MaterialTheme.typography.bodySmall);Text(if(role.skills.isEmpty()) "Skills not specified in this summary" else "${role.skills.size-state.gaps(role).size} of ${role.skills.size} listed skill tags in your profile",style=MaterialTheme.typography.bodySmall)}
                }
            }
        }
        item {
            LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                items(listOf("Responsibilities" to 5,"Requirements" to 6,"Eligibility" to 7,"Skill gaps" to 10)) { (label,index) ->
                    AssistChip(onClick={scope.launch{listState.animateScrollToItem(index)}},label={Text(label)},colors=AssistChipDefaults.assistChipColors(containerColor=BrandSoft,labelColor=BrandDeep))
                }
            }
        }
        item{
            Column(verticalArrangement=Arrangement.spacedBy(10.dp)) {
                Text(role.description,style=MaterialTheme.typography.bodyLarge)
                Text(if(role.availabilityStatus=="published") "Reviewed for publication. Confirm current availability and details with the employer." else "Availability needs confirmation. This advert has not been verified as currently open.",color=OrangeInk,style=MaterialTheme.typography.bodyMedium)
                if(role.companyDescription.isNotBlank())Text("About ${role.company}: ${role.companyDescription}",style=MaterialTheme.typography.bodyMedium)
                if(role.companyOfferings.isNotEmpty())Text("Company offerings: ${role.companyOfferings.joinToString()}",style=MaterialTheme.typography.bodySmall)
                if(role.companyWebsite.isNotBlank())Text(role.companyWebsite,style=MaterialTheme.typography.bodySmall,color=Muted)
                if(role.collectedDate.isNotBlank())Text("Collected: ${role.collectedDate}",color=Muted,style=MaterialTheme.typography.bodySmall)
                Text(if(role.deadline.isBlank()) "Closing date: unconfirmed" else "Reported closing date: ${role.deadline}",style=MaterialTheme.typography.bodySmall)
                if(role.researchNotes.isNotBlank())Text(role.researchNotes,style=MaterialTheme.typography.bodySmall,color=Muted)
                if(role.skillInterpretation.isNotBlank())Text(role.skillInterpretation,style=MaterialTheme.typography.bodySmall,color=Muted)
                if(role.hasSource()) {
                    Text(role.sourceUrl,style=MaterialTheme.typography.bodySmall,color=Muted)
                    OutlinedButton(onClick={runCatching{uriHandler.openUri(role.sourceUrl)}.onFailure{sourceError="Could not open the source. Check that a browser is available."}},modifier=Modifier.fillMaxWidth()){Text("View source advert")}
                }
                if(sourceError.isNotBlank())Text(sourceError,color=OrangeInk)
            }
        }
        item{SectionList("What you'll do",role.responsibilities.ifEmpty{listOf("See the role summary and source advert for full duties.")},BrandSoft,BrandDeep)}
        item{SectionList("What's required",role.requirements.ifEmpty{listOf("Check the eligibility notes and source advert for full requirements.")},Lavender,Plum)}
        item{SectionList("Who can apply",role.eligibility,CoralSoft,OrangeInk)}
        item{Heading("What you already have","")}
        item{val have=role.skills.filter{it !in state.gaps(role)};if(have.isEmpty())Text("Add your current skills in You to see them here.",color=Muted)else SkillChips(have)}
        item{Heading("Skills to develop","")}
        item{val gaps=state.gaps(role);if(role.skills.isEmpty())Text("Skill requirements are not specified. Review the source advert.",color=Muted)else if(gaps.isEmpty())InfoCard("All listed skills are in your profile","Prepare examples that show how you have used them.",Mint,Teal)else Column(verticalArrangement=Arrangement.spacedBy(8.dp)){SkillChips(gaps,true);if(gaps.any{gap->LearningLibrary.none{it.skill.equals(gap,true)}})Text("Growth activities cover some of these skills. Review the source and choose additional learning for the others.",color=Muted,style=MaterialTheme.typography.bodySmall)}}
        item{InfoCard("What happens next","Choose this role as your target. Growth will focus on its missing skills, then you can prepare a CV with relevant project examples.",Mint,Teal)}
        item{Button(onClick=plan,modifier=Modifier.fillMaxWidth()){Text("Build my growth path")}}
        item{OutlinedButton(onClick={state.toggleSaved(role.id)},modifier=Modifier.fillMaxWidth()){Text(if(role.id in state.saved)"Remove saved role" else "Save this role")}}
        item{OutlinedButton(onClick=cv,modifier=Modifier.fillMaxWidth()){Text("Prepare my CV")}}
        item{TextButton(onClick=coach){Text("Ask about this match ✦")}}
        item{Text("The percentage describes listed skills coverage, not hiring probability. Confirm availability and eligibility with the employer before applying.",style=MaterialTheme.typography.bodySmall,color=Muted)}
    }
}
@Composable fun SectionList(title:String,lines:List<String>,color:Color,ink:Color) {
    Card(colors=CardDefaults.cardColors(containerColor=color,contentColor=ink)) {
        Column(Modifier.fillMaxWidth().padding(20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Text(title,style=MaterialTheme.typography.titleLarge)
            lines.forEach{line->Row(horizontalArrangement=Arrangement.spacedBy(10.dp)){Text("•");Text(line,modifier=Modifier.weight(1f),style=MaterialTheme.typography.bodyMedium)}}
        }
    }
}
@Composable fun GrowthScreen(state:AppState,open:(String)->Unit,practice:(String)->Unit) {
    val steps=state.growthSteps()
    val courses=steps.groupBy { courseForSkill(it.skill) }
    val uriHandler=LocalUriHandler.current
    var linkError by remember { mutableStateOf("") }
    val done=steps.count{it.skill in state.completed}
    val target=state.roles.find{it.id==state.targetId}
    ScreenList(Modifier.fillMaxSize(),contentPadding=PaddingValues(start=20.dp,end=20.dp,top=12.dp,bottom=104.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
        item{Heading("Your growth path","Certificate programmes for your missing skills. Learn with established providers, then track your progress.")}
        item{
            Card(colors=CardDefaults.cardColors(containerColor=Lavender,contentColor=Plum)) {
                Column(Modifier.fillMaxWidth().padding(20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text("Level ${1+state.xp()/150}",style=MaterialTheme.typography.titleMedium);Text("$done / ${steps.size} skills reviewed")}
                    LinearProgressIndicator(progress={if(steps.isEmpty())0f else done.toFloat()/steps.size},modifier=Modifier.fillMaxWidth(),color=Plum,trackColor=Color.White)
                    Text("${state.xp()} XP · ${state.streak()} day streak",style=MaterialTheme.typography.bodyMedium)
                }
            }
        }
        item{Text("Provider fees may apply. Certificates are issued by the provider; your skill reviews are tracked here.",style=MaterialTheme.typography.bodySmall,color=Muted)}
        if(linkError.isNotBlank())item{InfoCard("Could not open course",linkError,CoralSoft,OrangeInk)}
        if(target!=null)item{
            InfoCard("Focused on ${target.title}","${state.gaps(target).size} skills to develop for ${target.company}.",BrandSoft,BrandDeep)
            Row{TextButton(onClick={open(target.id)}){Text("View role")};TextButton(onClick={state.clearTarget()}){Text("Show all opportunities")}}
        }
        if(steps.isEmpty())item{InfoCard("You’ve covered the listed skills","Explore a stretch role or add a project that demonstrates your strengths.",Mint,Teal)}
        items(courses.entries.toList(),key={it.key.url}){(course,relatedSteps)->
            val reviewed=relatedSteps.count { it.skill in state.completed }
            val next=relatedSteps.firstOrNull { it.skill !in state.completed } ?: relatedSteps.first()
            Card(colors=CardDefaults.cardColors(containerColor=Color.White),border=BorderStroke(1.dp,Line)) {
                Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    StatusPill(course.provider,BrandSoft,BrandDeep)
                    Text(course.title,style=MaterialTheme.typography.titleLarge)
                    Text("Professional certificate programme",style=MaterialTheme.typography.bodySmall,color=Muted)
                    Text("Related skills: ${relatedSteps.joinToString { it.skill }}",style=MaterialTheme.typography.bodyMedium)
                    if(reviewed>0)StatusPill("$reviewed of ${relatedSteps.size} skills reviewed",Mint,Teal)
                    Button(onClick={runCatching { uriHandler.openUri(course.url) }.onFailure { linkError="No browser is available. Install or enable a browser, then try again." }},modifier=Modifier.fillMaxWidth()){Text("View programme ↗")}
                    OutlinedButton(onClick={practice(next.skill)},modifier=Modifier.fillMaxWidth()){Text("${if(reviewed==relatedSteps.size)"Review" else "Record"} my learning · ${next.skill}")}
                }
            }
        }
    }
}
@Composable fun YouScreen(state:AppState,edit:()->Unit,cv:()->Unit,growth:()->Unit,saved:()->Unit) {
    val scores=state.roles.mapNotNull{state.score(it)}
    val average=if(scores.isEmpty())null else scores.average().toInt()
    val initials=state.profile.name.split(" ").filter{it.isNotBlank()}.take(2).joinToString(""){it.first().uppercase()}.ifBlank{"U"}
    ScreenList(Modifier.fillMaxSize(),contentPadding=PaddingValues(start=20.dp,end=20.dp,top=12.dp,bottom=104.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
        item{
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(14.dp)) {
                Box(Modifier.size(64.dp).clip(CircleShape).background(Brush.linearGradient(listOf(Coral,Brand))),contentAlignment=Alignment.Center){Text(initials,style=MaterialTheme.typography.titleLarge,color=Color.White)}
                Column(Modifier.weight(1f)){Text(state.profile.name.ifBlank{"Your profile"},style=MaterialTheme.typography.headlineSmall);Text(state.profile.education.ifBlank{"Add your education"},style=MaterialTheme.typography.bodySmall,color=Muted);Text(state.profile.location.ifBlank{"Kenya"},style=MaterialTheme.typography.bodySmall,color=Muted)}
            }
        }
        item{
            Card(colors=CardDefaults.cardColors(containerColor=BrandSoft)) {
                Row(Modifier.fillMaxWidth().padding(20.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(20.dp)){
                    MatchRing(average,104.dp,"avg match")
                    Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(6.dp)){Text("Your next chapter",style=MaterialTheme.typography.titleLarge,color=BrandDeep);Text(state.profile.goal,style=MaterialTheme.typography.bodyMedium);Text("Across ${state.roles.size} opportunities",style=MaterialTheme.typography.bodySmall,color=Muted)}
                }
            }
        }
        item{Row(horizontalArrangement=Arrangement.spacedBy(12.dp)){StatCard("${state.profile.skillSet().size}","Skills",Mint,Teal,Modifier.weight(1f));StatCard("${state.completed.size}","Steps done",BrandSoft,BrandDeep,Modifier.weight(1f))}}
        item{Row(horizontalArrangement=Arrangement.spacedBy(12.dp)){StatCard("${state.streak()}","Day streak",CoralSoft,OrangeInk,Modifier.weight(1f));StatCard("${1+state.xp()/150}","Level · ${state.xp()} XP",Lavender,Plum,Modifier.weight(1f))}}
        item{Text("Your skills",style=MaterialTheme.typography.titleLarge)}
        item{if(state.profile.skills.isBlank())InfoCard("Start with what you know","Add skills from coursework, projects or volunteering.")else SkillChips(state.profile.skills.split(",").map{it.trim()}.filter{it.isNotEmpty()})}
        item{Button(onClick=edit,modifier=Modifier.fillMaxWidth()){Text("Edit profile & skills")}}
        item{OutlinedButton(onClick=cv,modifier=Modifier.fillMaxWidth()){Text("Build my CV")}}
        item{OutlinedButton(onClick=saved,modifier=Modifier.fillMaxWidth()){Text("Saved roles · ${state.saved.size}")}}
        item{Text("Completed steps",style=MaterialTheme.typography.titleLarge)}
        if(state.completed.isEmpty())item{InfoCard("Your progress starts with one step","Choose an activity in Growth and save a short reflection.",CoralSoft,OrangeInk)}
        items(state.completed.sorted(),key={it}){skill->InfoCard("✓ $skill",state.evidenceFor(skill).ifBlank{"Practice completed"},Mint,Teal)}
        item{TextButton(onClick=growth){Text("Open my growth path →")}}
    }
}
@Composable fun StatCard(value:String,label:String,color:Color,ink:Color,modifier:Modifier) {
    Surface(modifier=modifier,color=color,shape=RoundedCornerShape(18.dp)){Column(Modifier.padding(18.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(6.dp)){Text(value,style=MaterialTheme.typography.headlineSmall,color=ink);Text(label,style=MaterialTheme.typography.bodySmall,color=ink)}}
}
@Composable fun EditProfileScreen(state:AppState,back:()->Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
        TextButton(onClick=back){Text("← Back")}
        Heading("Your starting point","Projects, coursework and volunteering all count.")
        ProfileFields(state)
        Text(if(state.userId != null) "Changes save to your account. Check the save status above." else "Changes save automatically on this device.",style=MaterialTheme.typography.bodySmall,color=Muted)
        Button(onClick={state.flushProfile();back()},modifier=Modifier.fillMaxWidth()){Text("Done")}
        Spacer(Modifier.height(24.dp))
    }
}
@Composable fun SavedRolesScreen(state:AppState,back:()->Unit,open:(String)->Unit) {
    val roles=state.rankedRoles().filter{it.id in state.saved}
    Column(Modifier.fillMaxSize().padding(horizontal=20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
        TextButton(onClick=back){Text("← Back")}
        Heading("Saved opportunities","Return to the roles you want to explore.")
        if(roles.isEmpty())InfoCard("No saved roles yet","Open a role in Matches and tap Save this role.",CoralSoft,OrangeInk)
        else AndroidView(factory={context->RecyclerView(context).apply{layoutManager=LinearLayoutManager(context);adapter=SavedRoleAdapter()}},update={list->(list.adapter as SavedRoleAdapter).submit(roles,state,open)},modifier=Modifier.weight(1f).fillMaxWidth())
    }
}
class SavedRoleAdapter:RecyclerView.Adapter<SavedRoleAdapter.Holder>() {
    private var rows=listOf<Role>()
    private var scores=mapOf<String,Int?>()
    private var open:(String)->Unit={}
    fun submit(next:List<Role>,state:AppState,action:(String)->Unit){val nextScores=next.associate{it.id to state.score(it)};open=action;if(next!=rows||scores!=nextScores){rows=next;scores=nextScores;notifyDataSetChanged()}}
    class Holder(val label:TextView):RecyclerView.ViewHolder(label)
    override fun onCreateViewHolder(parent:ViewGroup,type:Int)=Holder(TextView(parent.context).apply{val d=resources.displayMetrics.density;setPadding((18*d).toInt(),(22*d).toInt(),(18*d).toInt(),(22*d).toInt());textSize=16f;typeface=resources.getFont(R.font.karla);setTextColor(android.graphics.Color.rgb(30,63,176));layoutParams=ViewGroup.LayoutParams(-1,-2);isFocusable=true})
    override fun getItemCount()=rows.size
    override fun onBindViewHolder(holder:Holder,position:Int){val role=rows[position];holder.label.text="${role.title}\n${role.company} · ${scores[role.id]?.let{"$it% skills match"} ?: "Add your skills"}\n${role.location}\n\nView requirements →";holder.label.setOnClickListener{open(role.id)}}
}
