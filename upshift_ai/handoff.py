"""Schema-2 inference entry point shared by Member 2 and the delivery API."""

from pathlib import Path
import json
import threading
import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .matching import recommend
from .sentiment import analyse_sentiment
from .preprocessing import prepare_resume, clean_text
from .semantic import load_encoder, encode_documents


class ModelService:
    def __init__(self, artifact_dir, *, bundle_path=None):
        self.root = Path(artifact_dir)
        self.bundle = joblib.load(
            bundle_path
            if bundle_path is not None
            else self.root / "upshift_bundle.joblib"
        )
        if self.bundle.get("schema_version") != 2:
            raise ValueError(
                "Use the delivered schema-2 bundle, not the clear notebook toy export."
            )
        config = json.loads((self.root / "deployment_config.json").read_text())
        self.method = config["selected_method"]
        if self.method not in ("lexical", "semantic"):
            raise ValueError("Unknown selected method")
        self.encoder = None
        self.lock = threading.Lock()

    def prepare(self):
        """Validate the inference bundle and load the selected encoder before serving."""
        required = {"retriever", "jobs", "lexicon", "job_skills"}
        required.add("semantic_vectors" if self.method == "semantic" else "job_vectors")
        if not required <= self.bundle.keys():
            raise ValueError("The UpShift model bundle is missing required data.")
        if self.method == "semantic":
            self._encoder()

    def _encoder(self):
        with self.lock:
            if self.encoder is None:
                self.encoder = load_encoder(self.root / "semantic_encoder")
        return self.encoder

    def recommendations(self, text, top_k=5, live_only=False):
        result = recommend(
            self.bundle,
            text,
            top_k,
            self.method,
            encoder=self._encoder() if self.method == "semantic" else None,
            live_only=live_only,
        )
        return self._metadata(result)

    def _metadata(self, result):
        for match in result["matches"]:
            # Backwards-compatible names used by the older backend contract.
            match["skills_mentioned"] = [s["label"] for s in match["matched_skills"]]
            match["skills_not_mentioned"] = [
                s["label"] for s in match["required_skills_not_mentioned"]
            ]
        return {
            **result,
            "model_version": "schema-2-ai-assisted-2026-11-22",
            "score_definition": "Cosine text similarity, not a hiring probability. Skill coverage is a separate extracted-skill measure.",
            "validation_status": "single_ai_assisted_review_not_human_validated",
        }

    def sentiment(self, text):
        return analyse_sentiment(self.bundle, text)

    def rank_vacancies(self, text, vacancies, top_k=5):
        """Rank backend-supplied vacancies; caller must approve/filter access and expiry.

        Each item needs job_id, title and description. This function never treats
        the historical research catalogue as a live vacancy database.
        """
        if not isinstance(text, str) or not text.strip() or len(text) > 50000:
            raise ValueError("Provide 1 to 50,000 characters of CV text.")
        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or not 1 <= top_k <= 20
        ):
            raise ValueError("top_k must be 1 to 20.")
        if not vacancies:
            return self._metadata(
                {
                    "status": "no_match",
                    "method": self.method,
                    "matches": [],
                    "catalogue_status": "backend_supplied_vacancies",
                }
            )
        ids = [str(v["job_id"]) for v in vacancies]
        if len(set(ids)) != len(ids):
            raise ValueError("Vacancy IDs must be unique.")
        docs = []
        skill_descriptions = []
        for v in vacancies:
            if (
                not isinstance(v.get("title"), str)
                or not isinstance(v.get("description"), str)
                or not v["description"].strip()
            ):
                raise ValueError("Each vacancy needs title and nonblank description.")
            description = v["description"]
            requirements = v.get("requirements", [])
            if requirements:
                description += "\nRequirements:\n" + "\n".join(requirements)
            docs.append(clean_text(v["title"] + " " + description))
            skill_descriptions.append(description)
        query = prepare_resume(text)
        if self.method == "semantic":
            vectors = encode_documents(self._encoder(), [query] + docs)
            scores = (vectors[1:] @ vectors[0]).ravel()
        else:
            matrix = self.bundle["retriever"].transform([query] + docs)
            scores = cosine_similarity(matrix[0], matrix[1:]).ravel()
        have = self.bundle["lexicon"].profile_skills(text)

        def present(values):
            return [
                {"id": sid, "label": self.bundle["lexicon"].concepts[sid]["label"]}
                for sid in sorted(values)
            ]

        matches = []
        for pos in np.argsort(-scores, kind="stable"):
            if len(matches) >= top_k:
                break
            if float(scores[pos]) <= 0:
                continue
            v = vacancies[int(pos)]
            skills = self.bundle["lexicon"].job_skills(skill_descriptions[int(pos)])
            required = set(skills["required"])
            coverage = len(required & have) / len(required) if required else None
            matches.append(
                {
                    "job_id": str(v["job_id"]),
                    "title": v["title"],
                    "company_name": str(v.get("company_name", "")),
                    "description": v["description"],
                    "similarity": round(float(scores[pos]), 6),
                    "ranking_method": self.method,
                    "skill_coverage": coverage,
                    "skills_match_percentage": round(coverage * 100)
                    if coverage is not None
                    else None,
                    "matched_skills": present(required & have),
                    "required_skills_not_mentioned": present(required - have),
                    "preferred_skills_not_mentioned": present(
                        set(skills["preferred"]) - have
                    ),
                    "eligibility_status": "unverified",
                    "application_url": str(v.get("application_url", "")),
                }
            )
        return self._metadata(
            {
                "status": "matches_found" if matches else "no_match",
                "method": self.method,
                "matches": matches,
                "catalogue_status": "backend_supplied_vacancies",
            }
        )
