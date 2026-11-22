"""Verify the UpShift API using a Firebase ID token and an optional known vacancy."""
import argparse
import getpass
import os
from urllib.parse import urlsplit

import httpx


def check(base_url, token, search_text, expected_job_id=None):
    is_local = urlsplit(base_url).hostname in {"localhost", "127.0.0.1", "::1"}
    with httpx.Client(base_url=base_url, timeout=90, trust_env=not is_local) as client:
        response = client.get("/health")
        response.raise_for_status()
        health = response.json()
        if health.get("model_status") != "ready" or health.get("auth_configured") is not True:
            raise RuntimeError("The model or Firebase configuration is unavailable.")

        payload = {"resume_text": search_text, "catalogue": "live", "top_k": 5}
        if client.post("/recommendations", json=payload).status_code != 401:
            raise RuntimeError("The recommendations endpoint did not reject a missing token.")

        response = client.post(
            "/recommendations", json=payload, headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        result = response.json()
        matches = result["matches"]
        if result.get("catalogue_status") != "backend_supplied_vacancies":
            raise RuntimeError("The response did not use the live vacancy catalogue.")
        if result.get("status") != ("matches_found" if matches else "no_match"):
            raise RuntimeError("The response status does not match the live results.")
        if expected_job_id and expected_job_id not in {match["job_id"] for match in matches}:
            raise RuntimeError("The expected live vacancy was absent from the top five.")
        return len(matches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--search-text", default="Python software development internship")
    parser.add_argument("--expect-job-id")
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    if not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error("Provide an API base URL without credentials, a query, or a fragment.")
    if url.scheme != "https" and not (
        url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"}
    ):
        parser.error("Use HTTPS for deployed services.")
    token = os.getenv("UPSHIFT_FIREBASE_ID_TOKEN") or getpass.getpass("Firebase ID token: ")
    if not token:
        parser.error("A Firebase ID token is required.")
    try:
        count = check(args.base_url, token, args.search_text, args.expect_job_id)
    except (httpx.HTTPError, KeyError, ValueError, RuntimeError) as error:
        parser.exit(1, f"UpShift check failed: {error}\n")
    print(f"UpShift health and Firebase authentication passed. Live matches: {count}.")


if __name__ == "__main__":
    main()
