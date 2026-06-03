"""Pydantic schemas for developer CV evaluation APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeveloperRoleSchema(BaseModel):
    value: str
    label: str


class DeveloperProfileSchema(BaseModel):
    id: int
    candidate_id: int
    target_role: str
    current_role: Optional[str] = None
    seniority_level: Optional[str] = None
    total_relevant_experience_months: Optional[int] = None
    programming_languages: Optional[str] = None
    frameworks_libraries: Optional[str] = None
    databases: Optional[str] = None
    cloud_devops_tools: Optional[str] = None
    testing_tools: Optional[str] = None
    architecture_practices: Optional[str] = None
    projects: Optional[str] = None
    work_highlights: Optional[str] = None
    links: Optional[str] = None
    certifications: Optional[str] = None
    extraction_warnings: Optional[str] = None
    raw_profile_json: Optional[str] = None
    extraction_confidence: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeveloperModuleScoreSchema(BaseModel):
    id: int
    candidate_id: int
    developer_profile_id: Optional[int] = None
    score: float
    max_score: float
    normalized_score: Optional[float] = None
    grade: Optional[str] = None
    confidence: Optional[str] = None
    evidence_found: Optional[str] = None
    missing_evidence: Optional[str] = None
    reasons: Optional[str] = None
    recommendations: Optional[str] = None
    raw_json: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeveloperTechnicalSkillScoreSchema(DeveloperModuleScoreSchema):
    language_match_score: Optional[float] = None
    framework_match_score: Optional[float] = None
    database_match_score: Optional[float] = None
    api_skill_score: Optional[float] = None
    cloud_devops_score: Optional[float] = None
    skill_evidence_score: Optional[float] = None


class DeveloperProjectWorkScoreSchema(DeveloperModuleScoreSchema):
    complexity_score: Optional[float] = None
    production_evidence_score: Optional[float] = None
    measurable_impact_score: Optional[float] = None
    ownership_score: Optional[float] = None
    link_evidence_score: Optional[float] = None


class DeveloperExperienceScoreSchema(DeveloperModuleScoreSchema):
    duration_score: Optional[float] = None
    seniority_progression_score: Optional[float] = None
    role_relevance_score: Optional[float] = None
    tenure_consistency_score: Optional[float] = None
    gap_overlap_clarity_score: Optional[float] = None


class DeveloperEngineeringPracticeScoreSchema(DeveloperModuleScoreSchema):
    testing_score: Optional[float] = None
    version_control_score: Optional[float] = None
    architecture_score: Optional[float] = None
    ci_cd_score: Optional[float] = None
    security_performance_score: Optional[float] = None
    documentation_workflow_score: Optional[float] = None


class DeveloperRoleFitScoreSchema(DeveloperModuleScoreSchema):
    selected_role: str
    role_requirement_scores: Optional[str] = None


class DeveloperEducationCertificationScoreSchema(DeveloperModuleScoreSchema):
    degree_relevance_score: Optional[float] = None
    certification_score: Optional[float] = None
    continuous_learning_score: Optional[float] = None


class DeveloperCVQualityScoreSchema(DeveloperModuleScoreSchema):
    structure_score: Optional[float] = None
    project_detail_score: Optional[float] = None
    measurable_achievement_score: Optional[float] = None
    link_contact_score: Optional[float] = None
    consistency_score: Optional[float] = None


class DeveloperScoreSummarySchema(BaseModel):
    id: int
    candidate_id: int
    developer_profile_id: Optional[int] = None
    selected_role: str
    overall_score: float
    overall_grade: Optional[str] = None
    hiring_recommendation: Optional[str] = None
    confidence: Optional[str] = None
    technical_skill_score: Optional[float] = None
    project_work_score: Optional[float] = None
    experience_score: Optional[float] = None
    engineering_practice_score: Optional[float] = None
    role_fit_score: Optional[float] = None
    education_certification_score: Optional[float] = None
    cv_quality_score: Optional[float] = None
    top_strengths: Optional[str] = None
    top_weaknesses: Optional[str] = None
    recommendations: Optional[str] = None
    module_summary: Optional[str] = None
    explainability_report: Optional[str] = None
    raw_summary_json: Optional[str] = None
    is_complete: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeveloperScoresBundleSchema(BaseModel):
    profile: Optional[DeveloperProfileSchema] = None
    summary: Optional[DeveloperScoreSummarySchema] = None
    technical_skill_scores: List[DeveloperTechnicalSkillScoreSchema] = Field(default_factory=list)
    project_work_scores: List[DeveloperProjectWorkScoreSchema] = Field(default_factory=list)
    experience_scores: List[DeveloperExperienceScoreSchema] = Field(default_factory=list)
    engineering_practice_scores: List[DeveloperEngineeringPracticeScoreSchema] = Field(default_factory=list)
    role_fit_scores: List[DeveloperRoleFitScoreSchema] = Field(default_factory=list)
    education_certification_scores: List[DeveloperEducationCertificationScoreSchema] = Field(default_factory=list)
    cv_quality_scores: List[DeveloperCVQualityScoreSchema] = Field(default_factory=list)


class DeveloperScoringStatusSchema(BaseModel):
    candidate_id: int
    has_profile: bool
    has_summary: bool
    is_complete: bool
    selected_role: Optional[str] = None
    status: str

