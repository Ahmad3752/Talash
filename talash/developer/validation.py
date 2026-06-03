"""Validation helpers for developer evaluation requests."""

from typing import Optional

from .constants import ALLOWED_DEVELOPER_ROLES, ALLOWED_EVALUATION_TRACKS


def normalize_upload_track(
    evaluation_track: str,
    developer_role: Optional[str],
) -> tuple[str, Optional[str]]:
    """Normalize and validate upload track metadata.

    Raises ValueError with an API-safe message when the selection is invalid.
    """
    track = (evaluation_track or "researcher").strip().lower()
    role = (developer_role or "").strip().lower() or None

    if track not in ALLOWED_EVALUATION_TRACKS:
        raise ValueError("evaluation_track must be either 'researcher' or 'developer'")

    if track == "developer":
        if not role:
            raise ValueError("developer_role is required when evaluation_track is 'developer'")
        if role not in ALLOWED_DEVELOPER_ROLES:
            allowed = ", ".join(sorted(ALLOWED_DEVELOPER_ROLES))
            raise ValueError(f"developer_role must be one of: {allowed}")
    else:
        role = None

    return track, role

