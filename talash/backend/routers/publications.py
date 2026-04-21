from fastapi import APIRouter, HTTPException

from db_connect import get_session
from db_models import Candidate, Publication
from services.publication_enricher import enrich_publications, infer_authorship_roles


router = APIRouter()


@router.post("/enrich/{candidate_id}")
def enrich_candidate_publications(candidate_id: str):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.candidate_id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {candidate_id}")

        publications = (
            session.query(Publication)
            .filter(Publication.candidate_id == candidate.id)
            .order_by(Publication.id.asc())
            .all()
        )
        if not publications:
            return {
                "status": "success",
                "candidate_id": candidate_id,
                "total_publications": 0,
                "enriched_count": 0,
                "enriched_fields": [],
                "message": "No publications found for this candidate",
            }

        payload = []
        for p in publications:
            payload.append(
                {
                    "id": p.id,
                    "type": p.pub_type.value if p.pub_type else "journal",
                    "title": p.title,
                    "venue": p.venue,
                    "issn": p.issn,
                    "year": p.year,
                    "authors": [a.strip() for a in (p.authors or "").split(",") if a.strip()],
                    "authorship_role": p.authorship_role.value if p.authorship_role else None,
                    "doi": p.doi,
                    "publisher": p.publisher,
                    "journal_name": p.journal_name,
                    "conference_name": p.conference_name,
                    "conference_maturity": p.conference_maturity,
                    "proceedings_publisher": p.proceedings_publisher,
                }
            )

        enriched = enrich_publications(payload)
        enriched = infer_authorship_roles(enriched, candidate.name or "")

        records_by_id = {p.id: p for p in publications}
        enriched_count = 0
        enriched_fields: set[str] = set()

        for item in enriched:
            rec = records_by_id.get(item.get("id"))
            if not rec:
                continue

            changed = False
            for key in [
                "venue",
                "issn",
                "authorship_role",
                "doi",
                "publisher",
                "journal_name",
                "conference_name",
                "conference_maturity",
                "proceedings_publisher",
            ]:
                new_val = item.get(key)
                old_attr = getattr(rec, key)
                old_val = old_attr.value if hasattr(old_attr, "value") else old_attr
                if new_val != old_val:
                    setattr(rec, key, new_val)
                    enriched_fields.add(key)
                    changed = True

            if changed:
                enriched_count += 1

        session.commit()

        return {
            "status": "success",
            "candidate_id": candidate_id,
            "total_publications": len(publications),
            "enriched_count": enriched_count,
            "enriched_fields": sorted(enriched_fields),
            "message": f"All {len(publications)} publications enriched successfully",
        }
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Publication enrichment failed: {exc}")
    finally:
        session.close()
