package ke.upshift.app

import org.junit.Assert.*
import org.junit.Test

class CareerReplyTest {
    private val profile = StudentProfile(name="Amina", skills="Python", projects="Built an API")
    private val role = Role("one", "Python intern", "Example", "Nairobi", listOf("Python", "SQL"), "", eligibility=listOf("Current university student"))
    private fun reply(q:String) = careerReply(q,role,listOf("SQL"),50,profile)
    @Test fun differentCareerQuestionsDoNotReturnOneDefault() {
        val answers = listOf("Hi", "Help with my CV", "Am I eligible?", "How do I learn SQL?", "Explain my match", "Are certificates free?", "How do I apply?").map(::reply)
        assertEquals(answers.size, answers.toSet().size)
        assertTrue(reply("Am I eligible?").contains("Current university student"))
        assertTrue(reply("How do I learn SQL?").contains("join"))
        assertTrue(reply("Explain my match").contains("50%"))
        assertTrue(reply("Help with my CV").contains("PDF"))
    }
    @Test fun unknownQuestionsAreNotPresentedAsModelGeneratedAdvice() {
        assertTrue(reply("Write me a poem").contains("guided helper"))
        assertTrue(reply("Which jobs fit me?").contains("For you"))
        assertFalse(reply("this interface").startsWith("Hi "))
    }
    @Test fun missingProfileDoesNotInventAScore() {
        val answer=careerReply("Explain my match",null,emptyList(),null,StudentProfile())
        assertFalse(answer.contains("%"))
        assertTrue(answer.contains("Add your skills"))
    }
}
