"""SQLAlchemy models for developer CV evaluation.

These tables intentionally live outside the existing researcher scoring tables.
They keep developer extraction, module scores, and final summaries isolated so
the researcher pipeline can remain stable while the developer pipeline evolves.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..db_models import Base


class DeveloperProfile(Base):
    """Structured developer profile extracted from a CV."""

    __tablename__ = "developer_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True)

    target_role = Column(String, nullable=False)
    current_role = Column(String)
    seniority_level = Column(String)
    total_relevant_experience_months = Column(Integer)

    programming_languages = Column(Text)      # JSON list
    frameworks_libraries = Column(Text)       # JSON list
    databases = Column(Text)                  # JSON list
    cloud_devops_tools = Column(Text)         # JSON list
    testing_tools = Column(Text)              # JSON list
    architecture_practices = Column(Text)     # JSON list
    projects = Column(Text)                   # JSON list of structured projects
    work_highlights = Column(Text)            # JSON list
    links = Column(Text)                      # JSON list
    certifications = Column(Text)             # JSON list
    extraction_warnings = Column(Text)        # JSON list
    raw_profile_json = Column(Text)           # complete extraction payload

    extraction_confidence = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate")


class DeveloperScoreMixin:
    """Common explainability fields used by every developer score table."""

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    developer_profile_id = Column(Integer, ForeignKey("developer_profiles.id"))

    score = Column(Float, nullable=False, default=0.0)
    max_score = Column(Float, nullable=False)
    normalized_score = Column(Float)
    grade = Column(String)
    confidence = Column(String)

    evidence_found = Column(Text)       # JSON list
    missing_evidence = Column(Text)     # JSON list
    reasons = Column(Text)              # JSON object/list
    recommendations = Column(Text)      # JSON list
    raw_json = Column(Text)             # complete agent output

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeveloperTechnicalSkillScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_technical_skill_scores"

    language_match_score = Column(Float)
    framework_match_score = Column(Float)
    database_match_score = Column(Float)
    api_skill_score = Column(Float)
    cloud_devops_score = Column(Float)
    skill_evidence_score = Column(Float)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperProjectWorkScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_project_work_scores"

    complexity_score = Column(Float)
    production_evidence_score = Column(Float)
    measurable_impact_score = Column(Float)
    ownership_score = Column(Float)
    link_evidence_score = Column(Float)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperExperienceScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_experience_scores"

    duration_score = Column(Float)
    seniority_progression_score = Column(Float)
    role_relevance_score = Column(Float)
    tenure_consistency_score = Column(Float)
    gap_overlap_clarity_score = Column(Float)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperEngineeringPracticeScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_engineering_practice_scores"

    testing_score = Column(Float)
    version_control_score = Column(Float)
    architecture_score = Column(Float)
    ci_cd_score = Column(Float)
    security_performance_score = Column(Float)
    documentation_workflow_score = Column(Float)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperRoleFitScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_role_fit_scores"

    selected_role = Column(String, nullable=False)
    role_requirement_scores = Column(Text)    # JSON object

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperEducationCertificationScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_education_certification_scores"

    degree_relevance_score = Column(Float)
    certification_score = Column(Float)
    continuous_learning_score = Column(Float)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperCVQualityScore(DeveloperScoreMixin, Base):
    __tablename__ = "developer_cv_quality_scores"

    structure_score = Column(Float)
    project_detail_score = Column(Float)
    measurable_achievement_score = Column(Float)
    link_contact_score = Column(Float)
    consistency_score = Column(Float)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")


class DeveloperScoreSummary(Base):
    """Final aggregated developer evaluation summary."""

    __tablename__ = "developer_score_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True)
    developer_profile_id = Column(Integer, ForeignKey("developer_profiles.id"))

    selected_role = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False, default=0.0)
    overall_grade = Column(String)
    hiring_recommendation = Column(String)
    confidence = Column(String)

    technical_skill_score = Column(Float)
    project_work_score = Column(Float)
    experience_score = Column(Float)
    engineering_practice_score = Column(Float)
    role_fit_score = Column(Float)
    education_certification_score = Column(Float)
    cv_quality_score = Column(Float)

    top_strengths = Column(Text)          # JSON list
    top_weaknesses = Column(Text)         # JSON list
    recommendations = Column(Text)        # JSON list
    module_summary = Column(Text)         # JSON list
    explainability_report = Column(Text)  # full human-readable report JSON
    raw_summary_json = Column(Text)       # complete aggregation payload

    is_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate")
    developer_profile = relationship("DeveloperProfile")

