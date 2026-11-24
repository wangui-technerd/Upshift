package ke.upshift.app

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NavigationRefinementTest {
    @get:Rule val ui = createAndroidComposeRule<MainActivity>()
    private fun click(text:String) {
        if(ui.onAllNodesWithText(text).fetchSemanticsNodes().isEmpty()) {
            ui.onAllNodes(hasScrollToIndexAction()).onFirst().performScrollToNode(hasText(text))
        }
        ui.onNodeWithText(text).performClick()
    }
    @Test fun homeNavigationCoachAndCvActions() {
        val device = androidx.test.uiautomator.UiDevice.getInstance(androidx.test.platform.app.InstrumentationRegistry.getInstrumentation())
        device.wakeUp()
        device.executeShellCommand("wm dismiss-keyguard")
        ui.waitUntil(15000) { !ui.activity.state.restoring }
        ui.runOnIdle { ui.activity.state.enter() }
        ui.waitUntil(10000) { runCatching { ui.onAllNodesWithText("For you").fetchSemanticsNodes().isNotEmpty() }.getOrDefault(false) }
        ui.onNodeWithText("Get job recommendations").assertDoesNotExist()
        click("Growth");click("← Back")
        ui.onNodeWithText("Browse").assertExists()
        click("For you")
        ui.onNodeWithText("Back").performClick()
        ui.onNodeWithText("Browse").assertExists()
        click("You");click("Build my CV")
        ui.onNodeWithText("Build your CV").assertExists()
        ui.onNodeWithText("Print CV").assertDoesNotExist()
        click("← Back");click("← Back")
        ui.onNodeWithText("Browse").assertExists()
    }
}

