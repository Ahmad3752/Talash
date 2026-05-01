"""
FastAPI Backend for CV Processing & Candidate Management
Endpoints for PDF upload, processing, and candidate data retrieval

Fixes in this revision:
  1. DB init: all models imported BEFORE init_db() so create_all() sees them.
  2. Pydantic schemas: list fields default to [] (never None).
  3. pub_type serialization: handles SQLAlchemy Enum → .value safely.
  4. CV boundary detection: uses runner.detect_cv_boundaries (the smart
     heuristic at the top of runner.py with email/keyword checks).
     The Cell-7 naive override has been removed from runner.py.
  5. _count_cvs_in_pdf: generates IDs via runner._cv_fingerprint so they
     MATCH exactly what database_storage stores — prevents phantom replacements.
  6. process_pdf_background: uses runner.process_all_cvs_sequential correctly.
  7. CandidateDetailSchema: no duplicate list fields.
  8. from_orm → model_validate for Pydantic v2 compatibility.
  9. LangGraph graph in runner.py is now SEQUENTIAL — the parallel fan-out
     was duplicating all_results 4× and breaking the summarizer.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import tempfile
import os
from datetime import datetime
import json
import traceback
import asyncio

# ============================================================================
# CRITICAL: Import ALL models before init_db so SQLAlchemy create_all() sees
#           every table.
# ============================================================================
from db_models import (
    Base, Candidate, Education, Experience, Skill,
    Publication, Book, Patent, SupervisedStudent,
    EducationScore, ResearchScore, ProfessionalExperienceScore,
    SkillAlignmentScore, TopicVariabilityScore, CoauthorAnalysisScore,
    CVSummary,
)
from db_connect import init_db, get_session, engine

# Import runner utilities.
# detect_cv_boundaries is the SMART version (email/keyword heuristic).
# _cv_fingerprint ensures IDs in _count_cvs_in_pdf match what database_storage writes.
import runner
from runner import (
    process_single_cv,
    process_all_cvs_sequential,
    parser,
    CVState,
    detect_cv_boundaries,
    _cv_fingerprint,
)
import fitz  # PyMuPDF


# ============================================================================
# INITIALIZE DATABASE
# ============================================================================
init_db()


# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title="CV Processing Backend",
    description="API for uploading CVs, processing them with AI, and retrieving candidate data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HELPER — safe enum serialization
# ============================================================================

def _enum_val(v):
    """Return .value if v is an Enum, else v itself."""
    return v.value if hasattr(v, "value") else v


def _orm_to_dict(orm_obj, schema_cls):
    """
    Convert a SQLAlchemy ORM object to a dict using the Pydantic schema.
    Supports both Pydantic v1 (from_orm) and v2 (model_validate).
    """
    try:
        return schema_cls.model_validate(orm_obj).model_dump()
    except AttributeError:
        return schema_cls.from_orm(orm_obj).dict()


# ============================================================================
# PYDANTIC RESPONSE SCHEMAS
# ============================================================================

class EducationSchema(BaseModel):
    id: int
    degree: Optional[str] = None
    degree_level: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    board: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = None
    percentage: Optional[float] = None
    normalized_percentage: Optional[float] = None

    class Config:
        from_attributes = True
        orm_mode = True


class ExperienceSchema(BaseModel):
    id: int
    company: Optional[str] = None
    role: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True


class SkillSchema(BaseModel):
    id: int
    skill_name: Optional[str] = None
    inferred: bool = False

    class Config:
        from_attributes = True
        orm_mode = True


class PublicationSchema(BaseModel):
    id: int
    pub_type: Optional[str] = None
    title: Optional[str] = None
    venue: Optional[str] = None
    issn: Optional[str] = None
    year: Optional[int] = None
    authors: Optional[str] = None
    authorship_role: Optional[str] = None
    wos_indexed: Optional[bool] = None
    scopus_indexed: Optional[bool] = None
    quartile: Optional[str] = None
    impact_factor: Optional[float] = None
    core_rank: Optional[str] = None
    indexed_in: Optional[str] = None
    doi: Optional[str] = None
    publisher: Optional[str] = None
    journal_name: Optional[str] = None
    conference_name: Optional[str] = None
    conference_maturity: Optional[str] = None
    proceedings_publisher: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True


class BookSchema(BaseModel):
    id: int
    title: Optional[str] = None
    authors: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    authorship_role: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True


class PatentSchema(BaseModel):
    id: int
    patent_number: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    inventors: Optional[str] = None
    country: Optional[str] = None
    verification_url: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True


class SupervisedStudentSchema(BaseModel):
    id: int
    student_name: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None
    graduation_year: Optional[int] = None

    class Config:
        from_attributes = True
        orm_mode = True


class EducationScoreSchema(BaseModel):
    id: int
    degree_level_score: Optional[float] = None
    overall_gpa_score: Optional[float] = None
    institution_quality_score: Optional[float] = None
    consistency_score: Optional[float] = None
    continuity_score: Optional[float] = None
    data_completeness_bonus: Optional[float] = None
    raw_score: Optional[float] = None
    grade: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class ResearchScoreSchema(BaseModel):
    id: int
    publication_quality_score: Optional[float] = None
    authorship_strength_score: Optional[float] = None
    research_collaboration_score: Optional[float] = None
    conference_maturity_score: Optional[float] = None
    patents_books_score: Optional[float] = None
    supervision_record_score: Optional[float] = None
    raw_score: Optional[float] = None
    grade: Optional[str] = None
    total_publications: Optional[int] = None
    total_journal_papers: Optional[int] = None
    total_conference_papers: Optional[int] = None
    total_books: Optional[int] = None
    total_patents: Optional[int] = None
    total_supervised_students: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class ProfessionalExperienceScoreSchema(BaseModel):
    id: int
    gap_detection_score: Optional[float] = None
    overlap_analysis_score: Optional[float] = None
    gap_justification_score: Optional[float] = None
    role_seniority_score: Optional[float] = None
    tenure_consistency_score: Optional[float] = None
    domain_continuity_score: Optional[float] = None
    data_quality_bonus: Optional[float] = None
    raw_score: Optional[float] = None
    grade: Optional[str] = None
    avg_tenure_months: Optional[float] = None
    total_experience_months: Optional[int] = None
    seniority_trend: Optional[str] = None
    domain_continuity: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class SkillAlignmentScoreSchema(BaseModel):
    id: int
    applicable: Optional[bool] = None
    skill_experience_score: Optional[float] = None
    skill_publication_score: Optional[float] = None
    skill_consistency_score: Optional[float] = None
    raw_score: Optional[float] = None
    grade: Optional[str] = None
    total_skills_evaluated: Optional[int] = None
    strong_count: Optional[int] = None
    partial_count: Optional[int] = None
    weak_count: Optional[int] = None
    unsupported_count: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class TopicVariabilityScoreSchema(BaseModel):
    id: int
    applicable: Optional[bool] = None
    dominant_theme: Optional[str] = None
    diversity_score: Optional[float] = None
    focus_type: Optional[str] = None
    topic_trend: Optional[str] = None
    total_publications: Optional[int] = None
    themes_identified: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class CoauthorAnalysisScoreSchema(BaseModel):
    id: int
    applicable: Optional[bool] = None
    unique_coauthors: Optional[int] = None
    total_collaborations: Optional[int] = None
    solo_papers: Optional[int] = None
    avg_authors_per_paper: Optional[float] = None
    collaboration_style: Optional[str] = None
    network_diversity_score: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class CVSummarySchema(BaseModel):
    id: int
    overall_score: Optional[float] = None
    overall_grade: Optional[str] = None
    overall_status: Optional[str] = None
    education_score: Optional[float] = None
    education_grade: Optional[str] = None
    research_score: Optional[float] = None
    research_grade: Optional[str] = None
    experience_score: Optional[float] = None
    experience_grade: Optional[str] = None
    tvs_score: Optional[float] = None
    tvs_grade: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class CandidateDetailSchema(BaseModel):
    id: int
    candidate_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    education: List[EducationSchema] = Field(default_factory=list)
    experience: List[ExperienceSchema] = Field(default_factory=list)
    skills: List[SkillSchema] = Field(default_factory=list)
    publications: List[PublicationSchema] = Field(default_factory=list)
    books: List[BookSchema] = Field(default_factory=list)
    patents: List[PatentSchema] = Field(default_factory=list)
    supervised_students: List[SupervisedStudentSchema] = Field(default_factory=list)

    education_scores: List[EducationScoreSchema] = Field(default_factory=list)
    research_scores: List[ResearchScoreSchema] = Field(default_factory=list)
    professional_experience_scores: List[ProfessionalExperienceScoreSchema] = Field(default_factory=list)
    skill_alignment_scores: List[SkillAlignmentScoreSchema] = Field(default_factory=list)
    topic_variability_scores: List[TopicVariabilityScoreSchema] = Field(default_factory=list)
    coauthor_analysis_scores: List[CoauthorAnalysisScoreSchema] = Field(default_factory=list)

    cv_summary: Optional[CVSummarySchema] = None

    class Config:
        from_attributes = True
        orm_mode = True


class CandidateListSchema(BaseModel):
    id: int
    candidate_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True


class UploadResponseSchema(BaseModel):
    message: str
    candidates_count: int
    new_count: int
    existing_count: int
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    status: str


# ============================================================================
# HELPERS — publication serialization and candidate detail builder
# ============================================================================

def _serialize_publication(p) -> dict:
    return {
        "id": p.id,
        "pub_type": _enum_val(p.pub_type),
        "title": p.title,
        "venue": p.venue,
        "issn": p.issn,
        "year": p.year,
        "authors": p.authors,
        "authorship_role": _enum_val(p.authorship_role),
        "wos_indexed": p.wos_indexed,
        "scopus_indexed": p.scopus_indexed,
        "quartile": _enum_val(p.quartile),
        "impact_factor": p.impact_factor,
        "core_rank": p.core_rank,
        "indexed_in": p.indexed_in,
        "doi": getattr(p, "doi", None),
        "publisher": getattr(p, "publisher", None),
        "journal_name": getattr(p, "journal_name", None),
        "conference_name": getattr(p, "conference_name", None),
        "conference_maturity": getattr(p, "conference_maturity", None),
        "proceedings_publisher": getattr(p, "proceedings_publisher", None),
    }


def _build_candidate_detail(candidate) -> dict:
    return {
        "id": candidate.id,
        "candidate_id": candidate.candidate_id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "education":  [_orm_to_dict(e, EducationSchema)  for e in (candidate.education  or [])],
        "experience": [_orm_to_dict(e, ExperienceSchema) for e in (candidate.experience or [])],
        "skills":     [_orm_to_dict(s, SkillSchema)      for s in (candidate.skills     or [])],
        "publications": [_serialize_publication(p)        for p in (candidate.publications or [])],
        "books":     [_orm_to_dict(b, BookSchema)    for b in (candidate.books    or [])],
        "patents":   [_orm_to_dict(p, PatentSchema)  for p in (candidate.patents  or [])],
        "supervised_students": [
            _orm_to_dict(ss, SupervisedStudentSchema)
            for ss in (candidate.supervised_students or [])
        ],
        "education_scores": [
            _orm_to_dict(es, EducationScoreSchema) for es in (candidate.education_scores or [])
        ],
        "research_scores": [
            _orm_to_dict(rs, ResearchScoreSchema) for rs in (candidate.research_scores or [])
        ],
        "professional_experience_scores": [
            _orm_to_dict(pes, ProfessionalExperienceScoreSchema)
            for pes in (candidate.professional_experience_scores or [])
        ],
        "skill_alignment_scores": [
            _orm_to_dict(sas, SkillAlignmentScoreSchema)
            for sas in (candidate.skill_alignment_scores or [])
        ],
        "topic_variability_scores": [
            _orm_to_dict(tvs, TopicVariabilityScoreSchema)
            for tvs in (candidate.topic_variability_scores or [])
        ],
        "coauthor_analysis_scores": [
            _orm_to_dict(cas, CoauthorAnalysisScoreSchema)
            for cas in (candidate.coauthor_analysis_scores or [])
        ],
        "cv_summary": (
            _orm_to_dict(candidate.cv_summary, CVSummarySchema)
            if candidate.cv_summary else None
        ),
    }


# ============================================================================
# _count_cvs_in_pdf
#
# Uses runner.detect_cv_boundaries (the smart version — email/keyword heuristic)
# and runner._cv_fingerprint so IDs here match what database_storage writes.
# This ensures the upload response accurately reports new vs existing CVs.
# ============================================================================

def _count_cvs_in_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parse the PDF with the same boundary detector and fingerprint function
    as runner.py, and return one info-dict per CV:
      - cv_id   : fingerprint ID matching what database_storage will use
      - is_new  : True if this CV is NOT yet in the database
      - preview : first 80 chars of text (debugging / response)
    """
    doc   = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()

    cv_texts = detect_cv_boundaries(pages)   # smart version from runner

    session = get_session()
    try:
        results = []
        for text in cv_texts:
            fingerprint = _cv_fingerprint(text)
            cv_id       = f"cv_{fingerprint}"
            already_exists = (
                session.query(Candidate)
                .filter_by(candidate_id=cv_id)
                .first() is not None
            )
            results.append({
                "cv_id":   cv_id,
                "is_new":  not already_exists,
                "preview": text[:80].replace("\n", " ").strip(),
            })
        return results
    finally:
        session.close()


