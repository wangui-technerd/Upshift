plugins { id("com.android.application"); id("org.jetbrains.kotlin.plugin.compose") }
// Missing project configuration keeps guest use available, with an explicit auth error.
if (file("google-services.json").exists()) apply(plugin = "com.google.gms.google-services")
val firebaseEmulators = providers.gradleProperty("firebaseEmulators").orNull == "true"
layout.buildDirectory.set(file("${System.getProperty("java.io.tmpdir")}/upshift-build/${rootProject.projectDir.absolutePath.hashCode()}/app"))
android {
    namespace = "ke.upshift.app"
    compileSdk = 37
    defaultConfig { applicationId = "ke.upshift.app"; minSdk = 26; targetSdk = 37; versionCode = 1; versionName = "0.1.0" }
    defaultConfig {
        buildConfigField("boolean", "FIREBASE_EMULATORS", "false")
        buildConfigField("String", "AI_BASE_URL", "\"${providers.gradleProperty("aiBaseUrl").orNull ?: ""}\"")
    }
    buildTypes {
        getByName("debug") { buildConfigField("boolean", "FIREBASE_EMULATORS", firebaseEmulators.toString()) }
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
    buildFeatures { compose = true; buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies {
    // Keep Firebase on the Kotlin 2.2-compatible SDK line used by this build.
    implementation(platform("com.google.firebase:firebase-bom:34.0.0"))
    implementation("com.google.firebase:firebase-auth")
    implementation("com.google.firebase:firebase-firestore")
    implementation("androidx.credentials:credentials:1.3.0")
    implementation("androidx.credentials:credentials-play-services-auth:1.3.0")
    implementation("com.google.android.libraries.identity.googleid:googleid:1.1.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.10.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.9.4")
    testImplementation("junit:junit:4.13.2")
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.fragment:fragment-ktx:1.6.0")
    implementation("androidx.compose.material3:material3:1.3.2")
    implementation("androidx.compose.ui:ui-tooling-preview:1.7.8")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("androidx.core:core-splashscreen:1.0.1")
}
