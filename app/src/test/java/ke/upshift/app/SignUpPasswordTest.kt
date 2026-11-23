package ke.upshift.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class SignUpPasswordTest {
    @Test fun shortPasswordsAreRejected() {
        assertNotNull(signUpPasswordError("12345678901", "12345678901"))
    }

    @Test fun confirmationMustMatchExactly() {
        assertNotNull(signUpPasswordError("campus garden", ""))
        assertEquals("Passwords don't match.", signUpPasswordError("campus garden", "Campus garden"))
        assertNotNull(signUpPasswordError("campus garden ", "campus garden"))
    }

    @Test fun passphrasesAndTwelveCharacterPasswordsAreAccepted() {
        assertNull(signUpPasswordError("campus garden", "campus garden"))
        assertNull(signUpPasswordError("abcdefghijkl", "abcdefghijkl"))
    }
}
