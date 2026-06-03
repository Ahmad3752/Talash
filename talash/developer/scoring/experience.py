"""Professional experience scoring."""

from .state import DeveloperScoringState
from .utils import module_payload


def experience_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    months = p.get("total_relevant_experience_months") or 0
    seniority = (p.get("seniority_level") or "").lower()
    current_role = p.get("current_role")

    duration_score = 5 if months >= 48 else 4 if months >= 24 else 3 if months >= 12 else 1 if months else 0
    progression_score = 4 if seniority in {"senior", "lead", "principal", "manager"} else 3 if seniority == "mid" else 2 if seniority == "junior" else 1 if seniority == "intern" else 0
    relevance_score = 3 if current_role else 0
    tenure_score = 2 if months >= 24 else 1 if months else 0
    clarity_score = 1 if p.get("extraction_confidence") != "low" else 0
    score = duration_score + progression_score + relevance_score + tenure_score + clarity_score

    evidence = []
    if current_role:
        evidence.append(f"Current/recent role detected: {current_role}")
    if months:
        evidence.append(f"Relevant developer experience estimated at {months} months.")

    missing = []
    if not current_role:
        missing.append("No current/recent developer role detected.")
    if not months:
        missing.append("Relevant experience duration could not be estimated.")

    return {"module_scores": module_payload(
        "professional_experience", "Professional Experience", score, 15,
        evidence, missing,
        {
            "duration_score": duration_score,
            "seniority_progression_score": progression_score,
            "role_relevance_score": relevance_score,
            "tenure_consistency_score": tenure_score,
            "gap_overlap_clarity_score": clarity_score,
        },
        ["Add clear start/end dates and developer role descriptions."],
        "medium" if months else "low",
    )}
