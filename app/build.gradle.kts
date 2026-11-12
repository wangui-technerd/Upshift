plugins { id("com.android.application"); id("org.jetbrains.kotlin.plugin.compose") }
layout.buildDirectory.set(file("${System.getProperty("java.io.tmpdir")}/upshift-build/${rootProject.projectDir.absolutePath.hashCode()}/app"))
android {
    namespace = "ke.upshift.app"
    compileSdk = 37
    defaultConfig { applicationId = "ke.upshift.app"; minSdk = 26; targetSdk = 37; versionCode = 1; versionName = "0.1.0" }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
        create("preview") {
            initWith(getByName("release"))
            signingConfig = signingConfigs.getByName("debug")
            versionNameSuffix = "-preview"
            matchingFallbacks += "release"
        }
        create("qa") {
            initWith(getByName("preview"))
            applicationIdSuffix = ".qa"
            versionNameSuffix = "-qa"
            matchingFallbacks += "release"
        }
    }
    buildFeatures { compose = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    testImplementation("junit:junit:4.13.2")
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.fragment:fragment-ktx:1.6.0")
    implementation("androidx.compose.material3:material3:1.3.2")
    implementation("androidx.compose.ui:ui-tooling-preview:1.7.8")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("androidx.core:core-splashscreen:1.0.1")
}
