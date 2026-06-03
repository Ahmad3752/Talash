"""Persistence for developer scoring results."""

from typing import Any

from ...db_connect import get_session
from ..models import (
    DeveloperCVQualityScore,
    DeveloperEducationCertificationScore,
    DeveloperEngineeringPracticeScore,
    DeveloperExperienceScore,
    DeveloperProfile,
    DeveloperProjectWorkScore,
    DeveloperRoleFitScore,
    DeveloperScoreSummary,
    DeveloperTechnicalSkillScore,
)
from .graph import run_developer_scoring
from .utils import dump


def base_score_kwargs(profile: DeveloperProfile, module: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": profile.candidate_id,
        "developer_profile_id": profile.id,
        "score": module["score"],
        "max_score": module["max_score"],
        "normalized_score": module["normalized_score"],
        "grade": module["grade"],
        "confidence": module["confidence"],
        "evidence_found": dump(module["evidence_found"]),
        "missing_evidence": dump(module["missing_evidence"]),
        "reasons": dump(module["reasons"]),
        "recommendations": dump(module["recommendations"]),
        "raw_json": dump(module),
    }


def save_developer_scoring(profile_id: int) -> dict[str, Any]:
    session = get_session()
    try:
        profile = session.query(DeveloperProfile).filter_by(id=profile_id).first()
        if not profile:
            raise ValueError(f"Developer profile {profile_id} not found")

        result = run_developer_scoring(profile)
        modules = result["module_scores"]
        summary_payload = result["summary"]

        for model in [
            DeveloperTechnicalSkillScore,
            DeveloperProjectWorkScore,
            DeveloperExperienceScore,
            DeveloperEngineeringPracticeScore,
            DeveloperRoleFitScore,
            DeveloperEducationCertificationScore,
            DeveloperCVQualityScore,
        ]:
            session.query(model).filter_by(candidate_id=profile.candidate_id).delete()

        tech = modules["technical_skill_match"]
        session.add(DeveloperTechnicalSkillScore(
            **base_score_kwargs(profile, tech),
            language_match_score=tech["reasons"]["language_match_score"],
            framework_match_score=tech["reasons"]["framework_match_score"],
            database_match_score=tech["reasons"]["database_match_score"],
            api_skill_score=tech["reasons"]["api_skill_score"],
            cloud_devops_score=tech["reasons"]["cloud_devops_score"],
            skill_evidence_score=tech["reasons"]["skill_evidence_score"],
        ))

        project = modules["project_work_evidence"]
        session.add(DeveloperProjectWorkScore(
            **base_score_kwargs(profile, project),
            complexity_score=project["reasons"]["complexity_score"],
            production_evidence_score=project["reasons"]["production_evidence_score"],
            measurable_impact_score=project["reasons"]["measurable_impact_score"],
            ownership_score=project["reasons"]["ownership_score"],
            link_evidence_score=project["reasons"]["link_evidence_score"],
        ))

        exp = modules["professional_experience"]
        session.add(DeveloperExperienceScore(
            **base_score_kwargs(profile, exp),
            duration_score=exp["reasons"]["duration_score"],
            seniority_progression_score=exp["reasons"]["seniority_progression_score"],
            role_relevance_score=exp["reasons"]["role_relevance_score"],
            tenure_consistency_score=exp["reasons"]["tenure_consistency_score"],
            gap_overlap_clarity_score=exp["reasons"]["gap_overlap_clarity_score"],
        ))

        practices = modules["engineering_practices"]
        session.add(DeveloperEngineeringPracticeScore(
            **base_score_kwargs(profile, practices),
            testing_score=practices["reasons"]["testing_score"],
            version_control_score=practices["reasons"]["version_control_score"],
            architecture_score=practices["reasons"]["architecture_score"],
            ci_cd_score=practices["reasons"]["ci_cd_score"],
            security_performance_score=practices["reasons"]["security_performance_score"],
            documentation_workflow_score=practices["reasons"]["documentation_workflow_score"],
        ))

        role = modules["role_specific_fit"]
        session.add(DeveloperRoleFitScore(
            **base_score_kwargs(profile, role),
            selected_role=role["reasons"]["selected_role"],
            role_requirement_scores=dump(role["reasons"]["role_requirement_scores"]),
        ))

        edu = modules["education_certifications"]
        session.add(DeveloperEducationCertificationScore(
            **base_score_kwargs(profile, edu),
            degree_relevance_score=edu["reasons"]["degree_relevance_score"],
            certification_score=edu["reasons"]["certification_score"],
            continuous_learning_score=edu["reasons"]["continuous_learning_score"],
        ))

        quality = modules["cv_quality"]
        session.add(DeveloperCVQualityScore(
            **base_score_kwargs(profile, quality),
            structure_score=quality["reasons"]["structure_score"],
            project_detail_score=quality["reasons"]["project_detail_score"],
            measurable_achievement_score=quality["reasons"]["measurable_achievement_score"],
            link_contact_score=quality["reasons"]["link_contact_score"],
            consistency_score=quality["reasons"]["consistency_score"],
        ))

        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=profile.candidate_id).first()
        if summary is None:
            summary = DeveloperScoreSummary(candidate_id=profile.candidate_id)
            session.add(summary)

        summary.developer_profile_id = profile.id
        summary.selected_role = profile.target_role
        summary.overall_score = summary_payload["overall_score"]
        summary.overall_grade = summary_payload["overall_grade"]
        summary.hiring_recommendation = summary_payload["hiring_recommendation"]
        summary.confidence = summary_payload["confidence"]
        summary.technical_skill_score = modules["technical_skill_match"]["score"]
        summary.project_work_score = modules["project_work_evidence"]["score"]
        summary.experience_score = modules["professional_experience"]["score"]
        summary.engineering_practice_score = modules["engineering_practices"]["score"]
        summary.role_fit_score = modules["role_specific_fit"]["score"]
        summary.education_certification_score = modules["education_certifications"]["score"]
        summary.cv_quality_score = modules["cv_quality"]["score"]
        summary.top_strengths = dump(summary_payload["top_strengths"])
        summary.top_weaknesses = dump(summary_payload["top_weaknesses"])
        summary.recommendations = dump(summary_payload["recommendations"])
        summary.module_summary = dump(summary_payload["module_summary"])
        summary.explainability_report = dump(summary_payload)
        summary.raw_summary_json = dump({"modules": modules, "summary": summary_payload})
        summary.is_complete = True

        session.commit()
        return summary_payload
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
