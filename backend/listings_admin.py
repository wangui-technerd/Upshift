"""Trusted operator tool. Never exposes a self-service privilege-grant endpoint."""
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uid', required=True, help='Firebase account UID to grant or revoke operator access.')
    parser.add_argument('--revoke', action='store_true')
    args = parser.parse_args()
    project = os.getenv('UPSHIFT_FIREBASE_PROJECT_ID')
    if not project: parser.error('Set UPSHIFT_FIREBASE_PROJECT_ID and server-side credentials first.')
    emulator = os.getenv('FIREBASE_AUTH_EMULATOR_HOST')
    if emulator and (not project.startswith('demo-') or emulator not in ('127.0.0.1:9099', 'localhost:9099')):
        parser.error('Auth emulators are restricted to local demo projects.')
    import firebase_admin
    from firebase_admin import auth
    app = firebase_admin.initialize_app(options={'projectId': project}, name='upshift-listings-operator')
    user = auth.get_user(args.uid, app=app)
    claims = dict(user.custom_claims or {})
    if args.revoke: claims.pop('upshift_admin', None)
    else: claims['upshift_admin'] = True
    auth.set_custom_user_claims(args.uid, claims, app=app)
    print('Operator access updated. Sign in again to obtain a token with the new claims.')


if __name__ == '__main__': main()
