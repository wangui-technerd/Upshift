"""Populate a fictional vacancy on the local Member 2 Firestore emulator."""
import argparse
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.cloud import firestore
from google.auth.credentials import AnonymousCredentials

PROJECT = "demo-upshift"
HOST = "127.0.0.1:8080"
COMPANY = "member3-demo-employer"
VACANCY = "member3-demo-python-internship"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--close", action="store_true", help="Archive the demo vacancy")
    options = parser.parse_args()
    os.environ["FIRESTORE_EMULATOR_HOST"] = HOST
    db = firestore.Client(project=PROJECT, credentials=AnonymousCredentials())
    vacancy = db.collection("opportunities").document(VACANCY)
    if options.close:
        vacancy.update({"availability_status": "archived", "ready_for_live_application": False})
        print(f"Archived {VACANCY}. Request recommendations again.")
        return

    company = db.collection("partner_companies").document(COMPANY)
    deadline = datetime.now(ZoneInfo("Africa/Nairobi")).date() + timedelta(days=14)
    batch = db.batch()
    batch.set(company, {"id": COMPANY, "name": "UpShift Demo Employer", "status": "approved"})
    batch.set(vacancy, {
        "id": VACANCY,
        "company_id": COMPANY,
        "company": "UpShift Demo Employer",
        "title": "Python Software Intern (Demo)",
        "description": "Build Python APIs, write SQL queries and run tests with an engineering mentor.",
        "skills": ["Python", "SQL", "Git", "Docker"],
        "responsibilities": ["Build supervised Python APIs.", "Write SQL queries and review changes using Git."],
        "location": "Nairobi",
        "career_level": "internship",
        "requirements": ["Python is required.", "Docker is required.", "Git is required."],
        "eligibility": ["Current computing student."],
        "minimum_experience_months": 3,
        "deadline": deadline.isoformat(),
        "source_url": "https://example.org/?upshift-demo=python",
        "application_url": "https://example.org/?upshift-demo=apply",
        "availability_status": "published",
        "ready_for_live_application": True,
        "revision": 1,
    })
    batch.commit()
    print(f"Published emulator fixture {VACANCY} with deadline {deadline}.")


if __name__ == "__main__":
    main()
