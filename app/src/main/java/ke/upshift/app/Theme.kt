package ke.upshift.app

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.*
import androidx.compose.ui.unit.*

val Brand = Color(0xFF2E5AE8)
val BrandDeep = Color(0xFF1E3FB0)
val BrandSoft = Color(0xFFE8EDFC)
val Coral = Color(0xFFE0862E)
val CoralSoft = Color(0xFFFBEEDC)
val Paper = Color(0xFFF1F0EC)
val Ink = Color(0xFF15161B)
val Muted = Color(0xFF5D6068)
val Line = Color(0xFFE4E3DD)
@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
val Karla = FontFamily(Font(R.font.karla, loadingStrategy = FontLoadingStrategy.Async, variationSettings = FontVariation.Settings(FontVariation.weight(400))))
@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
val Fraunces = FontFamily(Font(R.font.fraunces, loadingStrategy = FontLoadingStrategy.Async, variationSettings = FontVariation.Settings(FontVariation.weight(500), FontVariation.opticalSizing(24.sp))))
@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
val FrauncesItalic = FontFamily(Font(R.font.fraunces_italic, style = FontStyle.Italic, loadingStrategy = FontLoadingStrategy.Async, variationSettings = FontVariation.Settings(FontVariation.weight(600), FontVariation.opticalSizing(24.sp))))
val UpshiftTypography = Typography(
    displaySmall = TextStyle(fontFamily = Fraunces, fontSize = 36.sp, lineHeight = 44.sp),
    headlineLarge = TextStyle(fontFamily = Fraunces, fontSize = 32.sp, lineHeight = 40.sp),
    headlineMedium = TextStyle(fontFamily = Fraunces, fontSize = 28.sp, lineHeight = 36.sp),
    headlineSmall = TextStyle(fontFamily = Fraunces, fontSize = 24.sp, lineHeight = 32.sp),
    titleLarge = TextStyle(fontFamily = Fraunces, fontSize = 21.sp, lineHeight = 28.sp),
    titleMedium = TextStyle(fontFamily = Karla, fontWeight = FontWeight.Bold, fontSize = 17.sp, lineHeight = 24.sp),
    titleSmall = TextStyle(fontFamily = Karla, fontWeight = FontWeight.Bold, fontSize = 15.sp, lineHeight = 22.sp),
    bodyLarge = TextStyle(fontFamily = Karla, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = Karla, fontSize = 15.sp, lineHeight = 22.sp),
    bodySmall = TextStyle(fontFamily = Karla, fontSize = 13.sp, lineHeight = 20.sp),
    labelLarge = TextStyle(fontFamily = Karla, fontWeight = FontWeight.Bold, fontSize = 15.sp, lineHeight = 22.sp),
    labelMedium = TextStyle(fontFamily = Karla, fontSize = 13.sp, lineHeight = 18.sp),
    labelSmall = TextStyle(fontFamily = Karla, fontSize = 12.sp, lineHeight = 16.sp)
)
@Composable fun UpshiftTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = lightColorScheme(primary = Brand, onPrimary = Color.White, primaryContainer = BrandSoft, onPrimaryContainer = BrandDeep,
        secondary = BrandDeep, secondaryContainer = CoralSoft, onSecondaryContainer = Color(0xFF754013), tertiary = Coral,
        background = Paper, onBackground = Ink, surface = Color.White, onSurface = Ink, surfaceVariant = BrandSoft,
        onSurfaceVariant = Muted, outline = Color(0xFF797B83), outlineVariant = Line, surfaceContainer = Paper,
        surfaceContainerHigh = Color.White, surfaceContainerLow = Color(0xFFF8F7F3)), typography = UpshiftTypography,
        shapes = Shapes(small = RoundedCornerShape(12.dp), medium = RoundedCornerShape(18.dp), large = RoundedCornerShape(24.dp)), content = content)
}
@Composable fun BrandMark(size: Dp = 28.dp, modifier: Modifier = Modifier) {
    Box(modifier.size(size).clip(RoundedCornerShape(topStartPercent = 50, topEndPercent = 50, bottomEndPercent = 50, bottomStartPercent = 12))
        .background(Brush.linearGradient(listOf(Coral, Brand))))
}
@Composable fun LaunchScreen() {
    Box(Modifier.fillMaxSize().background(Paper)) {
        Box(Modifier.offset((-70).dp, (-60).dp).size(280.dp).clip(CircleShape).background(BrandSoft))
        Box(Modifier.align(Alignment.BottomEnd).offset(65.dp, 60.dp).size(230.dp).clip(CircleShape).background(CoralSoft))
        Column(Modifier.align(Alignment.Center).padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            BrandMark(72.dp)
            Text("upshift", fontFamily = FrauncesItalic, fontStyle = FontStyle.Italic, fontSize = 36.sp, color = BrandDeep)
            Text("Your career copilot", color = Muted)
            Spacer(Modifier.height(12.dp))
            Box(Modifier.width(112.dp).height(3.dp).clip(CircleShape).background(Line)) {
                Box(Modifier.width(45.dp).fillMaxHeight().background(Coral))
            }
        }
    }
}
