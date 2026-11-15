import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app import create_app, RateLimiter
from backend.errors import Problem
from backend.models import Models
from backend.firebase_auth import FirebaseTokenVerifier

class TestVerifier:
    configured = True
    def verify(self, token):
        if token != "test-id-token":
            raise Problem(401, "unauthorized", "Invalid token")
        return "test-user"

class TestModels:
    state = "ready"
    bundle = {"sentiment_model": True}
    def recommendations(self, text, top_k):
        return {"method":"tfidf_cosine","matches":[{"job_id":"research-1","title":"Test only","similarity":0.5}],"received":text,"top_k":top_k}
    def sentiment(self, text):
        return {"label":"positive","method":"test-double"}

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(model_adapter=TestModels(), token_verifier=TestVerifier()))
        self.addCleanup(self.client.close)
        self.headers = {"Authorization":"Bearer test-id-token"}
    def test_auth_required_and_invalid_rejected(self):
        self.assertEqual(self.client.post("/recommendations",json={"resume_text":"Kotlin"}).status_code,401)
        self.assertEqual(self.client.post("/sentiment",json={"text":"Helpful"},headers={"Authorization":"Bearer invalid"}).status_code,401)
    def test_authenticated_inference_contract(self):
        response=self.client.post("/recommendations",headers=self.headers,json={"resume_text":"Kotlin projects", "top_k":3})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["top_k"],3)
        self.assertEqual(response.headers["Cache-Control"],"no-store")
        self.assertEqual(self.client.post("/sentiment",headers=self.headers,json={"text":"Helpful"}).json()["label"],"positive")
    def test_validation_does_not_echo_cv(self):
        private="personal text"*5000
        for body in ({"resume_text":"   "},{"resume_text":"Kotlin","top_k":True},{"resume_text":private}):
            response=self.client.post("/recommendations",headers=self.headers,json=body)
            self.assertEqual(response.status_code,422)
            self.assertNotIn(private,response.text)
    def test_local_accounts_and_storage_routes_removed(self):
        for path in ("/auth/sign-up","/auth/sign-in","/me/profile","/opportunities","/me/progress"):
            self.assertEqual(self.client.post(path,json={}).status_code,404)
    def test_missing_models_report_unavailable(self):
        with patch.dict("os.environ",{},clear=True):
            models=Models()
        with TestClient(create_app(model_adapter=models,token_verifier=TestVerifier())) as client:
            self.assertEqual(client.get("/health").json()["model_status"],"not_configured")
            self.assertEqual(client.post("/recommendations",headers=self.headers,json={"resume_text":"Kotlin"}).status_code,503)
            self.assertEqual(client.post("/sentiment",headers=self.headers,json={"text":"Helpful"}).status_code,503)
    def test_rate_limit(self):
        limiter=RateLimiter()
        for _ in range(30): limiter.check("a")
        with self.assertRaises(Problem) as caught: limiter.check("a")
        self.assertEqual(caught.exception.status,429)
        limiter.check("b")
    def test_missing_project_fails_closed(self):
        with patch.dict("os.environ",{},clear=True):
            verifier=FirebaseTokenVerifier()
        with self.assertRaises(Problem) as caught: verifier.verify("anything")
        self.assertEqual(caught.exception.status,503)
    def test_emulator_cannot_be_used_with_live_project(self):
        with patch.dict("os.environ",{"UPSHIFT_FIREBASE_PROJECT_ID":"real-project","FIREBASE_AUTH_EMULATOR_HOST":"127.0.0.1:9099"}):
            verifier=FirebaseTokenVerifier()
            with self.assertRaises(Problem) as caught: verifier.verify("anything")
            self.assertEqual(caught.exception.status,503)

if __name__ == "__main__": unittest.main()
