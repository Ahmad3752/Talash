from pathlib import Path
import re
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy.orm import selectinload

from db_connect import get_session
from db_models import Candidate
from graph import app as graph_app
from schemas import CandidateProfileResponse, CandidateResponse, UploadSummaryResponse


router = APIRouter()


def _to_yyyy_mm(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    match = re.match(r"^(\d{4})[-/](\d{1,2})", cleaned)
    if not match:
        return None

    year, month = match.groups()
    month_num = int(month)
    if month_num < 1 or month_num > 12:
        return None

    return f"{year}-{month_num:02d}"


@router.post("/upload", response_model=UploadSummaryResponse)
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    session = get_session()
    before_count = session.query(Candidate).count()
    session.close()

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        initial_state = {
            "pdf_path": temp_path,
            "raw_texts": [],
            "all_results": [],
            "error": None,
        }
        result = graph_app.invoke(initial_state)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        extracted = result.get("all_results", [])
        extraction_errors = [
            f"{x.get('_candidate_id', '?')}: {x.get('error')}" for x in extracted if "error" in x
        ]
        extracted_success = len([x for x in extracted if "error" not in x])

        session = get_session()
        after_count = session.query(Candidate).count()
        session.close()

        return UploadSummaryResponse(
            message="CV processing completed",
            extracted_candidates=extracted_success,
            newly_stored_candidates=max(after_count - before_count, 0),
            errors=extraction_errors,
        )
    finally:
        await file.close()
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


@router.get("/candidates", response_model=list[CandidateResponse])
def list_candidates():
    session = get_session()
    try:
        candidates = (
            session.query(Candidate)
            .options(
                selectinload(Candidate.education),
                selectinload(Candidate.experience),
                selectinload(Candidate.publications),
                selectinload(Candidate.skills),
                selectinload(Candidate.books),
                selectinload(Candidate.patents),
            )
            .all()
        )
        output: list[CandidateResponse] = []
        for c in candidates:
            output.append(
                CandidateResponse(
                    id=c.id,
                    candidate_id=c.candidate_id,
                    name=c.name,
                    email=c.email,
                    phone=c.phone,
                    education_count=len(c.education),
                    experience_count=len(c.experience),
                    publications_count=len(c.publications),
                    education=[
                        {
                            "degree": e.degree,
                            "degree_level": e.degree_level,
                            "field": e.field,
                            "institution": e.institution,
                            "start_year": e.start_year,
                            "end_year": e.end_year,
                            "normalized_percentage": e.normalized_percentage,
                        }
                        for e in c.education
                    ],
                    experience=[
                        {
                            "company": e.company,
                            "role": e.role,
                            "employment_type": e.employment_type,
                            "start_date": e.start_date,
                            "end_date": e.end_date,
                        }
                        for e in c.experience
                    ],
                    publications=[
                        {
                            "type": p.pub_type.value if p.pub_type else None,
                            "title": p.title,
                            "venue": p.venue,
                            "issn": p.issn,
                            "year": p.year,
                            "authorship_role": p.authorship_role.value if p.authorship_role else None,
                            "doi": p.doi,
                            "publisher": p.publisher,
                            "journal_name": p.journal_name,
                            "conference_name": p.conference_name,
                            "conference_maturity": p.conference_maturity,
                            "proceedings_publisher": p.proceedings_publisher,
                        }
                        for p in c.publications
                    ],
                    skills=[{"skill_name": s.skill_name, "inferred": bool(s.inferred)} for s in c.skills],
                    books=[
                        {"title": b.title, "publisher": b.publisher, "year": b.year}
                        for b in c.books
                    ],
                    patents=[
                        {
                            "patent_number": p.patent_number,
                            "title": p.title,
                            "year": p.year,
                        }
                        for p in c.patents
                    ],
                )
            )
        return output
    finally:
        session.close()


@router.get("/candidates/{candidate_id}", response_model=CandidateProfileResponse)
def get_candidate_profile(candidate_id: str):
    session = get_session()
    try:
        candidate = (
            session.query(Candidate)
            .options(
                selectinload(Candidate.education),
                selectinload(Candidate.experience),
                selectinload(Candidate.skills),
                selectinload(Candidate.publications),
                selectinload(Candidate.books),
                selectinload(Candidate.patents),
                selectinload(Candidate.supervised_students),
            )
            .filter(Candidate.candidate_id == candidate_id)
            .first()
        )

        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {candidate_id}")

        return CandidateProfileResponse(
            id=candidate.id,
            candidate_id=candidate.candidate_id,
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            education=[
                {
                    "id": e.id,
                    "degree": e.degree,
                    "degree_level": e.degree_level,
                    "field": e.field,
                    "institution": e.institution,
                    "board": e.board,
                    "start_year": e.start_year,
                    "end_year": e.end_year,
                    "cgpa": e.cgpa,
                    "cgpa_scale": e.cgpa_scale,
                    "percentage": e.percentage,
                    "normalized_percentage": e.normalized_percentage,
                }
                for e in candidate.education
            ],
            experience=[
                {
                    "id": ex.id,
                    "company": ex.company,
                    "role": ex.role,
                    "employment_type": ex.employment_type,
                    "start_date": _to_yyyy_mm(ex.start_date),
                    "end_date": _to_yyyy_mm(ex.end_date),
                    "description": ex.description,
                }
                for ex in candidate.experience
            ],
            skills=[
                {
                    "id": s.id,
                    "skill_name": s.skill_name,
                    "inferred": bool(s.inferred),
                }
                for s in candidate.skills
            ],
            publications=[
                {
                    "id": p.id,
                    "pub_type": p.pub_type.value if p.pub_type else None,
                    "title": p.title,
                    "venue": p.venue,
                    "issn": p.issn,
                    "year": p.year,
                    "authors": p.authors,
                    "authorship_role": p.authorship_role.value if p.authorship_role else None,
                    "wos_indexed": p.wos_indexed,
                    "scopus_indexed": p.scopus_indexed,
                    "quartile": p.quartile,
                    "impact_factor": p.impact_factor,
                    "core_rank": p.core_rank,
                    "indexed_in": p.indexed_in,
                    "doi": p.doi,
                    "publisher": p.publisher,
                    "journal_name": p.journal_name,
                    "conference_name": p.conference_name,
                    "conference_maturity": p.conference_maturity,
                    "proceedings_publisher": p.proceedings_publisher,
                }
                for p in candidate.publications
            ],
            books=[
                {
                    "id": b.id,
                    "title": b.title,
                    "authors": b.authors,
                    "isbn": b.isbn,
                    "publisher": b.publisher,
                    "year": b.year,
                    "url": b.url,
                    "authorship_role": b.authorship_role,
                }
                for b in candidate.books
            ],
            patents=[
                {
                    "id": pt.id,
                    "patent_number": pt.patent_number,
                    "title": pt.title,
                    "year": pt.year,
                    "inventors": pt.inventors,
                    "country": pt.country,
                    "verification_url": pt.verification_url,
                }
                for pt in candidate.patents
            ],
            supervised_students=[
                {
                    "id": ss.id,
                    "student_name": ss.student_name,
                    "level": ss.level.value if ss.level else None,
                    "role": ss.role.value if ss.role else None,
                    "graduation_year": ss.graduation_year,
                }
                for ss in candidate.supervised_students
            ],
        )
    finally:
        session.close()
