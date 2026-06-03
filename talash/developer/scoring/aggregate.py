"""Aggregate developer module scores into the final summary."""

from ..constants import DEVELOPER_SCORE_WEIGHTS
from .state import DeveloperScoringState


def aggregate_agent(state: DeveloperScoringState) -> dict:
    scores = state.get("module_scores", {})
    ordered_keys = list(DEVELOPER_SCORE_WEIGHTS.keys())
    module_summary = []
    total = 0.0
    strengths = []
    weaknesses = []
    recommendations = []

    for key in ordered_keys:
        module = scores.get(key)
        if not module:
            continue
        total += module["score"]
        module_summary.append({
            "key": key,
            "name": module["label"],
            "score": module["score"],
            "max": module["max_score"],
            "grade": module["grade"],
            "weight": DEVELOPER_SCORE_WEIGHTS[key],
            "confidence": module["confidence"],
            "evidence_found": module["evidence_found"],
            "missing_evidence": module["missing_evidence"],
            "reasons": module["reasons"],
            "recommendations": module["recommendations"],
        })
        if module["evidence_found"]:
            strengths.extend(module["evidence_found"][:2])
        if module["missing_evidence"]:
            weaknesses.extend(module["missing_evidence"][:2])
        recommendations.extend(module["recommendations"][:1])

    if total >= 85:
        grade = "EXCELLENT DEVELOPER FIT"
        recommendation = "Highly recommended for technical screening."
    elif total >= 70:
        grade = "STRONG DEVELOPER FIT"
        recommendation = "Recommended for technical screening."
    elif total >= 55:
        grade = "MODERATE DEVELOPER FIT"
        recommendation = "Consider screening if role constraints are flexible."
    elif total >= 40:
        grade = "WEAK DEVELOPER FIT"
        recommendation = "Request stronger project evidence before interview."
    else:
        grade = "INSUFFICIENT EVIDENCE"
        recommendation = "Not enough developer evidence for confident screening."

    summary = {
        "overall_score": round(total, 1),
        "overall_grade": grade,
        "hiring_recommendation": recommendation,
        "confidence": "high" if total >= 70 else "medium" if total >= 40 else "low",
        "module_summary": module_summary,
        "top_strengths": list(dict.fromkeys(strengths))[:6],
        "top_weaknesses": list(dict.fromkeys(weaknesses))[:6],
        "recommendations": list(dict.fromkeys(recommendations))[:6],
        "summary_interpretation": (
            f"Developer score is {round(total, 1)}/100. {recommendation} "
            "Scores are based on extracted CV evidence and missing-evidence deductions."
        ),
    }
    return {"summary": summary}
