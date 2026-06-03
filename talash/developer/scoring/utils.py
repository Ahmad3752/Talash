"""Shared helpers for developer scoring modules."""

import json
from typing import Any


def loads(value: Any, fallback: Any = None) -> Any:
    if fallback is None:
        fallback = []
    if value is None:
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return fallback


def dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, default=str)


def clamp(value: float, maximum: float) -> float:
    return round(max(0.0, min(float(value or 0), maximum)), 1)


def grade(score: float, max_score: float) -> str:
    pct = (score / max_score * 100) if max_score else 0
    if pct >= 85:
        return "EXCELLENT"
    if pct >= 70:
        return "STRONG"
    if pct >= 55:
        return "MODERATE"
    if pct >= 40:
        return "WEAK"
    return "INSUFFICIENT"


def module_payload(
    key: str,
    label: str,
    score: float,
    max_score: float,
    evidence: list[str],
    missing: list[str],
    reasons: dict[str, Any],
    recommendations: list[str],
    confidence: str = "medium",
    extra: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    final_score = clamp(score, max_score)
    normalized = round(final_score / max_score * 100, 1) if max_score else 0.0
    payload = {
        "key": key,
        "label": label,
        "score": final_score,
        "max_score": max_score,
        "normalized_score": normalized,
        "grade": grade(final_score, max_score),
        "confidence": confidence,
        "evidence_found": evidence,
        "missing_evidence": missing,
        "reasons": reasons,
        "recommendations": recommendations,
    }
    if extra:
        payload.update(extra)
    return {key: payload}


def skill_set(profile: dict[str, Any]) -> set[str]:
    keys = [
        "programming_languages",
        "frameworks_libraries",
        "databases",
        "cloud_devops_tools",
        "testing_tools",
        "architecture_practices",
    ]
    skills = set()
    for key in keys:
        skills.update(str(item).lower() for item in profile.get(key, []) if item)
    return skills
