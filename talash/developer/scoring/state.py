"""Developer scoring graph state."""

from typing import Annotated, Any, TypedDict


def merge_dict(left: dict, right: dict) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


class DeveloperScoringState(TypedDict, total=False):
    profile_payload: dict[str, Any]
    module_scores: Annotated[dict[str, dict[str, Any]], merge_dict]
    summary: dict[str, Any]
