package ke.upshift.app

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.ui.geometry.*
import androidx.compose.ui.semantics.Role as SemanticRole
import androidx.compose.foundation.shape.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.*
import androidx.compose.ui.unit.*

val Teal=Color(0xFF17634F)
val Mint=Color(0xFFDFF2E8)
val Lavender=Color(0xFFEEE6FA)
val Plum=Color(0xFF68439C)
val OrangeInk=Color(0xFF85430E)
@Composable fun BrandWordmark() {
    Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        BrandMark(25.dp)
        Text("upshift",fontFamily=FrauncesItalic,fontStyle=FontStyle.Italic,fontSize=24.sp,color=BrandDeep)
    }
}
@Composable fun Heading(title:String,subtitle:String) {
    Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text(title,style=MaterialTheme.typography.headlineMedium,color=Ink)
        if(subtitle.isNotBlank()) Text(subtitle,style=MaterialTheme.typography.bodyMedium,color=Muted)
    }
}
@Composable fun InfoCard(title:String,body:String,color:Color=BrandSoft,ink:Color=BrandDeep) {
    Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=color,contentColor=ink)) {
        Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) { Text(title,style=MaterialTheme.typography.titleMedium);Text(body,style=MaterialTheme.typography.bodyMedium) }
    }
}
@Composable fun StatusPill(text:String,color:Color=BrandSoft,ink:Color=BrandDeep) {
    Surface(color=color,shape=RoundedCornerShape(12.dp)) {Text(text,modifier=Modifier.padding(horizontal=12.dp,vertical=7.dp),style=MaterialTheme.typography.labelMedium,color=ink)}
}
@Composable fun MatchRing(percent:Int?,size:Dp=68.dp,label:String?=null) {
    val colour=when {percent==null->Muted;percent>=70->Brand;percent>=40->Coral;else->Plum}
    Box(Modifier.size(size).semantics(mergeDescendants=true){contentDescription=if(percent==null) "Add skills to calculate match" else "$percent percent ${label ?: "skills match"}"},contentAlignment=Alignment.Center) {
        Canvas(Modifier.fillMaxSize().padding(4.dp)) {
            val width=6.dp.toPx()
            drawArc(color=Line,startAngle=-90f,sweepAngle=360f,useCenter=false,style=Stroke(width))
            if(percent!=null)drawArc(color=colour,startAngle=-90f,sweepAngle=3.6f*percent,useCenter=false,style=Stroke(width,cap=StrokeCap.Round))
        }
        Column(horizontalAlignment=Alignment.CenterHorizontally,modifier=Modifier.clearAndSetSemantics{}) {
            Text(if(percent==null) "—" else "$percent%",fontFamily=Karla,fontWeight=FontWeight.Bold,fontSize=if(size>90.dp) 23.sp else 16.sp,color=colour)
            if(label!=null)Text(label,fontSize=11.sp,color=Muted)
        }
    }
}
@OptIn(ExperimentalLayoutApi::class)
@Composable fun SkillChips(skills:List<String>,missing:Boolean=false) {
    FlowRow(horizontalArrangement=Arrangement.spacedBy(8.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
        skills.forEach {StatusPill(it,if(missing)CoralSoft else Mint,if(missing)OrangeInk else Teal)}
    }
}
@OptIn(ExperimentalLayoutApi::class)
@Composable fun SkillSelector(state:AppState) {
    val selected=state.profile.skillSet()
    Text("${selected.size} skills selected",style=MaterialTheme.typography.labelLarge,color=BrandDeep)
    FlowRow(horizontalArrangement=Arrangement.spacedBy(8.dp),verticalArrangement=Arrangement.spacedBy(4.dp)) {
        LearningLibrary.forEach { step -> FilterChip(selected=step.skill.lowercase() in selected,onClick={
            val current=state.profile.skills.split(",").map{it.trim()}.filter{it.isNotEmpty()}
            val next=if(step.skill.lowercase() in selected)current.filterNot{it.equals(step.skill,true)}else current+step.skill
            state.update(state.profile.copy(skills=next.joinToString(", ")))
        },label={Text(step.skill)},colors=FilterChipDefaults.filterChipColors(selectedContainerColor=BrandSoft,selectedLabelColor=BrandDeep)) }
    }
    Field("Other skills, separated by commas",state.profile.skills,false){state.update(state.profile.copy(skills=it))}
}
@Composable fun Field(label:String,value:String,single:Boolean=true,change:(String)->Unit) {
    OutlinedTextField(value,change,label={Text(label)},singleLine=single,minLines=if(single)1 else 3,maxLines=if(single)1 else 6,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(12.dp))
}
@Composable fun ProfileFields(state:AppState) {
    val p=state.profile
    Field("Full name",p.name){state.update(state.profile.copy(name=it))}
    if(state.userId != null) OutlinedTextField(p.email,{},readOnly=true,label={Text("Account email")},modifier=Modifier.fillMaxWidth())
    else Field("Email",p.email){state.update(state.profile.copy(email=it))}
    Field("Phone (optional)",p.phone){state.update(state.profile.copy(phone=it))}
    Field("Location",p.location){state.update(state.profile.copy(location=it))}
    Field("Education and dates",p.education,false){state.update(state.profile.copy(education=it))}
    Field("Skills, separated by commas",p.skills,false){state.update(state.profile.copy(skills=it))}
    Field("Professional summary",p.summary,false){state.update(state.profile.copy(summary=it))}
    Field("Projects and achievements",p.projects,false){state.update(state.profile.copy(projects=it))}
    Field("Experience or volunteering (optional)",p.experience,false){state.update(state.profile.copy(experience=it))}
}

@Composable fun CoachLauncher(open:()->Unit) {
    Box(Modifier.size(56.dp),contentAlignment=Alignment.Center) {
        BrandMark(48.dp,Modifier.semantics { contentDescription="Open your coach" }.clickable(role=SemanticRole.Button,onClick=open))
    }
}
@Composable fun ScreenList(
    modifier:Modifier=Modifier,
    state:LazyListState=rememberLazyListState(),
    contentPadding:PaddingValues=PaddingValues(start=20.dp,end=20.dp,top=12.dp,bottom=104.dp),
    verticalArrangement:Arrangement.Vertical=Arrangement.spacedBy(16.dp),
    content:LazyListScope.()->Unit
) {
    Box(modifier.fillMaxSize()) {
        LazyColumn(state=state,modifier=Modifier.fillMaxSize(),contentPadding=contentPadding,verticalArrangement=verticalArrangement,content=content)
        Canvas(Modifier.align(Alignment.CenterEnd).fillMaxHeight().width(4.dp).padding(vertical=10.dp)) {
            val info=state.layoutInfo
            if(info.totalItemsCount>0 && (state.canScrollForward || state.canScrollBackward)) {
                val visible=info.visibleItemsInfo
                val fraction=(visible.size.toFloat()/info.totalItemsCount).coerceIn(.08f,.85f)
                val thumb=size.height*fraction
                val first=visible.firstOrNull()
                val part=if(first==null||first.size==0)0f else state.firstVisibleItemScrollOffset.toFloat()/first.size
                val progress=((state.firstVisibleItemIndex+part)/(info.totalItemsCount-visible.size).coerceAtLeast(1)).coerceIn(0f,1f)
                drawRoundRect(Line.copy(alpha=.6f),cornerRadius=CornerRadius(8f,8f))
                drawRoundRect(Brand.copy(alpha=.5f),topLeft=Offset(0f,progress*(size.height-thumb)),size=Size(size.width,thumb),cornerRadius=CornerRadius(8f,8f))
            }
        }
    }
}
