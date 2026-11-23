package ke.upshift.app

import org.junit.Assert.*
import org.junit.Test

class RecruiterValidationTest {
    @Test fun sourceLinksRejectCredentialsAndNonHttpsSchemes() {
        assertTrue(recruiterHttps("https://company.example/careers/intern"))
        listOf("javascript:alert(1)","http://company.example","https://user:secret@company.example", "https://company.example:9000", "https:///missing-host").forEach { assertFalse(recruiterHttps(it)) }
    }
    @Test fun statusLabelsDoNotTreatUnknownStateAsApproved() {
        assertEquals("In review",recruiterStatus("pending"))
        assertEquals("Changes requested",recruiterStatus("rejected"))
        assertEquals("Unconfirmed",recruiterStatus("arbitrary"))
    }
    @Test fun invalidDraftIsRejectedBeforeCreatingSubmission() {
        val draft=mapOf("title" to "Software intern","location" to "Nairobi","description" to "Build and test software with an experienced mentor.","source_url" to "javascript:alert(1)","career_level" to "internship")
        try { recruiterPayload(draft);fail("Unsafe source URL accepted") } catch(expected:IllegalArgumentException) { assertTrue(expected.message.orEmpty().contains("https://")) }
    }
}
