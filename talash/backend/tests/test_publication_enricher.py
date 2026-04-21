from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import services.publication_enricher as enricher


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_fetch_metadata_from_crossref_applies_overlap_guard(monkeypatch):
    payload = {
        "message": {
            "items": [
                {
                    "title": ["Completely Different Topic"],
                    "DOI": "10.bad/skip",
                    "publisher": "Bad Publisher",
                },
                {
                    "title": ["Deep Learning for Medical Image Segmentation"],
                    "DOI": "10.1000/xyz123",
                    "publisher": "Elsevier BV",
                    "ISSN": ["1234-5678"],
                    "container-title": ["Medical Image Analysis"],
                },
            ]
        }
    }

    monkeypatch.setattr(enricher.requests, "get", lambda *args, **kwargs: _FakeResponse(payload))

    data = enricher.fetch_metadata_from_crossref(
        "Deep Learning for Medical Image Segmentation",
        "journal",
    )

    assert data["doi"] == "10.1000/xyz123"
    assert data["publisher"] == "Elsevier BV"
    assert data["journal_name"] == "Medical Image Analysis"


def test_enrich_publications_does_not_overwrite_existing_values(monkeypatch):
    monkeypatch.setattr(enricher.time, "sleep", lambda *_: None)
    monkeypatch.setattr(
        enricher,
        "fetch_metadata_from_crossref",
        lambda title, pub_type: {
            "doi": "10.2000/new-doi",
            "publisher": "Springer",
            "issn": "1111-2222",
            "journal_name": "Journal of Testing",
            "conference_name": None,
            "conference_maturity": None,
            "proceedings_publisher": None,
        },
    )

    pubs = [
        {
            "type": "journal",
            "title": "A study",
            "doi": "10.1000/original-doi",
            "publisher": "Existing Publisher",
            "venue": "journal",
        }
    ]

    out = enricher.enrich_publications(pubs)

    assert out[0]["doi"] == "10.1000/original-doi"
    assert out[0]["publisher"] == "Existing Publisher"
    assert out[0]["journal_name"] == "Journal of Testing"
    assert out[0]["venue"] == "Journal of Testing"


def test_infer_authorship_roles_assigns_expected_roles():
    publications = [
        {
            "title": "Paper 1",
            "authors": ["Ahmed Ali", "Sara Khan"],
            "authorship_role": None,
        },
        {
            "title": "Paper 2",
            "authors": ["Sara Khan", "Ahmed Ali"],
            "authorship_role": None,
        },
        {
            "title": "Paper 3",
            "authors": ["Sara Khan", "Ahmed Ali", "John Doe"],
            "authorship_role": None,
        },
        {
            "title": "Paper 4",
            "authors": ["Ahmed Ali"],
            "authorship_role": None,
        },
    ]

    enriched = enricher.infer_authorship_roles(publications, "Ahmed Ali")

    assert enriched[0]["authorship_role"] == "first"
    assert enriched[1]["authorship_role"] == "corresponding"
    assert enriched[2]["authorship_role"] == "co_author"
    assert enriched[3]["authorship_role"] == "first_and_corresponding"


def test_infer_authorship_roles_overrides_weaker_existing_role_when_both_positions_match():
    publications = [
        {
            "title": "Paper X",
            "authors": ["Ahmed Ali", "John Doe", "Ahmed Ali"],
            "authorship_role": "first",
        }
    ]

    enriched = enricher.infer_authorship_roles(publications, "Ahmed Ali")
    assert enriched[0]["authorship_role"] == "first_and_corresponding"
