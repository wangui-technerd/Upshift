package ke.upshift.app

import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class MatchingProgressTest {
    private val scorer=SkillCoverageScorer()
    private fun role(skills:List<String>)=Role("test","Test role","Example","Kenya",skills,"")
    @Test fun rankingUsesCoverageRatherThanNumberOfSkills() {
        val profile=StudentProfile(skills="HTML, CSS, Git, Kotlin")
        val focused=role(listOf("HTML","CSS","Git","JavaScript"))
        val broad=role(listOf("HTML","CSS","Git","Kotlin","SQL","Python","Figma","Testing"))
        assertEquals(75,scorer.percentage(focused,profile))
        assertEquals(50,scorer.percentage(broad,profile))
        assertTrue(scorer.percentage(focused,profile)!! > scorer.percentage(broad,profile)!!)
    }
    @Test fun emptyProfileHasNoInventedPercentage() { assertNull(scorer.percentage(role(listOf("Git")),StudentProfile())) }
    @Test fun duplicateAndCaseVariantSkillsDoNotInflateScore() { assertEquals(50,scorer.percentage(role(listOf("Git","Kotlin")),StudentProfile(skills="Git, git, GIT"))) }
    @Test fun roleWithoutRequirementsHasNoPercentage() { assertNull(scorer.percentage(role(emptyList()),StudentProfile(skills="Git"))) }
    @Test fun streakContinuesUntilTodayEnds() {
        val today=LocalDate.of(2026,11,10)
        assertEquals(2,learningStreak(setOf(today.minusDays(1),today.minusDays(2)),today))
        assertEquals(3,learningStreak(setOf(today,today.minusDays(1),today.minusDays(2)),today))
    }
    @Test fun missingADayBreaksStreak() {
        val today=LocalDate.of(2026,11,10)
        assertEquals(0,learningStreak(setOf(today.minusDays(2)),today))
        assertEquals(1,learningStreak(setOf(today,today.minusDays(2)),today))
    }

    @Test fun everyLearningSkillHasAProviderProgramme() {
        LearningLibrary.forEach { step ->
            val course=courseForSkill(step.skill)
            assertTrue(course.url.startsWith("https://www.coursera.org/professional-certificates/"))
            assertTrue(step.skill in course.skills)
        }
    }
    @Test fun editedProfileDoesNotKeepOldCachedSkills() {
        val original=StudentProfile(skills="Git")
        assertEquals(setOf("git"),original.skillSet())
        val edited=original.copy(skills="Kotlin")
        assertEquals(setOf("kotlin"),edited.skillSet())
    }
    @Test fun addingLearnedSkillUpdatesCoverageAndKeepsProfileDetails() {
        val original = StudentProfile(name="Student", skills="Python", projects="A data project")
        val updated = original.withSkill("SQL")
        val job = role(listOf("Python", "SQL"))
        assertEquals(50, scorer.percentage(job, original))
        assertEquals(100, scorer.percentage(job, updated))
        assertEquals(original.name, updated.name)
        assertEquals(original.projects, updated.projects)
        assertEquals(setOf("python", "sql"), updated.skillSet())
    }
    @Test fun repeatedCourseCompletionCannotDuplicateSkillOrInflatePercentage() {
        val original = StudentProfile(skills="Python, SQL")
        assertEquals(original, original.withSkill(" sql "))
        assertEquals(original, original.withSkill(""))
        assertEquals(100, scorer.percentage(role(listOf("Python", "SQL")), original.withSkill("SQL")))
    }
}
