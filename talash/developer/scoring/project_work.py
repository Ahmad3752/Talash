"""Project and work evidence scoring."""

from .state import DeveloperScoringState
from .utils import clamp, module_payload


def project_work_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    projects = p.get("projects", [])
    links = p.get("links", [])
    impact = [pr for pr in projects if pr.get("measurable_impact")]
    production = [pr for pr in projects if pr.get("production_evidence")]
    ownership = [pr for pr in projects if pr.get("ownership_signal")]

    complexity_score = min(7, len(projects) * 2.5)
    production_score = min(6, len(production) * 3)
    impact_score = min(5, len(impact) * 2.5)
    ownership_score = min(4, len(ownership) * 2)
    link_score = min(3, len(links) * 1.5)
    score = complexity_score + production_score + impact_score + ownership_score + link_score

    evidence = [f"{len(projects)} project/work evidence item(s) extracted."] if projects else []
    if links:
        evidence.append(f"Links detected: {', '.join(links[:4])}")

    missing = []
    if not projects:
        missing.append("No clear developer projects were extracted.")
    if not impact:
        missing.append("No measurable impact evidence detected.")
    if not production:
        missing.append("No production/deployment evidence detected.")
    if not links:
        missing.append("No GitHub, portfolio, or deployed project links detected.")

    return {"module_scores": module_payload(
        "project_work_evidence", "Project & Work Evidence", score, 25,
        evidence, missing,
        {
            "complexity_score": clamp(complexity_score, 7),
            "production_evidence_score": clamp(production_score, 6),
            "measurable_impact_score": clamp(impact_score, 5),
            "ownership_score": clamp(ownership_score, 4),
            "link_evidence_score": clamp(link_score, 3),
        },
        ["Add 2-3 strong projects with tech stack, ownership, links, and measurable results."],
        "medium" if projects else "low",
    )}
