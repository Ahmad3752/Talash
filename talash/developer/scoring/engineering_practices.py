"""Engineering practices scoring."""

from .state import DeveloperScoringState
from .utils import clamp, module_payload, skill_set


def engineering_practices_agent(state: DeveloperScoringState) -> dict:
    p = state["profile_payload"]
    skills = skill_set(p)
    testing_tools = {str(x).lower() for x in p.get("testing_tools", [])}
    cloud_tools = {str(x).lower() for x in p.get("cloud_devops_tools", [])}
    practices = {str(x).lower() for x in p.get("architecture_practices", [])}

    testing_score = 3 if testing_tools else 0
    version_score = 2 if any(k in skills for k in {"git", "github", "gitlab"}) or p.get("links") else 1 if p.get("projects") else 0
    architecture_score = min(3, len(practices & {"api", "rest", "graphql", "microservices", "mvc", "clean architecture"}) * 1.5)
    ci_cd_score = 2 if any(k in cloud_tools for k in {"github actions", "gitlab ci", "jenkins", "ci/cd"}) else 0
    security_perf_score = min(3, len(practices & {"security", "performance", "scalability", "authentication", "authorization"}) * 1)
    doc_score = 2 if "documentation" in practices else 0
    score = testing_score + version_score + architecture_score + ci_cd_score + security_perf_score + doc_score

    evidence = []
    if testing_tools:
        evidence.append(f"Testing tools: {', '.join(sorted(testing_tools))}")
    if practices:
        evidence.append(f"Engineering practices: {', '.join(sorted(practices)[:8])}")

    missing = []
    if not testing_tools:
        missing.append("No testing evidence detected.")
    if not ci_cd_score:
        missing.append("No CI/CD evidence detected.")
    if not security_perf_score:
        missing.append("No security/performance/scalability evidence detected.")

    return {"module_scores": module_payload(
        "engineering_practices", "Engineering Practices", score, 15,
        evidence, missing,
        {
            "testing_score": testing_score,
            "version_control_score": version_score,
            "architecture_score": clamp(architecture_score, 3),
            "ci_cd_score": ci_cd_score,
            "security_performance_score": clamp(security_perf_score, 3),
            "documentation_workflow_score": doc_score,
        },
        ["Mention testing, CI/CD, architecture, security, and performance work explicitly."],
        "medium" if evidence else "low",
    )}
