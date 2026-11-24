package ke.upshift.app

import android.app.Activity
import android.app.Instrumentation
import android.content.Intent
import android.net.Uri
import android.os.SystemClock
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.espresso.intent.Intents
import androidx.test.espresso.intent.Intents.intending
import androidx.test.espresso.intent.matcher.IntentMatchers.hasAction
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Until
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.junit.*
import org.junit.runner.RunWith
import org.junit.runners.MethodSorters
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** Actual emulator UI + Auth/Firestore + model API, using fictional test accounts.
 * Requires scripts.emulator_test_gateway on 8124; never run against production.
 */
@RunWith(AndroidJUnit4::class)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
class EmulatorJourneyTest {
    @get:Rule(order = 0) val workspace = object : org.junit.rules.ExternalResource() {
        override fun before() {
            Assume.assumeTrue("Local emulator build required", BuildConfig.FIREBASE_EMULATORS)
            InstrumentationRegistry.getInstrumentation().targetContext
                .getSharedPreferences("upshift-workspace",0).edit().putString("last","student").commit()
            runBlocking { withContext(Dispatchers.Main) {
                FirebaseBackend(InstrumentationRegistry.getInstrumentation().targetContext).signOut()
            } }
        }
    }
    @get:Rule(order = 1) val ui = createAndroidComposeRule<MainActivity>()
    private val password = "Fictional-test-2026!"
    private val device get() = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())

    @Before fun prepare() {
        Assume.assumeTrue("Local emulator build required", BuildConfig.FIREBASE_EMULATORS)
        check(BuildConfig.AI_BASE_URL == "http://10.0.2.2:8124") { "Use the local test gateway, not a live service." }
        device.executeShellCommand("svc wifi enable");device.executeShellCommand("svc data enable")
        awaitGateway()
        control("mode", JSONObject().put("mode", "normal"))
        ui.runOnUiThread {
            ui.activity.state.leave()
            ui.activity.getSharedPreferences("upshift-workspace", 0).edit().putString("last", "student").commit()
        }
        ui.activityRule.scenario.recreate()
        waitText("Get started")
    }

    @After fun restore() {
        runCatching { control("mode", JSONObject().put("mode", "normal")) }
    }

    private fun waitText(text: String, substring: Boolean = false, timeout: Long = 35_000) {
        ui.waitUntil(timeout) { ui.onAllNodesWithText(text, substring = substring).fetchSemanticsNodes().isNotEmpty() }
    }
    private fun reveal(text: String, substring: Boolean = false): SemanticsNodeInteraction {
        val matcher = hasText(text, substring = substring)
        if (ui.onAllNodes(matcher).fetchSemanticsNodes().isEmpty()) {
            if (ui.onAllNodes(hasScrollToIndexAction()).fetchSemanticsNodes().isNotEmpty()) {
                ui.onAllNodes(hasScrollToIndexAction()).onFirst().performScrollToNode(matcher)
            } else waitText(text, substring)
        }
        return ui.onAllNodes(matcher).onFirst().also { runCatching { it.performScrollTo() } }
    }
    private fun click(text: String, substring: Boolean = false) { reveal(text, substring).performClick() }
    private fun fill(label: String, value: String) {
        ui.onNode(hasSetTextAction() and hasText(label)).performScrollTo().performClick().performTextReplacement(value)
        ui.runOnUiThread {
            androidx.core.view.WindowInsetsControllerCompat(ui.activity.window,ui.activity.window.decorView)
                .hide(androidx.core.view.WindowInsetsCompat.Type.ime())
        }
        ui.waitForIdle()
    }
    private fun menu(text: String) {
        ui.onNodeWithContentDescription("Open menu").performClick(); click(text)
    }
    private fun email() = "ui-${System.currentTimeMillis()}@example.test"
    private fun awaitGateway() {
        val until=SystemClock.elapsedRealtime()+20_000
        while (true) {
            try { control("mode",JSONObject().put("mode","normal"));return }
            catch (e:Exception) { if(SystemClock.elapsedRealtime()>until)throw e;SystemClock.sleep(300) }
        }
    }
    private fun signedIn(): String {
        val email=email()
        runBlocking { withContext(Dispatchers.Main) {
            val state=ui.activity.state
            check(state.backend.signUp("Amina Test", email, password) == AccountResult.Success)
            check(state.connectAccount("Amina Test"))
            state.update(state.profile.copy(name="Amina Test",education="Year 3 Computer Science",skills="Python, SQL",location="Nairobi",projects="Built a Python API and SQL project."))
            state.enter()
        } }
        waitText("Get job recommendations")
        return email
    }
    private fun control(path: String, body: JSONObject): JSONObject {
        check(BuildConfig.FIREBASE_EMULATORS)
        val c=URL("http://10.0.2.2:8124/__test__/$path").openConnection() as HttpURLConnection
        try {
            c.requestMethod="POST"; c.connectTimeout=5000;c.readTimeout=30000;c.doOutput=true
            c.setRequestProperty("Content-Type","application/json")
            c.outputStream.use { it.write(body.toString().toByteArray()) }
            check(c.responseCode in 200..299) { "Test fixture failed: ${c.responseCode}" }
            return JSONObject(c.inputStream.bufferedReader().readText())
        } finally { c.disconnect() }
    }

    @Test fun a_authenticationOnboardingAndPersistence() {
        click("Get started"); click("Skip")
        click("Create account"); waitText("Enter your name.")
        fill("Full name","Amina Test"); fill("Email address","invalid")
        click("Create account");waitText("Enter a valid email address.")
        val email=email();fill("Email address",email);fill("Password",password)
        click("Create account");waitText("Let’s start with you")
        fill("Education / programme","Year 3 Computer Science");fill("Location","Nairobi")
        click("Continue");waitText("What can you do today?")
        fill("Other skills, separated by commas","Python, SQL")
        click("Continue");click("See my matches");waitText("Get job recommendations")
        val uid=ui.activity.state.userId!!
        ui.activityRule.scenario.recreate();waitText("Get job recommendations")
        Assert.assertEquals("Python, SQL",ui.activity.state.profile.skills)
        val persisted=runBlocking { ui.activity.state.backend.loadUser(uid) }
        Assert.assertEquals("Python, SQL",(persisted["profile"] as Map<*,*>)["skills"])
        menu("Sign out");waitText("Get started")
        click("Log in");fill("Email address",email);fill("Password","Wrong-password-2026")
        click("Log in");waitText("Could not authenticate.",substring=true)
        fill("Password",password);click("Log in");waitText("Get job recommendations")
        menu("Sign out");click("Log in");click("Forgot password?")
        fill("Email address",email);click("Send reset link")
        waitText("If an account exists",substring=true)
    }

    @Test fun b_realRecommendationsLinksAndFeedback() {
        signedIn();click("Get job recommendations")
        fill("Experience in months (optional)","1201")
        reveal("Find jobs").assertIsNotEnabled()
        fill("Experience in months (optional)","6")
        val start=SystemClock.elapsedRealtime();click("Find jobs")
        waitText("Python Software Intern (Demo)")
        println("UPSHIFT_TIMING recommendations_ms=${SystemClock.elapsedRealtime()-start}")
        ui.activityRule.scenario.recreate();waitText("Python Software Intern (Demo)")
        reveal("Required skills your profile doesn’t mention").assertExists()
        reveal("Docker",substring=true).assertExists()
        Intents.init()
        try {
            intending(hasAction(Intent.ACTION_VIEW)).respondWith(Instrumentation.ActivityResult(Activity.RESULT_OK,null))
            click("Open application")
            Assert.assertTrue(Intents.getIntents().any { it.dataString=="https://example.org/?upshift-demo=apply" })
        } finally { Intents.release() }
        click("Back");menu("Feedback")
        fill("Feedback about UpShift","The app is helpful and clear.")
        click("Analyse feedback");waitText("Feedback sentiment:",substring=true)
        val before=ui.activity.state.profile
        ui.activityRule.scenario.recreate();waitText("Feedback about UpShift")
        waitText("Feedback sentiment:",substring=true)
        Assert.assertEquals(before,ui.activity.state.profile)
    }

    @Test fun c_errorsSlowResponsesAndRetry() {
        signedIn();click("Get job recommendations");fill("Experience in months (optional)","6")
        control("mode",JSONObject().put("mode","empty"));click("Find jobs")
        waitText("No active vacancies match your profile and filters.")
        control("mode",JSONObject().put("mode","unavailable"));click("Find jobs")
        waitText("The recommendations service is temporarily unavailable. Try again later.")
        control("mode",JSONObject().put("mode","normal"));click("Retry recommendations")
        waitText("Python Software Intern (Demo)")
        control("mode",JSONObject().put("mode","slow"));click("Find jobs")
        waitText("Still looking for vacancies.",substring=true);waitText("Python Software Intern (Demo)")
        control("mode",JSONObject().put("mode","timeout"));click("Find jobs")
        waitText("The server took too long. Try again.")
        control("mode",JSONObject().put("mode","unauthorized"));click("Retry recommendations")
        waitText("The backend couldn't verify your sign-in.",substring=true)
        reveal("Sign in again").assertExists()
        Assert.assertEquals("Python, SQL",ui.activity.state.profile.skills)
        control("mode",JSONObject().put("mode","normal"));click("Retry recommendations")
        waitText("Python Software Intern (Demo)")
        try {
            device.executeShellCommand("cmd connectivity airplane-mode enable")
            device.executeShellCommand("svc wifi disable");device.executeShellCommand("svc data disable")
            click("Find jobs")
            ui.waitUntil(60_000) {
                ui.onAllNodesWithText("Couldn’t reach the backend.",substring=true).fetchSemanticsNodes().isNotEmpty() ||
                    ui.onAllNodesWithText("The server took too long. Try again.").fetchSemanticsNodes().isNotEmpty()
            }
        } finally {
            device.executeShellCommand("cmd connectivity airplane-mode disable")
            device.executeShellCommand("svc wifi enable");device.executeShellCommand("svc data enable")
            awaitGateway()
        }
        Assert.assertEquals("6",ui.onNode(hasSetTextAction() and hasText("Experience in months (optional)")).fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text)
    }

    @Test fun d_savedGrowthCoachAndPdf() {
        signedIn()
        ui.waitUntil(15_000) { ui.activity.state.roles.any {it.id=="member3-demo-python-internship"} }
        reveal("Python Software Intern (Demo)").performClick()
        reveal("Who can apply").assertExists()
        click("Save this role");Assert.assertTrue("member3-demo-python-internship" in ui.activity.state.saved)
        click("Build my growth path");waitText("Your growth path")
        Intents.init()
        try {
            intending(hasAction(Intent.ACTION_VIEW)).respondWith(Instrumentation.ActivityResult(Activity.RESULT_OK,null))
            click("View programme ↗")
            Assert.assertTrue(Intents.getIntents().any { it.dataString?.contains("coursera.org")==true })
        } finally {Intents.release()}
        click("Record my learning · Git");click("Mark practice complete")
        waitText("Add a reflection of 20 to 2000 characters.")
        fill("My evidence / reflection","Created a Git branch, committed changes and reviewed the diff in a fictional practice project.")
        click("Mark practice complete");ui.waitUntil {ui.activity.state.xp()==25}
        Assert.assertEquals(1,ui.activity.state.streak())
        Assert.assertEquals("Python, SQL",ui.activity.state.profile.skills)
        ui.onNodeWithContentDescription("Open your coach").performClick();waitText("Your coach ✦")
        click("Close")
        click("You");click("Build my CV")
        val longProject="Built a Python project with SQL queries and wrote tests to verify the results. ".repeat(90)
        fill("Projects and achievements",longProject)
        click("Preview my CV");waitText("Your CV preview")
        val pdf=File(ui.activity.cacheDir,"fictional-ui-test-cv.pdf")
        Intents.init()
        try {
            intending(hasAction(Intent.ACTION_CREATE_DOCUMENT)).respondWith(Instrumentation.ActivityResult(Activity.RESULT_OK,Intent().setData(Uri.fromFile(pdf))))
            click("Save CV as PDF");waitText("CV saved as PDF.")
            Assert.assertTrue(pdf.length()>1000)
            android.graphics.pdf.PdfRenderer(android.os.ParcelFileDescriptor.open(pdf,android.os.ParcelFileDescriptor.MODE_READ_ONLY)).use {Assert.assertTrue(it.pageCount>=2)}
        } finally {Intents.release()}
        click("← Edit CV");ui.activityRule.scenario.recreate()
        ui.onNode(hasSetTextAction() and hasText("Projects and achievements")).assertExists()
        Assert.assertEquals(longProject.trim(),ui.activity.state.profile.projects.trim())
    }

    @Test fun a0_recruiterRegistrationDraftApprovalPublishWithdraw() {
        signedIn();menu("Company workspace");waitText("Company name")
        fill("Company name","Fictional UI Test Employer")
        fill("Company website · https://","https://example.org")
        fill("About your company","Fictional company for local emulator testing only.")
        click("Submit company for review");waitText("Company submitted for review.")
        click("Overview");click("Create an opportunity")
        fill("Role title","Python UI Test Internship");fill("Location","Nairobi")
        fill("Describe the role","Build Python APIs and learn SQL with a mentor in this fictional internship.")
        fill("Skills · comma separated","Python, SQL, Git")
        fill("Requirements · one per line","Python and SQL are required.")
        fill("Who can apply? · one condition per line","Current computing students in Kenya.")
        fill("Official advert URL · https://","https://example.org/ui-test-${System.currentTimeMillis()}")
        fill("Application URL · optional","https://example.org/ui-apply")
        fill("Closing date · YYYY-MM-DD · optional",java.time.LocalDate.now().plusDays(14).toString())
        reveal("Submit for review").assertIsNotEnabled()
        click("Save draft on this device");waitText("Draft saved on this device.",substring=true)
        click("← All opportunities");click("Continue draft on this device")
        ui.onNode(hasSetTextAction() and hasText("Role title")).assertTextContains("Python UI Test Internship")
        val client=RecruiterClient(ui.activity.state.backend)
        val company=runBlocking {client.companies().first()}
        control("approve",JSONObject().put("company_id",company.id))
        click("← All opportunities");click("Company");click("Refresh approval status")
        waitText("Your company can submit vacancies.",substring=true)
        click("Overview");click("Continue draft on this device");click("Submit for review")
        waitText("Changes saved.",substring=true)
        val submission=runBlocking {client.vacancies().first()}
        control("approve",JSONObject().put("submission_id",submission.id).put("revision",submission.revision))
        Assert.assertTrue("Published vacancy is returned through the Android recommendation client",
            runBlocking { AiClient(ui.activity.state.backend).recommendations(ui.activity.state.profile,"Nairobi",6) }
                .any { it.id==submission.id })
        // Reload through the visible workspace control before withdrawal.
        device.pressBack();click("Company");click("Refresh approval status");click("Vacancies")
        click("Python UI Test Internship");click("Withdraw vacancy");click("Withdraw")
        waitText("Vacancy withdrawn.")
        Assert.assertEquals("closed",runBlocking {client.vacancies().first().status})
        Assert.assertTrue("Withdrawn vacancy is excluded by the next Android recommendation request",
            runBlocking { AiClient(ui.activity.state.backend).recommendations(ui.activity.state.profile,"Nairobi",6) }
                .none { it.id==submission.id })
    }

    @Test fun f_largeTextRotationAndActualDocumentPicker() {
        signedIn()
        val previous=device.executeShellCommand("settings get system font_scale").trim().toFloatOrNull() ?: 1f
        try {
            device.executeShellCommand("settings put system font_scale 1.3")
            ui.waitUntil(10_000) { ui.activity.resources.configuration.fontScale >= 1.29f }
            ui.activityRule.scenario.recreate()
            waitText("Get job recommendations")
            click("You");click("Build my CV")
            fill("Projects and achievements","Created Python and SQL projects with tests. ".repeat(45))
            click("Preview my CV");waitText("Your CV preview")
            device.setOrientationLeft();waitText("Your CV preview")
            device.setOrientationNatural();waitText("Your CV preview")
            click("Save CV as PDF")
            Assert.assertTrue(device.wait(Until.hasObject(By.pkg("com.google.android.documentsui")),15_000))
            val name="Upshift-fictional-ui-${System.currentTimeMillis()}.pdf"
            val filename=device.wait(Until.findObject(By.clazz("android.widget.EditText")),10_000)
            Assert.assertNotNull("Document picker filename field",filename)
            filename.text=name
            val save=device.wait(Until.findObject(By.text(java.util.regex.Pattern.compile("(?i)save"))),10_000)
            Assert.assertNotNull("Document picker Save button",save)
            save.click()
            waitText("CV saved as PDF.")
        } finally {
            device.unfreezeRotation()
            device.executeShellCommand("settings put system font_scale $previous")
        }
    }
}
