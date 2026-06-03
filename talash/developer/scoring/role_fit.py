"""Role-specific fit scoring."""

from ..constants import DEVELOPER_ROLES
from .requirements import ROLE_REQUIREMENTS
from .state import DeveloperScoringState
from .utils import module_payload


def role_fit_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    role = p.get("target_role") or "backend"
    req = ROLE_REQUIREMENTS.get(role, ROLE_REQUIREMENTS["backend"])
    languages = {str(x).lower() for x in p.get("programming_languages", [])}
    frameworks = {str(x).lower() for x in p.get("frameworks_libraries", [])}
    databases = {str(x).lower() for x in p.get("databases", [])}
    practices = {str(x).lower() for x in p.get("architecture_practices", [])}
    cloud = {str(x).lower() for x in p.get("cloud_devops_tools", [])}

    requirement_scores = {
        "language_fit": 2 if languages & req["languages"] else 0,
        "framework_fit": 2 if frameworks & req["frameworks"] else 0,
        "database_fit": 2 if not req["databases"] or databases & req["databases"] else 0,
        "practice_fit": 2 if practices & req["practices"] else 0,
        "deployment_or_delivery_fit": 2 if cloud or p.get("links") else 0,
    }
    score = sum(requirement_scores.values())
    label = DEVELOPER_ROLES.get(role, role)
    evidence = [f"Role evaluated as {label}."] if score else []
    missing = [name.replace("_", " ") for name, val in requirement_scores.items() if val == 0]

    return {"module_scores": module_payload(
        "role_specific_fit", "Role-Specific Fit", score, 10,
        evidence, missing,
        {"selected_role": role, "role_requirement_scores": requirement_scores},
        [f"Add evidence that maps directly to {label} requirements."],
        "medium",
    )}
