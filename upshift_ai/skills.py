"""Conservative ESCO extraction with stable concept IDs and contextual evidence."""

from dataclasses import dataclass
from collections import defaultdict
import re
from .preprocessing import clean_text, plain_text, segments, TOKEN_PATTERN

MANUAL = {
    "Python": (
        [
            "python",
            "python programming",
            "python language",
            "python (computer programming)",
        ],
        ["Python (computer programming)"],
    ),
    "Java": (
        ["java", "java programming", "java (computer programming)"],
        ["Java (computer programming)"],
    ),
    "JavaScript": (["javascript", "js"], ["JavaScript"]),
    "TypeScript": (["typescript"], ["TypeScript"]),
    "SQL": (["sql", "structured query language"], ["SQL"]),
    "HTML": (["html", "html5"], ["HTML"]),
    "CSS": (["css", "css3"], ["CSS"]),
    "C++": (["c++"], ["C++"]),
    "C#": (["c#", "c sharp"], ["C#"]),
    ".NET": ([".net", "dotnet", "dot net"], [".NET"]),
    "Node.js": (["node.js", "nodejs", "node js"], ["Node.js"]),
    "React": (["react", "react.js", "reactjs"], []),
    "React Native": (["react native"], []),
    "Kotlin": (["kotlin"], ["Kotlin"]),
    "Android": (["android", "android sdk"], []),
    "Firebase": (["firebase"], []),
    "Git": (["git", "git version control"], ["Git"]),
    "Docker": (["docker", "docker containers"], []),
    "Excel": (["excel", "ms excel", "microsoft excel"], ["Microsoft Excel"]),
    "Figma": (["figma"], []),
    "Canva": (["canva"], []),
    "Teamwork": (["teamwork", "team work"], []),
    "Communication": (
        ["communication skills", "written communication", "verbal communication"],
        [],
    ),
    "MySQL": (["mysql"], ["MySQL"]),
    "PostgreSQL": (["postgresql", "postgres"], ["PostgreSQL"]),
    "Linux": (["linux"], ["Linux"]),
    "REST APIs": (["rest api", "rest apis", "restful api", "restful apis"], []),
    "Testing": (["unit testing", "software testing", "automated testing"], []),
    "Research": (["user research", "usability research"], []),
    "Accessibility": (["web accessibility", "digital accessibility", "wcag"], []),
}
AMBIGUOUS = {
    "plan",
    "stand",
    "commitment",
    "less",
    "react",
    "integrity",
    "reliability",
    "history",
    "pregnancy",
    "morality",
    "banking",
    "call",
    "support",
    "english",
    "assume responsibility",
    "approach challenges positively",
}
TECH_SINGLE = {
    clean_text(a)
    for name, (aliases, _) in MANUAL.items()
    for a in aliases
    if " " not in a
}


