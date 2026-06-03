"""Developer evaluation orchestration services."""

import json
from typing import Iterable, Optional

from ..db_connect import get_session
from ..db_models import Candidate
from .extraction import extract_developer_profile, profile_to_storage
from .models import DeveloperProfile, DeveloperScoreSummary


def _candidate_ids_from_results(results: Iterable[dict]) -> list[str]:
    ids = []
    seen = set()
    for result in results or []:
        if not result or "error" in result:
            continue
        candidate_id = result.get("_candidate_id")
        if candidate_id and candidate_id not in seen:
            seen.add(candidate_id)
            ids.append(candidate_id)
    return ids


def _starter_summary_payload(profile: DeveloperProfile) -> dict:
    return {
        "phase": "developer_profile_extraction",
        "status": "profile_extracted_scoring_pending",
        "message": "Developer profile extracted. Module scoring agents have not run yet.",
        "developer_profile_id": profile.id,
        "target_role": profile.target_role,
    }


def _developer_summary_for_candidate(candidate_id: int) -> dict:
    session = get_session()
    try:
        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=candidate_id).first()
        if not summary:
            return {}
        try:
            module_scores = json.loads(summary.module_summary or "[]")
        except Exception:
            module_scores = []
        return {
            "overall_score": summary.overall_score,
            "overall_grade": summary.overall_grade,
            "module_scores": module_scores,
        }
    finally:
        session.close()


def save_developer_profile_for_candidate(candidate: Candidate, target_role: str) -> DeveloperProfile:
    """Extract and upsert a developer profile for one candidate."""
    return save_developer_profile_for_candidate_id(candidate.id, target_role)


def save_developer_profile_for_candidate_id(candidate_id: int, target_role: str) -> DeveloperProfile:
    """Extract and upsert a developer profile for one candidate database id."""
    session = get_session()
    try:
        db_candidate = session.query(Candidate).filter_by(id=candidate_id).first()
        if not db_candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        extracted = extract_developer_profile(db_candidate, target_role)
        storage = profile_to_storage(extracted)

        profile = session.query(DeveloperProfile).filter_by(candidate_id=db_candidate.id).first()
        if profile is None:
            profile = DeveloperProfile(candidate_id=db_candidate.id, target_role=target_role)
            session.add(profile)
            session.flush()

        for field, value in storage.items():
            setattr(profile, field, value)

        session.flush()

        summary = session.query(DeveloperScoreSummary).filter_by(candidate_id=db_candidate.id).first()
        if summary is None:
            summary = DeveloperScoreSummary(
                candidate_id=db_candidate.id,
                developer_profile_id=profile.id,
                selected_role=target_role,
                overall_score=0.0,
                overall_grade="PENDING",
                hiring_recommendation="Scoring pending",
                confidence=profile.extraction_confidence,
                is_complete=False,
            )
            session.add(summary)
        else:
            summary.developer_profile_id = profile.id
            summary.selected_role = target_role
            summary.overall_score = summary.overall_score or 0.0
            summary.overall_grade = "PENDING"
            summary.hiring_recommendation = "Scoring pending"
            summary.confidence = profile.extraction_confidence
            summary.is_complete = False

        starter_payload = _starter_summary_payload(profile)
        summary.raw_summary_json = json.dumps(starter_payload, ensure_ascii=True)
        summary.module_summary = json.dumps([], ensure_ascii=True)
        summary.explainability_report = json.dumps(starter_payload, ensure_ascii=True)

        session.commit()
        session.refresh(profile)
        profile_id = profile.id
        from .scoring import save_developer_scoring

        save_developer_scoring(profile_id)
        return profile
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_developer_profile_extraction(
    pipeline_results: Iterable[dict],
    target_role: Optional[str],
) -> list[dict]:
    """Run Phase 3 developer extraction for all successful processed CVs."""
    if not target_role:
        return []

    candidate_ids = _candidate_ids_from_results(pipeline_results)
    if not candidate_ids:
        return []

    session = get_session()
    try:
        candidates = (
            session.query(Candidate)
            .filter(Candidate.candidate_id.in_(candidate_ids))
            .all()
        )
        candidate_by_public_id = {candidate.candidate_id: candidate for candidate in candidates}
    finally:
        session.close()

    saved = []
    for public_id in candidate_ids:
        candidate = candidate_by_public_id.get(public_id)
        if not candidate:
            saved.append({
                "candidate_id": public_id,
                "status": "skipped",
                "reason": "Candidate not found in database",
            })
            continue
        try:
            profile = save_developer_profile_for_candidate(candidate, target_role)
            summary = _developer_summary_for_candidate(candidate.id)
            saved.append({
                "candidate_id": public_id,
                "database_id": candidate.id,
                "developer_profile_id": profile.id,
                "target_role": profile.target_role,
                "overall_score": summary.get("overall_score"),
                "overall_grade": summary.get("overall_grade"),
                "module_scores": summary.get("module_scores", []),
                "status": "scored",
            })
        except Exception as e:
            saved.append({
                "candidate_id": public_id,
                "database_id": candidate.id,
                "status": "error",
                "reason": str(e),
            })

    return saved
