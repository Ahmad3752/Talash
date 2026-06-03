"""Technical skill match scoring."""

from .requirements import ROLE_REQUIREMENTS
from .state import DeveloperScoringState
from .utils import clamp, module_payload


def technical_skill_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    languages = p.get("programming_languages", [])
    frameworks = p.get("frameworks_libraries", [])
    databases = p.get("databases", [])
    cloud = p.get("cloud_devops_tools", [])
    practices = p.get("architecture_practices", [])
    projects = p.get("projects", [])
    role = p.get("target_role")
    req = ROLE_REQUIREMENTS.get(role, ROLE_REQUIREMENTS["backend"])

    language_score = min(6, len({str(x).lower() for x in languages} & req["languages"]) * 3)
    framework_score = min(5, len({str(x).lower() for x in frameworks} & req["frameworks"]) * 2.5)
    database_score = 4 if databases else 0
    api_score = 4 if any(str(x).lower() in {"api", "rest", "graphql"} for x in practices) else 0
    cloud_score = min(3, len(cloud) * 1.5)
    evidence_score = 3 if projects else 1 if languages or frameworks else 0
    score = language_score + framework_score + database_score + api_score + cloud_score + evidence_score

    evidence = []
    if languages:
        evidence.append(f"Programming languages detected: {', '.join(languages[:8])}")
    if frameworks:
        evidence.append(f"Frameworks/libraries detected: {', '.join(frameworks[:8])}")
    if databases:
        evidence.append(f"Database evidence detected: {', '.join(databases[:6])}")
    if cloud:
        evidence.append(f"Cloud/DevOps tools detected: {', '.join(cloud[:6])}")

    missing = []
    if not languages:
        missing.append("No programming languages detected.")
    if not frameworks:
        missing.append("No framework/library evidence detected.")
    if not databases:
        missing.append("No database evidence detected.")
    if not cloud:
        missing.append("No cloud or DevOps evidence detected.")

    return {"module_scores": module_payload(
        "technical_skill_match", "Technical Skill Match", score, 25,
        evidence, missing,
        {
            "language_match_score": clamp(language_score, 6),
            "framework_match_score": clamp(framework_score, 5),
            "database_match_score": clamp(database_score, 4),
            "api_skill_score": clamp(api_score, 4),
            "cloud_devops_score": clamp(cloud_score, 3),
            "skill_evidence_score": clamp(evidence_score, 3),
        },
        ["Add project-level evidence for listed skills.", "Mention databases, APIs, deployment, and testing where applicable."],
        "high" if evidence else "low",
    )}
