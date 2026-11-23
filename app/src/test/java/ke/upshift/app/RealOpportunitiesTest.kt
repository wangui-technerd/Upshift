package ke.upshift.app

import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class RealOpportunitiesTest {
    private val today = LocalDate.of(2026, 11, 13)
    private fun role(status: String = "needs_primary_review", deadline: String = "") =
        Role("sourced-one", "Intern", "Employer", "Kenya", emptyList(), "Summary",
            sourceUrl = "https://example.org/jobs/one", availabilityStatus = status, deadline = deadline)

    @Test fun closedAndUnresolvedAdvertsAreHidden() {
        listOf("archived", "availability_unverified", "unconfirmed", "").forEach {
            assertFalse(role(it).isDiscoverable(today))
        }
        assertTrue(role().isDiscoverable(today))
    }
    @Test fun deadlinesRemainVisibleThroughClosingDay() {
        assertFalse(role(deadline = "2026-11-12").isDiscoverable(today))
        assertTrue(role(deadline = "2026-11-13").isDiscoverable(today))
        assertTrue(role(deadline = "2026-11-14T07:59:00+03:00").isDiscoverable(today))
        assertFalse(role(deadline = "not-a-date").isDiscoverable(today))
    }
    @Test fun invalidAndMissingSourcesAreHidden() {
        listOf("", "javascript:alert(1)", "https:///job", "https://user@example.org/job").forEach {
            assertFalse(role().copy(sourceUrl = it).isDiscoverable(today))
        }
    }
    @Test fun emptyCloudKeepsBundleAndWithdrawalOverridesIt() {
        val bundled = listOf(role())
        assertEquals(bundled, mergeOpportunities(bundled, emptyList(), today))
        assertTrue(mergeOpportunities(bundled, listOf(role("archived")), today).isEmpty())
        val updated = role().copy(title = "Updated title")
        assertEquals(listOf(updated), mergeOpportunities(bundled, listOf(updated), today))
    }
    @Test fun differentCloudIdCanReplaceAndWithdrawResearchCopy() {
        val bundled = role()
        val cloud = bundled.copy(id="partner-id", availabilityStatus="published")
        assertEquals(listOf(cloud), mergeOpportunities(listOf(bundled), listOf(cloud), today))
        assertTrue(mergeOpportunities(listOf(bundled), listOf(cloud.copy(availabilityStatus="archived")), today).isEmpty())
        assertFalse(cloud.copy(availabilityStatus="pending_review").isDiscoverable(today))
    }
    @Test fun missingRequirementsDoNotInventStudentEligibility() {
        val parsed = roleFromFields("one", mapOf("title" to "Intern", "company" to "Employer"))!!
        assertTrue(parsed.requirements.isEmpty())
        assertTrue(parsed.responsibilities.isEmpty())
        assertEquals(listOf("Eligibility is unconfirmed. Check the source advert."), parsed.eligibility)
        assertFalse(parsed.isDiscoverable(today))
    }
}
