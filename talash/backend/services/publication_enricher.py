import html
import os
import re
import time
from typing import Dict, List

import requests


CROSSREF_BASE = "https://api.crossref.org/works"
CROSSREF_HEADERS = {
    "User-Agent": (
        f"CVEnrichmentBot/1.0 "
        f"(mailto:{os.getenv('CROSSREF_CONTACT_EMAIL', 'support@example.com')})"
    )
}

VALID_ROLES = {"first", "corresponding", "first_and_corresponding", "co_author"}
_GENERIC_VENUES = {
    "journal",
    "conference",
    "journal paper",
    "conference paper",
    "n/a",
    "na",
    "none",
    "unknown",
    "",
}


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _word_overlap(query: str, result: str) -> float:
    q_words = _tokenize(query)
    r_words = _tokenize(result)
    if not q_words:
        return 0.0
    return len(q_words & r_words) / max(len(q_words), 1)


def _first_value(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _infer_conference_maturity(name: str | None) -> str | None:
    if not name:
        return None
    lowered = name.lower()
    if "biennial" in lowered:
        return "Biennial"
    if "triennial" in lowered:
        return "Triennial"
    if "annual" in lowered:
        return "Annual"
    return None


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "n/a", "na", "none", "null", "unknown"}
    return False


def _is_generic_venue(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in _GENERIC_VENUES


def fetch_metadata_from_crossref(title: str, pub_type: str) -> Dict:
    if not title or not title.strip():
        return {}

    params = {
        "query.title": title.strip(),
        "rows": 5,
        "sort": "relevance",
        "order": "desc",
    }

    try:
        print(f"[CrossRef] lookup title={title!r}, pub_type={pub_type}")
        resp = requests.get(
            CROSSREF_BASE,
            headers=CROSSREF_HEADERS,
            params=params,
            timeout=8,
        )
        resp.raise_for_status()
        payload = resp.json() or {}
        items = payload.get("message", {}).get("items", [])

        for item in items:
            result_title = _first_value(item.get("title")) or ""
            overlap = _word_overlap(title, result_title)
            if overlap < 0.4:
                continue

            publisher = item.get("publisher")
            container_title = _first_value(item.get("container-title"))
            event_name = item.get("event", {}).get("name") if isinstance(item.get("event"), dict) else None
            conference_name = event_name or container_title if pub_type == "conference" else None

            metadata = {
                "doi": item.get("DOI"),
                "publisher": publisher,
                "issn": _first_value(item.get("ISSN")),
                "journal_name": container_title if pub_type == "journal" else None,
                "conference_name": conference_name,
                "conference_maturity": _infer_conference_maturity(conference_name),
                "proceedings_publisher": publisher if pub_type == "conference" else None,
            }
            print(
                "[CrossRef] match accepted "
                f"overlap={overlap:.2f}, doi={metadata.get('doi')}, venue={metadata.get('journal_name') or metadata.get('conference_name')}"
            )
            return metadata

    except requests.exceptions.Timeout:
        print(f"[CrossRef] timeout for title: {title}")
    except Exception as exc:
        print(f"[CrossRef] failed for '{title}': {exc}")

    return {}


def enrich_publications(publications: List[Dict]) -> List[Dict]:
    enriched: List[Dict] = []

    for pub in publications or []:
        item = dict(pub)
        pub_type = (item.get("type") or "journal").strip().lower()
        title = item.get("title")

        metadata = fetch_metadata_from_crossref(title or "", pub_type)
        updated_fields: List[str] = []

        if metadata:
            for key in [
                "doi",
                "publisher",
                "issn",
                "journal_name",
                "conference_name",
                "conference_maturity",
                "proceedings_publisher",
            ]:
                if _is_missing(item.get(key)) and not _is_missing(metadata.get(key)):
                    item[key] = metadata.get(key)
                    updated_fields.append(key)

            if _is_generic_venue(item.get("venue")):
                venue_value = metadata.get("journal_name") or metadata.get("conference_name")
                if venue_value:
                    item["venue"] = html.unescape(venue_value)
                    updated_fields.append("venue")

        if updated_fields:
            print(f"[CrossRef] enriched {title!r}: {', '.join(sorted(set(updated_fields)))}")
        else:
            print(f"[CrossRef] no enrichment for {title!r}")

        enriched.append(item)
        time.sleep(0.1)

    return enriched


def infer_authorship_roles(publications: List[Dict], candidate_name: str) -> List[Dict]:
    tokens = [t for t in re.findall(r"[a-z]+", (candidate_name or "").lower()) if len(t) > 1]
    anchor = tokens[-1] if tokens else ""

    def name_matches(author_name: str) -> bool:
        normalized = (author_name or "").lower()
        if not anchor:
            return False
        return anchor in normalized

    inferred_publications: List[Dict] = []
    for pub in publications or []:
        item = dict(pub)

        authors = item.get("authors") or []
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(",") if a.strip()]

        if not authors:
            inferred_publications.append(item)
            continue

        role = item.get("authorship_role")
        first_match = name_matches(authors[0])
        last_match = name_matches(authors[-1])
        any_match = any(name_matches(a) for a in authors)
        prev_role = role

        if len(authors) == 1 and first_match:
            item["authorship_role"] = "first_and_corresponding"
        elif first_match and last_match:
            item["authorship_role"] = "first_and_corresponding"
        elif first_match:
            item["authorship_role"] = "first"
        elif last_match:
            item["authorship_role"] = "corresponding"
        elif any_match:
            item["authorship_role"] = "co_author"

        if prev_role in VALID_ROLES and item.get("authorship_role") in VALID_ROLES and prev_role != item.get("authorship_role"):
            print(
                f"[authorship] corrected role for {item.get('title')!r}: "
                f"{prev_role} -> {item.get('authorship_role')}"
            )
        elif item.get("authorship_role") in VALID_ROLES:
            print(
                f"[authorship] role for {item.get('title')!r}: {item.get('authorship_role')} "
                f"(first_match={first_match}, last_match={last_match}, authors={len(authors)})"
            )

        inferred_publications.append(item)

    return inferred_publications
