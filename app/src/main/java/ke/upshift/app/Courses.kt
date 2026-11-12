package ke.upshift.app

data class LearningCourse(val title:String,val provider:String,val url:String,val skills:Set<String>)
val CertificateCourses=listOf(
    LearningCourse("Google Data Analytics","Google · Coursera","https://www.coursera.org/professional-certificates/google-data-analytics",setOf("Excel","SQL","Python","Statistics")),
    LearningCourse("Meta Front-End Developer","Meta · Coursera","https://www.coursera.org/professional-certificates/meta-front-end-developer",setOf("HTML","CSS","JavaScript","Git")),
    LearningCourse("Meta Android Developer","Meta · Coursera","https://www.coursera.org/professional-certificates/meta-android-developer",setOf("Kotlin","Android","Testing","REST APIs")),
    LearningCourse("Google UX Design","Google · Coursera","https://www.coursera.org/professional-certificates/google-ux-design",setOf("Figma","Accessibility","Research")),
    LearningCourse("Google Digital Marketing & E-commerce","Google · Coursera","https://www.coursera.org/professional-certificates/google-digital-marketing-ecommerce",setOf("Writing","Canva")),
    LearningCourse("Google IT Support","Google · Coursera","https://www.coursera.org/professional-certificates/google-it-support",setOf("Networking","Communication"))
)
fun courseForSkill(skill:String)=CertificateCourses.first{skill in it.skills}
