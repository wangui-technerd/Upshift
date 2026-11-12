package ke.upshift.app

import android.content.Context
import android.print.*
import android.os.*
import android.graphics.*
import android.graphics.pdf.PdfDocument
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import java.io.OutputStream

fun cvSections(p:StudentProfile)=listOf("PROFILE" to p.summary,"EDUCATION" to p.education,"SKILLS" to p.skills,"PROJECTS" to p.projects,"EXPERIENCE & VOLUNTEERING" to p.experience).filter{it.second.isNotBlank()}
@Composable fun CvScreen(state:AppState,preview:Boolean,setPreview:(Boolean)->Unit,back:()->Unit) {
    val context=LocalContext.current
    val scope=rememberCoroutineScope()
    var error by remember{mutableStateOf("")}
    var status by remember{mutableStateOf("")}
    var saving by remember{mutableStateOf(false)}
    var pendingProfile by remember{mutableStateOf<StudentProfile?>(null)}
    val savePdf=rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/pdf")){uri->
        val profile=pendingProfile
        if(uri!=null && profile!=null)scope.launch {
            saving=true;status="";error=""
            try {
                withContext(Dispatchers.IO){context.contentResolver.openOutputStream(uri,"w")?.use{writeCvPdf(profile,it)} ?: error("Cannot open the selected file")}
                status="CV saved as PDF."
            } catch(_:Exception){error="Could not save the PDF. Please choose a location and try again."}
            finally{saving=false;pendingProfile=null}
        }
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
        TextButton(onClick={if(preview)setPreview(false)else back()}){Text(if(preview)"← Edit CV" else "← Back")}
        Heading(if(preview)"Your CV preview" else "Build your CV",if(preview)"Review your details before saving." else "Fill in your details. Empty optional sections will be left out.")
        if(!preview){
            ProfileFields(state)
            if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
            Button(onClick={
                val p=state.profile
                error=when{p.name.isBlank()->"Enter your name.";!android.util.Patterns.EMAIL_ADDRESS.matcher(p.email).matches()->"Enter a valid email address.";p.education.isBlank()->"Add your education.";else->""}
                if(error.isEmpty())setPreview(true)
            },modifier=Modifier.fillMaxWidth()){Text("Preview my CV")}
        }else{
            Surface(color=androidx.compose.ui.graphics.Color.White,modifier=Modifier.fillMaxWidth()){
                Column(Modifier.padding(24.dp),verticalArrangement=Arrangement.spacedBy(16.dp)){
                    Text(state.profile.name,style=MaterialTheme.typography.headlineSmall)
                    Text(listOf(state.profile.location,state.profile.email,state.profile.phone).filter{it.isNotBlank()}.joinToString(" · "))
                    cvSections(state.profile).forEach{(title,body)->Text(title,style=MaterialTheme.typography.titleSmall);Text(body)}
                }
            }
            if(status.isNotBlank())InfoCard("Saved",status,Mint,Teal)
            if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
            Button(enabled=!saving,onClick={pendingProfile=state.profile;savePdf.launch("Upshift-CV.pdf")},modifier=Modifier.fillMaxWidth()){Text(if(saving)"Saving…" else "Save CV as PDF")}
            OutlinedButton(onClick={val manager=context.getSystemService(Context.PRINT_SERVICE)as PrintManager;manager.print("Upshift CV",CvPrintAdapter(state.profile),PrintAttributes.Builder().setMediaSize(PrintAttributes.MediaSize.ISO_A4).build())},modifier=Modifier.fillMaxWidth()){Text("Print CV")}
        }
        Spacer(Modifier.height(24.dp))
    }
}
private data class CvLine(val text:String,val y:Float,val size:Float,val bold:Boolean)
private fun cvPages(profile:StudentProfile):List<List<CvLine>> {
    val pages=mutableListOf<MutableList<CvLine>>(mutableListOf())
    val paint=Paint(Paint.ANTI_ALIAS_FLAG)
    var y=56f
    fun nextPage(){pages.add(mutableListOf());y=56f}
    fun line(value:String,size:Float=11f,bold:Boolean=false){
        paint.textSize=size;paint.typeface=if(bold)Typeface.DEFAULT_BOLD else Typeface.DEFAULT
        value.replace("\r\n","\n").split('\n').forEach{paragraph->
            var remaining=paragraph
            if(remaining.isBlank()){y+=15f;if(y>780)nextPage()}
            while(remaining.isNotEmpty()){
                var count=paint.breakText(remaining,true,491f,null).coerceAtLeast(1)
                if(count<remaining.length){val space=remaining.lastIndexOf(' ',count-1);if(space>0)count=space}
                if(y+size>780)nextPage()
                pages.last().add(CvLine(remaining.take(count),y,size,bold));y+=size+6f
                remaining=remaining.drop(count).trimStart()
            }
        }
    }
    line(profile.name,22f,true)
    line(listOf(profile.location,profile.email,profile.phone).filter{it.isNotBlank()}.joinToString(" | "))
    cvSections(profile).forEach{(title,body)->if(y+64>780)nextPage()else y+=18;line(title,12f,true);line(body)}
    return pages.filter{it.isNotEmpty()}
}
fun writeCvPdf(profile:StudentProfile,output:OutputStream,ranges:Array<out PageRange> = arrayOf(PageRange.ALL_PAGES),signal:CancellationSignal?=null):Int {
    val pages=cvPages(profile)
    val pdf=PdfDocument()
    try {
        val paint=Paint(Paint.ANTI_ALIAS_FLAG).apply{color=Color.BLACK}
        pages.forEachIndexed{index,lines->
            if(signal?.isCanceled==true)throw java.util.concurrent.CancellationException()
            if(ranges.none{index in it.start..it.end})return@forEachIndexed
            val page=pdf.startPage(PdfDocument.PageInfo.Builder(595,842,index+1).create())
            lines.forEach{line->paint.textSize=line.size;paint.typeface=if(line.bold)Typeface.DEFAULT_BOLD else Typeface.DEFAULT;page.canvas.drawText(line.text,52f,line.y,paint)}
            paint.textSize=9f;paint.typeface=Typeface.DEFAULT;paint.color=Color.GRAY
            page.canvas.drawText("${index+1}",535f,814f,paint);paint.color=Color.BLACK
            pdf.finishPage(page)
        }
        pdf.writeTo(output)
    }finally{pdf.close()}
    return pages.size
}
class CvPrintAdapter(private val profile:StudentProfile):PrintDocumentAdapter(){
    private val scope=CoroutineScope(SupervisorJob()+Dispatchers.IO)
    override fun onLayout(old:PrintAttributes?,new:PrintAttributes?,signal:CancellationSignal,callback:LayoutResultCallback,extras:Bundle?){
        if(signal.isCanceled)callback.onLayoutCancelled()else callback.onLayoutFinished(PrintDocumentInfo.Builder("Upshift-CV.pdf").setContentType(PrintDocumentInfo.CONTENT_TYPE_DOCUMENT).setPageCount(cvPages(profile).size).build(),true)
    }
    override fun onWrite(ranges:Array<out PageRange>,destination:ParcelFileDescriptor,signal:CancellationSignal,callback:WriteResultCallback){
        scope.launch{
            try{
                java.io.FileOutputStream(destination.fileDescriptor).use{writeCvPdf(profile,it,ranges,signal)}
                withContext(Dispatchers.Main){callback.onWriteFinished(ranges)}
            }catch(_:java.util.concurrent.CancellationException){withContext(Dispatchers.Main){callback.onWriteCancelled()}}
            catch(_:Exception){withContext(Dispatchers.Main){callback.onWriteFailed("Could not export CV. Please try again.")}}
        }
    }
    override fun onFinish(){scope.cancel();super.onFinish()}
}
