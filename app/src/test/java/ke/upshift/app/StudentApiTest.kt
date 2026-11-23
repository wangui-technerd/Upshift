package ke.upshift.app

import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class StudentApiTest {
    @Test fun matchingEvidenceExcludesContactFields() {
        val profile = StudentProfile(
            name = "Fixture Name", email = "fixture@example.test", phone = "555-0100",
            education = "Computer science", skills = "Kotlin, SQL", projects = "Campus timetable",
            location = "Nairobi", goal = "Internship",
        )
        val text = profileRecommendationText(profile)
        for (unused in listOf(profile.name, profile.email, profile.phone, profile.location)) {
            assertFalse(text.contains(unused))
        }
        assertTrue(text.contains("Skills: Kotlin, SQL"))
        assertTrue(text.contains("Projects: Campus timetable"))
        assertFalse(hasRecommendationEvidence(StudentProfile(name = "Just a name", goal = "Internship")))
        assertTrue(hasRecommendationEvidence(profile))
    }

    @Test fun apiAddressAllowsEmulatorHttpOnlyInDebug() {
        assertEquals("http://10.0.2.2:8122/recommendations",
            apiAddress("http://10.0.2.2:8122/", "/recommendations", true).toString())
        assertEquals("https://api.example.test/v1/sentiment",
            apiAddress("https://api.example.test/v1", "/sentiment", false).toString())
        listOf("http://10.0.2.2:8122", "http://example.test", "https://user@api.example.test",
            "https://api.example.test?override=true").forEach {
            assertThrows(AiFailure::class.java) { apiAddress(it, "/recommendations", false) }
        }
        assertThrows(AiFailure::class.java) { apiAddress("http://example.test", "/sentiment", true) }
    }

    @Test fun applicationAddressesRequireServerApprovalAndHttps() {
        val official = "https://employer.example.test/jobs/intern?ref=student#apply"
        assertEquals(official, applicationAddress(official, true))
        assertNull(applicationAddress(official, false))
        assertNull(applicationAddress("https://user@employer.example.test/jobs/intern", true))
        assertNull(applicationAddress("javascript:alert(0)", true))
        assertNull(applicationAddress("http://example.test", true))
    }

    @Test fun unauthorizedResponseRefreshesTheTokenExactlyOnce() = runBlocking {
        val refreshes = mutableListOf<Boolean>()
        val tokens = mutableListOf<String>()
        val result = authorizedAiRequest(
            token = { refresh -> refreshes += refresh; if (refresh) "fresh" else "old" },
            send = { token -> tokens += token; AiHttpResult(401, "") },
        )
        assertEquals(listOf(false, true), refreshes)
        assertEquals(listOf("old", "fresh"), tokens)
        assertEquals(AiProblem.TOKEN_REJECTED, assertThrows(AiFailure::class.java) { requireAiSuccess(result) }.problem)
    }

    @Test fun successAndRoutineErrorsAreHandledSeparately() {
        assertEquals("result", requireAiSuccess(AiHttpResult(200, "result")))
        mapOf(403 to AiProblem.ACCESS_DENIED, 422 to AiProblem.INVALID_INPUT, 503 to AiProblem.SERVICE, 504 to AiProblem.TIMEOUT)
            .forEach { (status, problem) ->
                assertEquals(problem, assertThrows(AiFailure::class.java) {
                    requireAiSuccess(AiHttpResult(status, ""))
                }.problem)
            }
        val throttled = assertThrows(AiFailure::class.java) { requireAiSuccess(AiHttpResult(429, "", "30")) }
        assertEquals(AiProblem.RATE_LIMIT, throttled.problem)
        assertEquals(30L, throttled.retryAfterSeconds)
    }
}
