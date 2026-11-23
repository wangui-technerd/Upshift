"""Validate client ID tokens with Firebase Admin; never accept a client-supplied UID."""
import os
import threading
from .errors import Problem


class FirebaseTokenVerifier:
    def __init__(self):
        self.project_id = os.getenv('UPSHIFT_FIREBASE_PROJECT_ID', '')
        self.configured = bool(self.project_id)
        self.lock = threading.Lock()
        self.app = None

    def verify(self, token):
        return self.verify_claims(token)['uid']

    def verify_claims(self, token):
        if not self.configured:
            raise Problem(503, 'auth_unavailable', 'Configure the Firebase project for the AI service.')
        emulator = os.getenv('FIREBASE_AUTH_EMULATOR_HOST')
        if emulator and (not self.project_id.startswith('demo-') or emulator not in ('127.0.0.1:9099', 'localhost:9099')):
            raise Problem(503, 'auth_unavailable', 'Auth emulator mode is restricted to local demo projects.')
        try:
            import firebase_admin
            from firebase_admin import auth
        except ImportError:
            raise Problem(503, 'auth_unavailable', 'Firebase Admin dependencies are not installed.')
        try:
            with self.lock:
                if self.app is None:
                    self.app = firebase_admin.initialize_app(options={'projectId': self.project_id}, name='upshift-ai-' + self.project_id)
        except (ValueError, OSError):
            raise Problem(503, 'auth_unavailable', 'Firebase Admin credentials could not be initialized.')
        try:
            decoded = auth.verify_id_token(token, app=self.app, check_revoked=not bool(emulator))
            uid = decoded.get('uid')
            if not isinstance(uid, str) or not uid:
                raise ValueError('Missing UID')
            return decoded
        except (auth.CertificateFetchError, auth.UserNotFoundError) as error:
            if isinstance(error, auth.UserNotFoundError):
                raise Problem(401, 'unauthorized', 'Sign in again to continue.')
            raise Problem(503, 'auth_unavailable', 'Firebase verification is temporarily unavailable.')
        except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, ValueError):
            raise Problem(401, 'unauthorized', 'Sign in again to continue.')
        except Exception:
            raise Problem(503, 'auth_unavailable', 'Firebase verification is temporarily unavailable.')
