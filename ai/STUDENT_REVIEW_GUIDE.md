# Student recommendation review

This pack is for the AI/app deliverable, separate from the proposal questionnaire. No relevance judgements have been invented.

## Order

1. Run `python ai/prepare_student_review.py` once using the trusted local export and saved encoder. It writes `ai/student_review/` and refuses to overwrite it.
2. Give each reviewer only their own reviewer folder, this guide and `calibration_five_pairs.csv`. Keep `private/` and the other reviewer's answers out of sight.
3. Discuss the five calibration examples to agree how to apply the rubric. These separate profiles are excluded from reported metrics. Then rate the main sheets independently.
4. In `reviewer_identity.json`, record `reviewer_type` as `human` or `ai_assisted`, the date and an actual unique reviewer identifier. An AI review must not be described as a second independent human reviewer.
5. Reviewers complete all rows, then discuss disagreements. Copy `private/adjudication_template.csv` to `private/adjudication_completed.csv`; insert original reviewer scores, final decisions and reasons. Preserve original sheets.
6. Run `python ai/score_student_review.py`. It refuses blank/invalid ratings. Freeze the scoring plan before reviewing.

## Rubric

Assess the actual job description against the supplied student evidence. Do not use the job title alone. Do not invent missing qualifications. Missing evidence is not proof the student lacks a skill.

| relevance | Meaning |
| --- | --- |
| 0 | Poor fit: substantially different field or mandatory experience/qualifications far beyond this first-internship profile. |
| 1 | Partial fit: related skills or discipline, with meaningful gaps or limited evidence for core duties. |
| 2 | Good fit: relevant student/entry-level role with evidence for the main duties; ordinary learnable internship gaps are acceptable. |

If unsure, leave relevance blank and explain `uncertain_reason`; resolve before final scoring. Never silently convert uncertainty into 0.

Record `eligibility` separately: `eligible`, `ineligible`, or `unknown`. Use explicit location, work-authorisation, education or other stated conditions. A foreign location does not prove eligibility; unknown authorisation remains unknown. Senior experience requirements affect fit as well as any explicit eligibility rule.

Record `availability` separately: `active`, `expired`, or `unknown`. Use dates or verified evidence, not assumptions. This catalogue is historical, so the pack is not a list of jobs students can apply to now. A relevant historical role can still be expired.

Write a short reason anchored in the profile and vacancy. Do not exchange main-sheet answers before both independent reviews finish.

## Frozen design

There are 12 fictional profiles across computing, finance/accounting, marketing, HR, engineering and digital media, with one validation and one test profile per field. Two separate calibration profiles supply five practice pairs. Profiles are synthetic research cases, not a representative sample of Kenyan students.

Both TF-IDF (`lexical`) and MiniLM (`semantic`) retrieve five results from the same existing catalogue. A duplicate profile/job pair is rated once. Reviewer sheets omit method, rank, similarity, skill-coverage predictions and dataset split. Each job's descriptive evidence remains visible. Long job descriptions are retained without truncation.

P@5 = count of relevance-2 matches divided by five, including unfilled slots in the denominator. NDCG@5 uses gains 0/1/3 and the ideal order among the pooled top-five candidates from both methods. It is pooled NDCG, not a full-catalogue benchmark. A profile with no relevant candidates gets NDCG 0. Coverage reports both any returned result and at least one good match.

Choose the ranking method on validation mean pooled NDCG@5, breaking ties on validation P@5 and then preferring lexical. Evaluate the selected method on test profiles once. Do not tune on test judgements. Report disagreement and reviewer types; do not average human and AI assessments and call the result human ground truth.

Keep the corpus, profiles and method settings unchanged during review. The private manifest records hashes and the method/rank mapping. If inputs must change, create a separately versioned review, do not overwrite completed labels.

## Completion

This pack completes review preparation only. Final method selection, final model export and the Member 2 handoff remain pending real ratings and adjudication. No backend, Android changes, external messages or claims of human validation are made by generating the pack.
