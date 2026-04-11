from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy.orm import selectinload

from db_connect import get_session
from db_models import Candidate
from graph import app as graph_app
from schemas import CandidateResponse, UploadSummaryResponse


router = APIRouter()


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
                    name=c.name,
                    email=c.email,
                    phone=c.phone,
                    education_count=len(c.education),
                    experience_count=len(c.experience),
                    publications_count=len(c.publications),
                    education=[
                        {
                            "degree": e.degree,
                            "field": e.field,
                            "institution": e.institution,
                            "start_year": e.start_year,
                            "end_year": e.end_year,
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
                            "type": p.type.value if p.type else None,
                            "title": p.title,
                            "venue": p.venue,
                            "year": p.year,
                        }
                        for p in c.publications
                    ],
                    skills=[{"skill_name": s.skill_name} for s in c.skills],
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
