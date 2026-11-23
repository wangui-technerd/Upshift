"""Real Auth + Firestore emulator checks, not mocks. Never points at a live project.

Start: firebase emulators:start --only auth,firestore --project demo-upshift
Run: python -m backend.tests.emulator_smoke
"""
import secrets
import unittest
import httpx

AUTH = 'http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1'
DB = 'http://127.0.0.1:8080/v1/projects/demo-upshift/databases/(default)/documents'


def value(v):
    if isinstance(v, bool): return {'booleanValue': v}
    if isinstance(v, str): return {'stringValue': v}
    if isinstance(v, list): return {'arrayValue': {'values': [value(x) for x in v]}}
    if isinstance(v, dict): return {'mapValue': {'fields': {k: value(x) for k, x in v.items()}}}
    raise TypeError(type(v))


class FirebaseEmulatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = httpx.Client(timeout=15)
        cls.addClassCleanup(cls.client.close)
        cls.accounts = []
        for _ in range(2):
            email = f'test-{secrets.token_hex(6)}@example.com'
            response = cls.client.post(AUTH+'/accounts:signUp?key=emulator-only', json={
                'email': email, 'password': 'Emulator-test-password-123', 'returnSecureToken': True})
            response.raise_for_status()
            cls.accounts.append((email, response.json()['localId'], response.json()['idToken']))

    def headers(self, index=0):
        return {'Authorization': 'Bearer '+self.accounts[index][2]}

    def data(self, index=0):
        return {'profile': {'name':'Student','email':self.accounts[index][0], 'phone':'',
                            'education':'BICS','skills':'Kotlin','summary':'','projects':'',
                            'experience':'','location':'Kenya','goal':'Internship'},
                'saved':[], 'targetId':'', 'activityDays':[]}

    def write(self, path, data, index=0):
        return self.client.patch(DB+'/'+path, headers=self.headers(index),
                                 json={'fields':{k:value(v) for k,v in data.items()}})

    def test_profile_persistence_and_account_isolation(self):
        uid = self.accounts[0][1]
        self.assertEqual(self.write('users/'+uid,self.data()).status_code,200)
        self.assertEqual(self.client.get(DB+'/users/'+uid,headers=self.headers()).status_code,200)
        self.assertEqual(self.client.get(DB+'/users/'+uid,headers=self.headers(1)).status_code,403)
        self.assertEqual(self.write('users/'+uid,self.data(1),1).status_code,403)
        self.assertEqual(self.client.get(DB+'/users/'+uid).status_code,403)

    def test_spoofed_email_and_extra_fields_rejected(self):
        uid = self.accounts[0][1]
        data = self.data(); data['profile']['email'] = 'someone-else@example.com'
        self.assertEqual(self.write('users/'+uid,data).status_code,403)
        data = self.data(); data['admin'] = True
        self.assertEqual(self.write('users/'+uid,data).status_code,403)

    def test_learning_rules_and_no_xp_tampering(self):
        uid = self.accounts[0][1]
        self.write('users/'+uid,self.data())
        path = 'users/'+uid+'/learning/kotlin'
        data = {'notes':'Built and tested a Kotlin profile class.', 'completed':True}
        self.assertEqual(self.write(path,data).status_code,200)
        self.assertEqual(self.client.get(DB+'/'+path,headers=self.headers(1)).status_code,403)
        self.assertEqual(self.write(path,{**data,'xp':'99999'}).status_code,403)
        self.assertEqual(self.write(path,{'notes':'short','completed':True}).status_code,403)
        self.assertEqual(self.write(path,{**data,'completed':False}).status_code,200)

    def test_opportunities_are_operator_only(self):
        data = {'title':'Sample - emulator only'}
        self.assertEqual(self.write('opportunities/test-only',data).status_code,403)
        self.assertEqual(self.client.get(DB+'/opportunities',headers=self.headers()).status_code,200)

    def test_signin_and_reset_email(self):
        email, uid, _ = self.accounts[0]
        response=self.client.post(AUTH+'/accounts:signInWithPassword?key=emulator-only',json={
            'email':email,'password':'Emulator-test-password-123','returnSecureToken':True})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['localId'],uid)
        response=self.client.post(AUTH+'/accounts:sendOobCode?key=emulator-only',json={
            'email':email,'requestType':'PASSWORD_RESET'})
        self.assertEqual(response.status_code,200)


if __name__ == '__main__':
    unittest.main()
