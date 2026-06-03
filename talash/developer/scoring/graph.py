"""LangGraph assembly for developer scoring."""

from langgraph.graph import END, START, StateGraph

from .aggregate import aggregate_agent
from .cv_quality import cv_quality_agent
from .education_certifications import education_certifications_agent
from .engineering_practices import engineering_practices_agent
from .experience import experience_agent
from .profile_payload import profile_to_payload
from .project_work import project_work_agent
from .role_fit import role_fit_agent
from .state import DeveloperScoringState
from .technical_skill import technical_skill_agent


_graph = StateGraph(DeveloperScoringState)
_graph.add_node("technical_skill_agent", technical_skill_agent)
_graph.add_node("project_work_agent", project_work_agent)
_graph.add_node("experience_agent", experience_agent)
_graph.add_node("engineering_practices_agent", engineering_practices_agent)
_graph.add_node("role_fit_agent", role_fit_agent)
_graph.add_node("education_certifications_agent", education_certifications_agent)
_graph.add_node("cv_quality_agent", cv_quality_agent)
_graph.add_node("aggregate_agent", aggregate_agent)

for node in [
    "technical_skill_agent",
    "project_work_agent",
    "experience_agent",
    "engineering_practices_agent",
    "role_fit_agent",
    "education_certifications_agent",
    "cv_quality_agent",
]:
    _graph.add_edge(START, node)
    _graph.add_edge(node, "aggregate_agent")

_graph.add_edge("aggregate_agent", END)
developer_scoring_graph = _graph.compile()


def run_developer_scoring(profile) -> dict:
    result = developer_scoring_graph.invoke({"profile_payload": profile_to_payload(profile), "module_scores": {}})
    return {
        "module_scores": result.get("module_scores", {}),
        "summary": result.get("summary", {}),
    }
