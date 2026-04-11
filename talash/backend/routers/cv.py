from pathlib import Path
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from db_connect import get_session
from db_models import Candidate
from graph import app as graph_app
from schemas import CandidateSummaryResponse, UploadSummaryResponse


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


@router.get("/candidates", response_model=list[CandidateSummaryResponse])
def list_candidates():
    session = get_session()
    try:
        candidates = session.query(Candidate).all()
        output: list[CandidateSummaryResponse] = []
        for c in candidates:
            output.append(
                CandidateSummaryResponse(
                    id=c.id,
                    name=c.name,
                    email=c.email,
                    phone=c.phone,
                    education_count=len(c.education),
                    experience_count=len(c.experience),
                    publications_count=len(c.publications),
                )
            )
        return output
    finally:
        session.close()
