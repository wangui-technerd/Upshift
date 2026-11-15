"""Shared UpShift inference. Load only trusted, self-produced joblib artifacts."""
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

TOKEN_PATTERN = r"(?u)(?:\.net\b|\b\w+(?:[.+#-]\w+)*(?:\+\+|#)?)"
SECTION_WORDS = {"summary","skills","skill","experience","education","objective",
                 "profile","highlights","qualifications","career","professional"}

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\.\S+|\S+@\S+", " ", text.lower())
    return re.sub(r"\s+", " ", re.sub(r"[^\w+#.\s-]", " ", text)).strip()

def prepare_resume(text):
    if not isinstance(text, str):
        return ""
    rest = text.strip()
    for _ in range(2):
        parts = re.split(r"\s{2,}", rest, maxsplit=1)
        chunk = parts[0]
        letters = [c for c in chunk if c.isalpha()]
        words = re.findall(r"[a-z]+", chunk.lower())
        title = (len(parts) == 2 and 0 < len(chunk) <= 80 and letters
                 and sum(c.isupper() for c in letters)/len(letters) > .8
                 and words and words[0] not in SECTION_WORDS)
        if not title:
            break
        rest = parts[1]
    rest = re.sub(r"\bcompany name\b|\bcity\s*,?\s*state\b", " ", rest, flags=re.I)
    return clean_text(rest)

def build_lookup(frame):
    table = frame.dropna(subset=["label_norm", "canonical"]).copy()
    table["alias"] = table["label_norm"].map(clean_text)
    # Exclude unresolved collisions rather than silently selecting one.
    clashes = table.groupby("alias")["canonical"].nunique()
    table = table[~table["alias"].isin(clashes[clashes > 1].index)]
    stop = {"plan","stand","commitment","less","react","integrity","reliability",
            "history","pregnancy","morality","banking","call","support","english"}
    table = table[~table["alias"].isin(stop)]
    # Multiword labels and explicit technology aliases only: conservative precision-first policy.
    table = table[table["alias"].str.contains(" ") | table["alias"].isin(
        {"python","java","javascript","typescript","sql","kotlin","c++","c#","html","css",
         "linux","git","docker","firebase","mysql","postgresql","mongodb"})]
    lookup = dict(zip(table["alias"], table["canonical"]))
    lookup.update({"react.js":"React","reactjs":"React","react native":"React Native",
                   "docker":"Docker","teamwork":"Teamwork","kotlin":"Kotlin",
                   "firebase":"Firebase","c++":"C++","c#":"C#","python":"Python",
                   "sql":"SQL",".net":".NET","node.js":"Node.js"})
    return lookup

_TRIE_CACHE = (None, None)

def extract_skills(text, lookup):
    global _TRIE_CACHE
    tokens = re.findall(TOKEN_PATTERN, clean_text(text))
    if _TRIE_CACHE[0] is not lookup:
        trie = {}
        for alias, canonical in lookup.items():
            node = trie
            for token in re.findall(TOKEN_PATTERN, alias):
                node = node.setdefault(token, {})
            node["__skill__"] = canonical
        _TRIE_CACHE = (lookup, trie)
    trie = _TRIE_CACHE[1]
    hits, i = set(), 0
    while i < len(tokens):
        node, j, longest = trie, i, None
        while j < len(tokens) and tokens[j] in node:
            node = node[tokens[j]]
            j += 1
            if "__skill__" in node:
                longest = (j, node["__skill__"])
        if longest:
            i, skill = longest
            hits.add(skill)
        else:
            i += 1
    return hits

def recommend(bundle, resume_text, top_k=5, min_similarity=0.0):
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Provide non-empty CV text.")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer from 1 to 20.")
    if not 0 <= min_similarity <= 1:
        raise ValueError("min_similarity must be between 0 and 1.")
    text = prepare_resume(resume_text)
    vector = bundle["retriever"].transform([text])
    if vector.nnz == 0 or len(bundle["jobs"]) == 0:
        return {"status":"no_match", "matches":[]}
    scores = cosine_similarity(vector, bundle["job_vectors"]).ravel()
    best = np.argsort(-scores, kind="stable")[:top_k]
    resume_skills = extract_skills(text, bundle["skill_lookup"])
    matches = []
    for pos in best:
        score = float(scores[pos])
        if score <= min_similarity:
            continue
        row = bundle["jobs"].iloc[int(pos)]
        required = bundle["job_skills"][int(pos)]
        matches.append({
            "job_id": str(row["job_id"]), "title":str(row["title"]),
            "company_name":str(row["company_name"]), "similarity":round(score, 6),
            "application_url":str(row.get("application_url", "")),
            "job_posting_url":str(row.get("job_posting_url", "")),
            "skills_mentioned":sorted(required & resume_skills),
            "skills_not_mentioned":sorted(required - resume_skills),
            "skill_coverage":len(required & resume_skills)/len(required) if required else None})
    return {"status":"matches_found" if matches else "no_match", "matches":matches}
