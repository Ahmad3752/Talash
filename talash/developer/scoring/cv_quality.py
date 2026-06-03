"""CV quality and communication scoring."""

from .state import DeveloperScoringState
from .utils import clamp, module_payload


def cv_quality_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    warnings = p.get("extraction_warnings", [])
    projects = p.get("projects", [])
    links = p.get("links", [])
    highlights = p.get("work_highlights", [])
    has_impact = any(pr.get("measurable_impact") for pr in projects)

    structure_score = 1 if p.get("current_role") or p.get("programming_languages") else 0
    project_detail_score = 1.5 if projects else 0
    achievement_score = 1 if has_impact else 0
    link_score = 1 if links else 0
    consistency_score = 0.5 if len(warnings) <= 2 and (projects or highlights) else 0
    score = structure_score + project_detail_score + achievement_score + link_score + consistency_score

    evidence = []
    if projects:
        evidence.append("Project/work detail is present.")
    if links:
        evidence.append("Candidate links are present.")

    missing = list(warnings[:4])
    if not has_impact:
        missing.append("No measurable achievements detected.")

    return {"module_scores": module_payload(
        "cv_quality", "CV Quality & Communication", score, 5,
        evidence, missing,
        {
            "structure_score": clamp(structure_score, 1),
            "project_detail_score": clamp(project_detail_score, 1.5),
            "measurable_achievement_score": clamp(achievement_score, 1),
            "link_contact_score": clamp(link_score, 1),
            "consistency_score": clamp(consistency_score, 0.5),
        },
        ["Improve CV by adding project links, measurable impact, and clearer project descriptions."],
        "medium" if evidence else "low",
    )}
