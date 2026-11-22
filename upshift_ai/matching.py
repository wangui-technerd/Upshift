"""Shared recommendation contract for the notebook and Python service."""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .preprocessing import prepare_resume


def recommend(
    bundle,
    resume_text,
    top_k=5,
    method="lexical",
    min_similarity=0.0,
    encoder=None,
    live_only=False,
):
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Provide non-empty profile or CV text.")
    if len(resume_text) > 50000:
        raise ValueError("CV text exceeds 50,000 characters.")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer between 1 and 20.")
    if method not in {"lexical", "semantic"}:
        raise ValueError("method must be lexical or semantic.")
    if not isinstance(min_similarity, (float, int)) or not 0 <= min_similarity <= 1:
        raise ValueError("min_similarity must be in [0,1].")
    vector = bundle["retriever"].transform([prepare_resume(resume_text)])
    if vector.nnz == 0:
        return {
            "status": "no_match",
            "method": method,
            "matches": [],
            "catalogue_status": "historical_research_not_live",
        }
    if method == "semantic":
        if encoder is None:
            raise ValueError("Semantic encoder must be loaded for semantic requests.")
        from .semantic import encode_documents

        scores = (
            encode_documents(encoder, [prepare_resume(resume_text)])
            @ bundle["semantic_vectors"].T
        ).ravel()
    else:
        scores = cosine_similarity(vector, bundle["job_vectors"]).ravel()
    profile_skills = bundle["lexicon"].profile_skills(resume_text)
    order = np.argsort(-scores, kind="stable")
    matches = []
    for pos in order:
        if len(matches) >= top_k:
            break
        score = float(scores[pos])
        if score <= min_similarity:
            continue
        row = bundle["jobs"].iloc[int(pos)]
        if live_only and (
            bool(row["is_expired"]) or row["eligibility_status"] != "verified"
        ):
            continue
        skillsets = bundle["job_skills"][int(pos)]
        required = set(skillsets["required"])
        preferred = set(skillsets["preferred"])

        def present(ids):
            return [
                {"id": sid, "label": bundle["lexicon"].concepts[sid]["label"]}
                for sid in sorted(
                    ids, key=lambda x: bundle["lexicon"].concepts[x]["label"]
                )
            ]

        matched = required & profile_skills
        unmentioned = required - profile_skills
        coverage = len(matched) / len(required) if required else None
        matches.append(
            {
                "job_id": str(row.job_id),
                "title": str(row.title),
                "company_name": str(row.company_name),
                "description": str(row.description),
                "location": str(row.location),
                "work_type": str(row.formatted_work_type),
                "experience_level": str(row.formatted_experience_level),
                "similarity": round(score, 6),
                "ranking_method": method,
                "skill_coverage": coverage,
                "skills_match_percentage": round(coverage * 100)
                if coverage is not None
                else None,
                "matched_skills": present(matched),
                "required_skills_not_mentioned": present(unmentioned),
                "preferred_skills_not_mentioned": present(preferred - profile_skills),
                "mentioned_other_skills": present(set(skillsets["mentioned"])),
                "is_expired": bool(row.is_expired),
                "eligibility_status": str(row.eligibility_status),
                "listed_date": row.listed_time_utc,
                "expiry_date": row.expiry_utc,
                "application_url": str(row.application_url),
                "job_posting_url": str(row.job_posting_url),
            }
        )
    return {
        "status": "matches_found" if matches else "no_match",
        "method": method,
        "catalogue_status": "historical_research_not_live",
        "matches": matches,
    }