# ============================================================================
# BACKGROUND TASK
# ============================================================================

async def process_pdf_background(pdf_path: str):
    """Background task — runs the full pipeline from runner.py."""
    try:
        print("\n" + "=" * 60)
        print("BACKGROUND PROCESSING STARTED")
        print("=" * 60)
        results = await runner.process_all_cvs_sequential(pdf_path)
        print(f"\n✅ Background processing complete: {len(results)} candidate(s)")
    except Exception as e:
        print(f"\n❌ ERROR in background processing: {str(e)}")
        print(traceback.format_exc())
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"🗑️  Temp file removed: {pdf_path}")
            except Exception:
                pass


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    return {"message": "CV Processing API", "status": "running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    session = get_session()
    try:
        session.query(Candidate).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")
    finally:
        session.close()


@app.post("/upload", response_model=UploadResponseSchema, tags=["Upload"])
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """
    Upload a PDF containing one or more CVs.

    - CVs are identified by content fingerprint, not upload order.
    - Re-uploading the same CV (in any PDF) will NOT create duplicates —
      the existing row is updated in place.
    - The response immediately reports how many CVs are new vs already stored.
    - Extraction + scoring runs in the background.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Persist to a temp file; the background task will delete it when done.
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        contents = await file.read()
        with os.fdopen(tmp_fd, "wb") as tmp_file:
            tmp_file.write(contents)
    except Exception as e:
        try:
            os.close(tmp_fd)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"Failed to save uploaded file: {e}")

    # ── Analyse CV boundaries & DB status BEFORE queueing background work ──
    try:
        cv_infos = _count_cvs_in_pdf(tmp_path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")

    candidates_count = len(cv_infos)
    new_count        = sum(1 for c in cv_infos if c["is_new"])
    existing_count   = candidates_count - new_count

    candidates_info = [
        {
            "cv_id":   c["cv_id"],
            "status":  "new — will be processed" if c["is_new"] else "already in DB — will be refreshed",
            "preview": c["preview"],
        }
        for c in cv_infos
    ]

    # Queue the heavy work
    if background_tasks is not None:
        background_tasks.add_task(process_pdf_background, tmp_path)
    else:
        asyncio.create_task(process_pdf_background(tmp_path))

    status_msg = (
        f"PDF uploaded. {candidates_count} CV(s) detected "
        f"({new_count} new, {existing_count} already in DB). "
        "Processing queued."
    )

    return UploadResponseSchema(
        message=status_msg,
        candidates_count=candidates_count,
        new_count=new_count,
        existing_count=existing_count,
        candidates=candidates_info,
        status="processing",
    )


# ── Candidate list / detail ──────────────────────────────────────────────────

@app.get("/candidates", response_model=List[CandidateListSchema], tags=["Candidates"])
async def list_candidates():
    """List all candidates with basic info."""
    session = get_session()
    try:
        candidates = session.query(Candidate).all()
        return [
            {
                "id":           c.id,
                "candidate_id": c.candidate_id,
                "name":         c.name,
                "email":        c.email,
                "phone":        c.phone,
            }
            for c in candidates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve candidates: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}", response_model=CandidateDetailSchema, tags=["Candidates"])
async def get_candidate_details(candidate_id: int):
    """Full candidate detail including all scores and summary."""
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return _build_candidate_detail(candidate)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve candidate details: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/education",
         response_model=List[EducationSchema], tags=["Candidates"])
async def get_candidate_education(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [_orm_to_dict(e, EducationSchema) for e in (candidate.education or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve education: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/experience",
         response_model=List[ExperienceSchema], tags=["Candidates"])
async def get_candidate_experience(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [_orm_to_dict(e, ExperienceSchema) for e in (candidate.experience or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve experience: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/skills",
         response_model=List[SkillSchema], tags=["Candidates"])
async def get_candidate_skills(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [_orm_to_dict(s, SkillSchema) for s in (candidate.skills or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve skills: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/publications",
         response_model=List[PublicationSchema], tags=["Candidates"])
async def get_candidate_publications(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [_serialize_publication(p) for p in (candidate.publications or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve publications: {e}")
    finally:
        session.close()


# ── Score endpoints ───────────────────────────────────────────────────────────

@app.get("/candidates/{candidate_id}/scores/education",
         response_model=List[EducationScoreSchema], tags=["Scores"])
async def get_education_scores(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [_orm_to_dict(es, EducationScoreSchema) for es in (candidate.education_scores or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve education scores: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/scores/research",
         response_model=List[ResearchScoreSchema], tags=["Scores"])
async def get_research_scores(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [_orm_to_dict(rs, ResearchScoreSchema) for rs in (candidate.research_scores or [])]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve research scores: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/scores/experience",
         response_model=List[ProfessionalExperienceScoreSchema], tags=["Scores"])
async def get_experience_scores(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [
            _orm_to_dict(pes, ProfessionalExperienceScoreSchema)
            for pes in (candidate.professional_experience_scores or [])
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve experience scores: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/scores/skills",
         response_model=List[SkillAlignmentScoreSchema], tags=["Scores"])
async def get_skill_alignment_scores(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        return [
            _orm_to_dict(sas, SkillAlignmentScoreSchema)
            for sas in (candidate.skill_alignment_scores or [])
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve skill scores: {e}")
    finally:
        session.close()


@app.get("/candidates/{candidate_id}/scores/summary",
         response_model=CVSummarySchema, tags=["Scores"])
async def get_cv_summary(candidate_id: int):
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        if not candidate.cv_summary:
            raise HTTPException(
                status_code=404,
                detail=f"No CV summary for candidate {candidate_id} — scoring may still be running",
            )
        return _orm_to_dict(candidate.cv_summary, CVSummarySchema)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve CV summary: {e}")
    finally:
        session.close()