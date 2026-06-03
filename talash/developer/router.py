"""Read-only developer evaluation API endpoints for Phase 2."""

from fastapi import APIRouter, HTTPException, Query

from ..db_connect import get_session
from ..db_models import Candidate
from .constants import DEVELOPER_ROLES
from .validation import normalize_upload_track
from .models import (
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
from .schemas import (
    DeveloperCVQualityScoreSchema,
    DeveloperEducationCertificationScoreSchema,
    DeveloperEngineeringPracticeScoreSchema,
    DeveloperExperienceScoreSchema,
    DeveloperProfileSchema,
    DeveloperProjectWorkScoreSchema,
    DeveloperRoleFitScoreSchema,
    DeveloperRoleSchema,
    DeveloperScoresBundleSchema,
    DeveloperScoreSummarySchema,
    DeveloperScoringStatusSchema,
    DeveloperTechnicalSkillScoreSchema,
)

router = APIRouter(prefix="/developer", tags=["Developer Evaluation"])


def _orm_to_schema(orm_obj, schema_cls):
    return schema_cls.model_validate(orm_obj).model_dump()


def _require_candidate(session, candidate_id: int) -> Candidate:
    candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return candidate


@router.get("/roles", response_model=list[DeveloperRoleSchema])
async def list_developer_roles():
    """Return developer roles supported by the scoring rubric."""
    return [
        DeveloperRoleSchema(value=value, label=label)
        for value, label in DEVELOPER_ROLES.items()
    ]


@router.get("/candidates/{candidate_id}/status", response_model=DeveloperScoringStatusSchema)
async def get_developer_scoring_status(candidate_id: int):
    session = get_session()
    try:
        _require_candidate(session, candidate_id)
        profile = session.query(DeveloperProfile).filter_by(candidate_id=candidate_id).first()
        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=candidate_id).first()

        if summary and summary.is_complete:
            status = "complete"
        elif profile or summary:
            status = "in_progress"
        else:
            status = "not_started"

        return DeveloperScoringStatusSchema(
            candidate_id=candidate_id,
            has_profile=profile is not None,
            has_summary=summary is not None,
            is_complete=bool(summary and summary.is_complete),
            selected_role=(summary.selected_role if summary else profile.target_role if profile else None),
            status=status,
        )
    finally:
        session.close()


@router.get("/candidates/{candidate_id}/profile", response_model=DeveloperProfileSchema)
async def get_developer_profile(candidate_id: int):
    session = get_session()
    try:
        _require_candidate(session, candidate_id)
        profile = session.query(DeveloperProfile).filter_by(candidate_id=candidate_id).first()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"No developer profile for candidate {candidate_id}",
            )
        return _orm_to_schema(profile, DeveloperProfileSchema)
    finally:
        session.close()


@router.post("/candidates/{candidate_id}/extract", response_model=DeveloperProfileSchema)
async def extract_developer_profile_for_candidate(
    candidate_id: int,
    target_role: str = Query(..., description="Developer role key, for example backend or full_stack"),
):
    """Run Phase 3 developer profile extraction for an existing candidate."""
    try:
        _, normalized_role = normalize_upload_track("developer", target_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session = get_session()
    try:
        candidate = _require_candidate(session, candidate_id)
        detached_candidate_id = candidate.id
    finally:
        session.close()

    from .service import save_developer_profile_for_candidate_id

    profile = save_developer_profile_for_candidate_id(detached_candidate_id, normalized_role)
    return DeveloperProfileSchema.model_validate(profile)


@router.post("/profiles/{profile_id}/score", response_model=DeveloperScoreSummarySchema)
async def score_developer_profile(profile_id: int):
    """Run Phase 4-5 developer scoring for an existing developer profile."""
    from .scoring import save_developer_scoring

    try:
        save_developer_scoring(profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Developer scoring failed: {e}")

    session = get_session()
    try:
        profile = session.query(DeveloperProfile).filter_by(id=profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail=f"Developer profile {profile_id} not found")
        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=profile.candidate_id).first()
        if not summary:
            raise HTTPException(status_code=404, detail=f"No developer score summary for profile {profile_id}")
        return _orm_to_schema(summary, DeveloperScoreSummarySchema)
    finally:
        session.close()


@router.get("/candidates/{candidate_id}/summary", response_model=DeveloperScoreSummarySchema)
async def get_developer_score_summary(candidate_id: int):
    session = get_session()
    try:
        _require_candidate(session, candidate_id)
        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=candidate_id).first()
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"No developer score summary for candidate {candidate_id}",
            )
        return _orm_to_schema(summary, DeveloperScoreSummarySchema)
    finally:
        session.close()


@router.get("/candidates/{candidate_id}/scores", response_model=DeveloperScoresBundleSchema)
async def get_developer_scores(candidate_id: int):
    session = get_session()
    try:
        _require_candidate(session, candidate_id)
        profile = session.query(DeveloperProfile).filter_by(candidate_id=candidate_id).first()
        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=candidate_id).first()

        return DeveloperScoresBundleSchema(
            profile=DeveloperProfileSchema.model_validate(profile) if profile else None,
            summary=DeveloperScoreSummarySchema.model_validate(summary) if summary else None,
            technical_skill_scores=[
                DeveloperTechnicalSkillScoreSchema.model_validate(row)
                for row in session.query(DeveloperTechnicalSkillScore).filter_by(candidate_id=candidate_id).all()
            ],
            project_work_scores=[
                DeveloperProjectWorkScoreSchema.model_validate(row)
                for row in session.query(DeveloperProjectWorkScore).filter_by(candidate_id=candidate_id).all()
            ],
            experience_scores=[
                DeveloperExperienceScoreSchema.model_validate(row)
                for row in session.query(DeveloperExperienceScore).filter_by(candidate_id=candidate_id).all()
            ],
            engineering_practice_scores=[
                DeveloperEngineeringPracticeScoreSchema.model_validate(row)
                for row in session.query(DeveloperEngineeringPracticeScore).filter_by(candidate_id=candidate_id).all()
            ],
            role_fit_scores=[
                DeveloperRoleFitScoreSchema.model_validate(row)
                for row in session.query(DeveloperRoleFitScore).filter_by(candidate_id=candidate_id).all()
            ],
            education_certification_scores=[
                DeveloperEducationCertificationScoreSchema.model_validate(row)
                for row in session.query(DeveloperEducationCertificationScore).filter_by(candidate_id=candidate_id).all()
            ],
            cv_quality_scores=[
                DeveloperCVQualityScoreSchema.model_validate(row)
                for row in session.query(DeveloperCVQualityScore).filter_by(candidate_id=candidate_id).all()
            ],
        )
    finally:
        session.close()
