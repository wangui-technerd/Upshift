package ke.upshift.app

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.shape.RoundedCornerShape

@OptIn(ExperimentalMaterial3Api::class)
@Composable fun CoachSheet(state:AppState,role:Role?,dismiss:()->Unit) {
    val contextRole=role ?: state.roles.find{it.id==state.targetId}
    var input by rememberSaveable {mutableStateOf("")}
    var messages by rememberSaveable(contextRole?.id) {mutableStateOf(listOf("Hi ${state.profile.name.substringBefore(' ').ifBlank{"there"}}. Let’s work on your next step. Ask about ${contextRole?.title ?: "your matches"}, a skill gap or your CV."))}
    val list=rememberLazyListState()
    LaunchedEffect(messages.size){if(messages.isNotEmpty())list.animateScrollToItem(messages.lastIndex)}
    fun send(question:String){if(question.isNotBlank()){messages=messages+question.trim()+state.coach.reply(question,contextRole,state);input=""}}
    ModalBottomSheet(onDismissRequest=dismiss,sheetState=rememberModalBottomSheetState(skipPartiallyExpanded=true),containerColor=Paper) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(0.92f).imePadding().padding(horizontal=20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically){
                Column(Modifier.weight(1f)){Text("Your coach ✦",style=MaterialTheme.typography.headlineSmall,color=BrandDeep);Text("Guided role & skills help",style=MaterialTheme.typography.bodySmall,color=Muted)}
                TextButton(onClick=dismiss){Text("Close")}
            }
            LazyColumn(state=list,modifier=Modifier.weight(1f).fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(vertical=12.dp)) {
                itemsIndexed(messages){index,message->
                    Surface(color=if(index%2==0)Color.White else BrandSoft,shape=RoundedCornerShape(18.dp),modifier=Modifier.fillMaxWidth().padding(start=if(index%2==0)0.dp else 28.dp,end=if(index%2==0)28.dp else 0.dp)) {
                        Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(5.dp)){Text(if(index%2==0)"Coach" else "You",style=MaterialTheme.typography.labelSmall,color=BrandDeep);Text(message,style=MaterialTheme.typography.bodyMedium)}
                    }
                }
            }
            LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp)){items(listOf("Explain my match","What should I learn next?","Help with my CV","Check eligibility")){question->AssistChip(onClick={send(question)},label={Text(question)})}}
            Row(Modifier.fillMaxWidth().padding(bottom=18.dp),horizontalArrangement=Arrangement.spacedBy(8.dp),verticalAlignment=Alignment.CenterVertically){
                OutlinedTextField(input,{input=it},label={Text("Ask about a role or a gap")},maxLines=3,modifier=Modifier.weight(1f),shape=RoundedCornerShape(16.dp))
                Button(onClick={send(input)},enabled=input.isNotBlank()){Text("Send")}
            }
        }
    }
}
@OptIn(ExperimentalMaterial3Api::class)
@Composable fun PracticeSheet(state:AppState,step:LearningStep,dismiss:()->Unit) {
    var notes by rememberSaveable(step.skill){mutableStateOf(state.evidenceFor(step.skill))}
    var error by remember{mutableStateOf("")}
    var confirmSkill by rememberSaveable(step.skill){mutableStateOf(false)}
    fun save(addSkill: Boolean) {
        if (state.recordStep(step.skill, notes, addToProfile = addSkill)) dismiss()
        else error = "Your profile is still loading. Please try again."
    }
    ModalBottomSheet(onDismissRequest=dismiss,sheetState=rememberModalBottomSheetState(skipPartiallyExpanded=true),containerColor=Paper) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(0.9f).imePadding()) {
            Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal=24.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
                TextButton(onClick=dismiss){Text("← Back to Growth")}
                StatusPill("${step.skill} · PRACTICE ACTIVITY",CoralSoft,OrangeInk)
                Heading(step.title,"About ${step.minutes} minutes · 25 XP on completion")
                InfoCard("Your task",step.brief,BrandSoft,BrandDeep)
                InfoCard("Show what you learned","Write a short reflection or paste a project link. Explain what you tried and how you checked the result.",Lavender,Plum)
                OutlinedTextField(notes,{notes=it;error=""},label={Text("My evidence / reflection")},minLines=4,maxLines=8,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(12.dp))
                if(error.isNotEmpty())Text(error,color=MaterialTheme.colorScheme.error)
                if(step.skill in state.completed)TextButton(onClick={state.undoStep(step.skill);dismiss()}){Text("Mark as not complete")}
                Spacer(Modifier.height(12.dp))
            }
            Surface(color=Paper) {
                Column(Modifier.fillMaxWidth().padding(horizontal=24.dp,vertical=12.dp)) {
                    Button(onClick={
                        if(notes.trim().length !in 20..2000) error="Add a reflection of 20 to 2000 characters."
                        else if(step.skill.lowercase() !in state.profile.skillSet()) confirmSkill=true
                        else save(false)
                    },modifier=Modifier.fillMaxWidth()){Text(if(step.skill in state.completed)"Save updated evidence" else "Mark practice complete")}
                    TextButton(onClick=dismiss,modifier=Modifier.fillMaxWidth()){Text("Close")}
                }
            }
        }
    }
    if (confirmSkill) AlertDialog(
        onDismissRequest={confirmSkill=false},
        title={Text("Add ${step.skill} to your profile?")},
        text={Text("Confirm you can use this skill. It will be saved as a skill you reported, and your job skills-match percentages will update. Your certificate is not verified here.")},
        confirmButton={TextButton(onClick={confirmSkill=false;save(true)}){Text("Add skill & complete")}},
        dismissButton={TextButton(onClick={confirmSkill=false;save(false)}){Text("Save progress only")}}
    )
}
