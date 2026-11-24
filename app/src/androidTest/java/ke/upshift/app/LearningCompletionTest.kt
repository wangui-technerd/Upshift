package ke.upshift.app

import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LearningCompletionTest {
    @get:Rule val ui = createAndroidComposeRule<MainActivity>()

    private fun complete(addSkill: Boolean) {
        assumeTrue("Use the isolated QA app.", BuildConfig.APPLICATION_ID.endsWith(".qa"))
        lateinit var state: AppState
        var dismissed = false
        val role = Role("learning-test", "Data intern", "Example", "Kenya", listOf("Python", "SQL"), "")
        ui.runOnUiThread {
            ui.activity.state.close()
            FirebaseBackend(ui.activity).signOut()
            ui.activity.getSharedPreferences("upshift", 0).edit().clear().commit()
            state = AppState(ui.activity, DemoOpportunitiesRepository())
            state.update(StudentProfile(name="Learning test", skills="Python"))
            state.flushProfile()
            ui.activity.setContent {
                MaterialTheme {
                    PracticeSheet(state, LearningLibrary.first { it.skill == "SQL" }) { dismissed = true }
                }
            }
        }
        ui.runOnIdle { assertEquals(50, state.score(role)) }
        ui.onNodeWithText("My evidence / reflection").performTextReplacement(
            "Completed the SQL course and practised joins on two related tables.")
        ui.onNodeWithText("Mark practice complete").performClick()
        ui.onNodeWithText("Add SQL to your profile?").assertExists()
        ui.onNodeWithText(if(addSkill) "Add skill & complete" else "Save progress only").performClick()
        ui.runOnIdle {
            assertTrue(dismissed)
            assertTrue("SQL" in state.completed)
            assertEquals(addSkill, "sql" in state.profile.skillSet())
            assertEquals(if(addSkill) 100 else 50, state.score(role))
            // Repeating completion never creates extra skills or XP.
            assertTrue(state.recordStep("SQL", state.evidenceFor("SQL"), addSkill))
            assertEquals(if(addSkill) 2 else 1, state.profile.skillSet().size)
            state.close()
            val restored = AppState(ui.activity, DemoOpportunitiesRepository())
            assertEquals(addSkill, "sql" in restored.profile.skillSet())
            assertTrue("SQL" in restored.completed)
            assertEquals(if(addSkill) 100 else 50, restored.score(role))
            restored.close()
        }
    }
    @Test fun addLearnedSkillUpdatesAndPersistsProfileAndPercentage() = complete(true)
    @Test fun progressOnlyKeepsProfileAndPercentageUnchanged() = complete(false)
}
