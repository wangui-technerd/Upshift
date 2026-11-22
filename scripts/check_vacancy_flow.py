"""Exercise the real model and moderation API against local Firebase emulators."""
import os
from datetime import timedelta
from uuid import uuid4

import firebase_admin
import httpx
from firebase_admin import auth

from backend.listing_service import listing_day


def expect(response, status):
    if response.status_code != status:
        raise RuntimeError(
            f"{response.request.method} {response.request.url.path}: "
            f"expected HTTP {status}, got {response.status_code}: {response.text}"
        )
    return response.json()


def sign_up(client, label, run_id):
    email = f"{label}-{run_id}@example.test"
    password = uuid4().hex
    result = expect(
        client.post("http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signUp",
                    params={"key": "emulator"},
                    json={"email": email, "password": password, "returnSecureToken": True}),
        200,
    )
    return result, email, password


def main():
    project = os.environ.get("UPSHIFT_FIREBASE_PROJECT_ID", "")
    if not project.startswith("demo-") or (
        os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") != "127.0.0.1:9099"
        or os.environ.get("FIRESTORE_EMULATOR_HOST") != "127.0.0.1:8080"
    ):
        raise RuntimeError("This test requires local Firebase emulators and a demo project.")
    firebase = firebase_admin.initialize_app(options={"projectId": project})
    run_id = uuid4().hex[:12]
    with httpx.Client(base_url="http://127.0.0.1:8122", timeout=60, trust_env=False) as client:
        recruiter, _, _ = sign_up(client, "recruiter", run_id)
        other, _, _ = sign_up(client, "other", run_id)
        student, _, _ = sign_up(client, "student", run_id)
        admin, admin_email, admin_password = sign_up(client, "admin", run_id)
        auth.set_custom_user_claims(admin["localId"], {"upshift_admin": True}, app=firebase)
        admin = expect(
            client.post("http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
                        params={"key": "emulator"},
                        json={"email": admin_email, "password": admin_password, "returnSecureToken": True}),
            200,
        )

        def request(account, method, path, status, body=None):
            return expect(client.request(method, path, json=body,
                          headers={"Authorization": f"Bearer {account['idToken']}"}), status)

        health = expect(client.get("/health"), 200)
        assert health["auth_configured"] and health["model_status"] == "ready"
        source = f"https://example.org/upshift-fixtures/{run_id}/python"
        application = f"https://example.org/upshift-fixtures/{run_id}/apply?source=partner&job=348#application"
        vacancy = {
            "title": "Python Software Intern",
            "description": "Build Python APIs with an engineering mentor. Write tests and use source control.",
            "career_level": "internship", "location": "Nairobi, Kenya",
            "source_url": source, "application_url": application,
            "requirements": ["Docker is required.", "Python is required."],
            "minimum_experience_months": 3,
            "eligibility": ["Current computing student."],
            "deadline": (listing_day() + timedelta(days=10)).isoformat(),
        }

        def register_company(account):
            company = request(account, "POST", "/listings/companies", 201,
                              {"name": "UpShift Test Employer", "website": "https://example.org"})
            review = f"/listings/admin/companies/{company['id']}/review"
            request(account, "POST", review, 403, {"approved": True})
            request(admin, "POST", review, 200, {"approved": True})
            return f"/listings/companies/{company['id']}/vacancies"

        def publish(posting):
            path = f"/listings/admin/submissions/{posting['id']}/review"
            request(student, "POST", path, 403, {"revision": posting["revision"], "decision": "publish",
                                                "note": "Fixture checked."})
            return request(admin, "POST", path, 200, {"revision": posting["revision"], "decision": "publish",
                                                      "note": "Fixture checked."})

        payload = {
            "resume_text": "Computing student. I built Python APIs, wrote SQL queries, and used Git.",
            "location": "Nairobi", "experience_months": 6,
        }

        def recommend(**overrides):
            return request(student, "POST", "/recommendations", 200, payload | overrides)

        expect(client.post("/recommendations", json=payload), 401)
        main_path = register_company(recruiter)
        request(other, "POST", main_path, 403, vacancy)
        primary = request(recruiter, "POST", main_path, 201, vacancy)
        assert recommend()["matches"] == []
        publish(primary)
        match, = recommend()["matches"]
        assert match["job_id"] == primary["id"]
        assert match["application_url"] == application
        assert match["job_posting_url"] == source
        assert match["experience_requirement_status"] == "meets_minimum"
        assert "Docker" in match["skills_not_mentioned"], match["skills_not_mentioned"]
        assert recommend(experience_months=0)["matches"] == []
        assert recommend(experience_months=None)["matches"][0]["experience_requirement_status"] == "unknown"
        assert recommend(location="Kisumu")["status"] == "no_match"

        edited = request(recruiter, "POST", main_path, 201, vacancy | {"title": "Python API Intern"})
        assert recommend()["matches"] == []
        publish(edited)
        assert recommend()["matches"][0]["title"] == "Python API Intern"

        duplicate = request(other, "POST", register_company(other), 201,
                            vacancy | {"source_url": source + "?utm_source=email"})
        publish(duplicate)
        assert len(recommend()["matches"]) == 1
        duplicate_path = f"/listings/submissions/{duplicate['id']}/withdraw"
        request(other, "POST", duplicate_path, 200)
        assert [row["job_id"] for row in recommend()["matches"]] == [primary["id"]]
        primary_path = f"/listings/submissions/{primary['id']}/withdraw"
        request(student, "POST", primary_path, 403)
        request(recruiter, "POST", primary_path, 200)
        after = recommend()
        assert after["status"] == "no_match" and after["matches"] == []
        sentiment = request(student, "POST", "/sentiment", 200, {"text": "This app helped."})
        assert sentiment["label"] in {"positive", "negative", "neutral"}
        print("PASS: model readiness, Firebase roles, publication, edit, requirements, "
              "experience, deduplication, correct application destination, withdrawal and sentiment")


if __name__ == "__main__":
    main()
