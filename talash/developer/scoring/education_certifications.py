"""Education and certification scoring."""

from .state import DeveloperScoringState
from .utils import clamp, module_payload


def education_certifications_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    certs = p.get("certifications", [])
    raw = str(p.get("raw_profile_json") or "").lower()
    degree_score = 2 if any(k in raw for k in ["computer", "software", "information technology", "it", "engineering"]) else 0
    cert_score = min(1.5, len(certs) * 1.5)
    learning_score = 1.5 if certs or p.get("projects") else 0
    score = degree_score + cert_score + learning_score

    evidence = []
    if degree_score:
        evidence.append("Relevant CS/software/engineering education signal detected.")
    if certs:
        evidence.append(f"Certifications detected: {', '.join(certs[:4])}")

    missing = []
    if not degree_score:
        missing.append("No clearly relevant software/CS education signal detected.")
    if not certs:
        missing.append("No developer certifications detected.")

    return {"module_scores": module_payload(
        "education_certifications", "Education & Certifications", score, 5,
        evidence, missing,
        {
            "degree_relevance_score": clamp(degree_score, 2),
            "certification_score": clamp(cert_score, 1.5),
            "continuous_learning_score": clamp(learning_score, 1.5),
        },
        ["Add relevant certifications, courses, or training if applicable."],
        "medium" if evidence else "low",
    )}
