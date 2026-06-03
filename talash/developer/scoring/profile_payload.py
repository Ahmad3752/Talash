"""Convert stored developer profiles into scoring payloads."""

from typing import Any

from ..models import DeveloperProfile
from .utils import loads


def profile_to_payload(profile: DeveloperProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "candidate_id": profile.candidate_id,
        "target_role": profile.target_role,
        "current_role": profile.current_role,
        "seniority_level": profile.seniority_level,
        "total_relevant_experience_months": profile.total_relevant_experience_months,
        "programming_languages": loads(profile.programming_languages),
        "frameworks_libraries": loads(profile.frameworks_libraries),
        "databases": loads(profile.databases),
        "cloud_devops_tools": loads(profile.cloud_devops_tools),
        "testing_tools": loads(profile.testing_tools),
        "architecture_practices": loads(profile.architecture_practices),
        "projects": loads(profile.projects),
        "work_highlights": loads(profile.work_highlights),
        "links": loads(profile.links),
        "certifications": loads(profile.certifications),
        "extraction_warnings": loads(profile.extraction_warnings),
        "raw_profile_json": profile.raw_profile_json,
        "extraction_confidence": profile.extraction_confidence,
    }
