package ke.upshift.app

internal const val MIN_SIGN_UP_PASSWORD_LENGTH = 12

internal fun signUpPasswordError(password: String, confirmation: String): String? = when {
    password.isBlank() -> "Enter your password."
    password.codePointCount(0, password.length) < MIN_SIGN_UP_PASSWORD_LENGTH ->
        "Choose a password with at least $MIN_SIGN_UP_PASSWORD_LENGTH characters."
    confirmation.isEmpty() -> "Confirm your password."
    password != confirmation -> "Passwords don't match."
    else -> null
}