@dataclass
class SkillLexicon:
    aliases: dict
    concepts: dict
    audit: dict

    def __post_init__(self):
        self.trie = {}
        for alias, sid in self.aliases.items():
            tokens = re.findall(TOKEN_PATTERN, alias)
            if not tokens:
                continue
            node = self.trie
            for token in tokens:
                node = node.setdefault(token, {})
            node["_id"] = sid

    def find(self, text):
        cleaned = clean_text(text)
        tokens = re.findall(TOKEN_PATTERN, cleaned)
        hits = []
        i = 0
        while i < len(tokens):
            node = self.trie
            j = i
            best = None
            while j < len(tokens) and tokens[j] in node:
                node = node[tokens[j]]
                j += 1
                if "_id" in node:
                    best = (j, node["_id"])
            if best:
                end, sid = best
                alias = " ".join(tokens[i:end])
                before = " ".join(tokens[max(0, i - 6) : i])
                after = " ".join(tokens[end : end + 5])
                neg = bool(
                    re.search(r"\b(?:no|not|without|lack|lacking|never)\b", before)
                    or re.search(
                        r"^(?:is |are )?(?:not required|not necessary|not needed|isn t required)",
                        after,
                    )
                )
                if "not only" in before:
                    neg = False
                if alias == "react" and not (
                    re.search(
                        r"\b(?:javascript|frontend|front-end|framework|jsx|web|skills)\b",
                        cleaned,
                    )
                    or re.search(r"\bReact\b", text)
                ):
                    i = end
                    continue
                hits.append(
                    {
                        "id": sid,
                        "label": self.concepts[sid]["label"],
                        "alias": alias,
                        "negated": neg,
                        "evidence": text[:400],
                    }
                )
                i = end
            else:
                i += 1
        return hits

    def profile_skills(self, text):
        return {
            h["id"]
            for part in segments(text)
            for h in self.find(part)
            if not h["negated"]
        }

    def job_skills(self, text):
        found = {
            "required": set(),
            "preferred": set(),
            "mentioned": set(),
            "excluded": set(),
        }
        evidence = []
        mode = "mentioned"
        for part in segments(text):
            lower = part.lower()
            if re.search(
                r"^(?:responsibilities|what you.ll do|about us|about the company|benefits|we offer|our team)\b",
                lower,
            ):
                mode = "mentioned"
            if re.search(
                r"^(?:requirements|qualifications|essential|what you bring|what you.ll need|skills required|technical skills|minimum qualifications)\b",
                lower,
            ):
                mode = "required"
            if re.search(r"^(?:preferred|nice to have|desirable|bonus)\b", lower):
                mode = "preferred"
            current = mode
            if re.search(
                r"\b(?:preferred|nice to have|optional|a plus|desirable|bonus)\b", lower
            ):
                current = "preferred"
            elif re.search(
                r"\b(?:must|required|essential|proficien\w*|knowledge of|experience (?:with|in)|ability to|familiarity with)\b",
                lower,
            ):
                current = "required"
            sentence_negated = (
                bool(re.search(r"not required|not necessary|not needed", lower))
                and not re.search(r"\b(?:is|are) required\b", lower)
                and current != "preferred"
            )
            for hit in self.find(part):
                sid = hit["id"]
                if hit["negated"] or sentence_negated:
                    # "preferred but not required" is handled as a preference, never a requirement.
                    if (
                        current == "preferred"
                        and re.search(r"not required|not necessary", lower)
                        and not re.search(
                            r"\bno (?:experience|knowledge)|\bwithout\b", lower
                        )
                    ):
                        found["preferred"].add(sid)
                    else:
                        found["excluded"].add(sid)
                else:
                    found[current].add(sid)
                evidence.append({**hit, "kind": current})
        found["preferred"] -= found["required"]
        found["mentioned"] -= found["required"] | found["preferred"]
        return {**{k: sorted(v) for k, v in found.items()}, "evidence": evidence}


def build_lexicon(frame):
    frame = frame.fillna("").drop_duplicates("conceptUri")
    concepts = {}
    candidates = defaultdict(set)
    preferred = {}
    for row in frame.to_dict("records"):
        sid = row["conceptUri"]
        label = row["preferredLabel"].strip()
        if not sid or not label:
            continue
        concepts[sid] = {
            "label": label,
            "source": "ESCO",
            "type": row.get("skillType", ""),
        }
        preferred[clean_text(label)] = sid
        for alias in (
            [label]
            + str(row.get("altLabels", "")).split("\n")
            + str(row.get("hiddenLabels", "")).split("\n")
        ):
            alias = clean_text(alias)
            if (
                not alias
                or alias in AMBIGUOUS
                or (len(alias) < 3 and alias not in {"c#", "c++"})
            ):
                continue
            if " " not in alias and alias not in TECH_SINGLE:
                continue
            candidates[alias].add(sid)
    clashes = {a: sorted(ids) for a, ids in candidates.items() if len(ids) > 1}
    aliases = {a: next(iter(ids)) for a, ids in candidates.items() if len(ids) == 1}
    for name, (spellings, targets) in MANUAL.items():
        sid = next(
            (preferred[clean_text(t)] for t in targets if clean_text(t) in preferred),
            None,
        )
        if sid is None:
            sid = "urn:upshift:skill:" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip(
                "-"
            )
        concepts[sid] = {
            "label": name,
            "source": "ESCO" if sid.startswith("http") else "UpShift extension",
            "type": "knowledge",
        }
        # Keep all existing synonyms for the selected concept, and assign new synonyms to that same ID.
        for alias in spellings:
            aliases[clean_text(alias)] = sid
    return SkillLexicon(
        aliases,
        concepts,
        {
            "ambiguous_aliases_excluded": clashes,
            "alias_count": len(aliases),
            "concept_count": len(concepts),
        },
    )
