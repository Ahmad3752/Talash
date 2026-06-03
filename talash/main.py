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

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Header, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from typing import Optional, List, Dict, Any
import tempfile
import os
import secrets
from datetime import datetime
import json
import traceback
import asyncio

# ============================================================================
# CRITICAL: Import ALL models before init_db so SQLAlchemy create_all() sees
#           every table.
# ============================================================================
from .db_models import (
    Base, Candidate, Education, Experience, Skill,
    Publication, Book, Patent, SupervisedStudent,
    EducationScore, ResearchScore, ProfessionalExperienceScore,
    SkillAlignmentScore, TopicVariabilityScore, CoauthorAnalysisScore,
    CVSummary,
)
from .developer import models as developer_models  # noqa: F401 - registers developer tables
from .developer.router import router as developer_router
from .developer.validation import normalize_upload_track
from .db_connect import init_db, get_session, engine
from .utils.email import send_email, build_recommendation_email_html

# Import runner utilities.
# detect_cv_boundaries is the SMART version (email/keyword heuristic).
# _cv_fingerprint ensures IDs in _count_cvs_in_pdf match what database_storage writes.
from . import runner
from .runner import (
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

frontend_urls = [
    origin.strip()
    for origin in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
    if origin.strip()
]
for local_origin in (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
):
    if local_origin not in frontend_urls:
        frontend_urls.append(local_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(developer_router)


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
    reasons: Optional[str] = None  # JSON
    warnings: Optional[str] = None  # JSON list
    recommendations: Optional[str] = None  # JSON list

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
    gaps: Optional[str] = None  # JSON
    job_overlaps: Optional[str] = None  # JSON
    edu_overlaps: Optional[str] = None  # JSON
    flags: Optional[str] = None  # JSON
    seniority_trajectory: Optional[str] = None  # JSON
    career_notes: Optional[str] = None  # JSON

    class Config:
        from_attributes = True
        orm_mode = True


class SkillAlignmentScoreSchema(BaseModel):
    id: int
    applicable: Optional[bool] = None
    applicability_reason: Optional[str] = None
    skill_experience_score: Optional[float] = None
    skill_publication_score: Optional[float] = None
    skill_consistency_score: Optional[float] = None
    raw_score: Optional[float] = None
    grade: Optional[str] = None
    skill_details: Optional[str] = None  # JSON
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
    reason: Optional[str] = None
    dominant_theme: Optional[str] = None
    diversity_score: Optional[float] = None
    focus_type: Optional[str] = None
    topic_trend: Optional[str] = None
    trend_explanation: Optional[str] = None
    overall_interpretation: Optional[str] = None
    themes: Optional[str] = None  # JSON
    total_publications: Optional[int] = None
    themes_identified: Optional[int] = None
    id_coverage_ok: Optional[bool] = None
    missing_pub_ids: Optional[str] = None  # JSON
    extra_pub_ids: Optional[str] = None  # JSON
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True


class CoauthorAnalysisScoreSchema(BaseModel):
    id: int
    applicable: Optional[bool] = None
    reason: Optional[str] = None
    unique_coauthors: Optional[int] = None
    total_collaborations: Optional[int] = None
    solo_papers: Optional[int] = None
    avg_authors_per_paper: Optional[float] = None
    max_authors_in_one_paper: Optional[int] = None
    recurring_collaborators: Optional[int] = None
    collaboration_style: Optional[str] = None
    network_diversity_score: Optional[float] = None
    collaboration_type: Optional[str] = None
    international_flag: Optional[bool] = None
    interpretation: Optional[str] = None
    top_collaborators: Optional[str] = None  # JSON
    all_coauthor_freq: Optional[str] = None  # JSON
    total_publications: Optional[int] = None
    candidate_name_used: Optional[str] = None
    parse_warnings: Optional[str] = None  # JSON
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
    summary_data: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {'from_attributes': True}


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
    cv_summary: Optional[CVSummarySchema] = None

    model_config = {'from_attributes': True}


class UploadResponseSchema(BaseModel):
    message: str
    evaluation_track: str
    developer_role: Optional[str] = None
    candidates_count: int
    new_count: int
    existing_count: int
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    status: str


class CacheResetResponseSchema(BaseModel):
    pattern: str
    matched_before: int
    deleted: int
    matched_after: int
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

async def process_pdf_background(
    pdf_path: str,
    evaluation_track: str = "researcher",
    developer_role: Optional[str] = None,
):
    """Background task — runs the full pipeline from runner.py."""
    try:
        print("\n" + "=" * 60)
        print("BACKGROUND PROCESSING STARTED")
        print(f"Evaluation track: {evaluation_track}")
        if developer_role:
            print(f"Developer role: {developer_role}")
        print("=" * 60)
        results = await runner.process_all_cvs_sequential(pdf_path)
        if evaluation_track == "developer":
            from .developer.service import run_developer_profile_extraction

            print("\n" + "-" * 60)
            print("DEVELOPER EVALUATION")
            print("-" * 60)
            developer_results = await run_in_threadpool(
                run_developer_profile_extraction,
                results,
                developer_role,
            )
            print(f"\nDeveloper profile extraction complete: {len(developer_results)} candidate(s)")
            for item in developer_results:
                print(
                    "  "
                    f"{item.get('candidate_id')}: {item.get('status')}"
                    f" profile={item.get('developer_profile_id', '-')}"
                )
                if item.get("overall_score") is not None:
                    print(
                        "     "
                        f"Developer Score: {item.get('overall_score')}/100"
                        f" [{item.get('overall_grade', 'N/A')}]"
                    )
                for module in item.get("module_scores", []):
                    print(
                        "     "
                        f"- {module.get('name')}: {module.get('score')}/{module.get('max')}"
                        f" [{module.get('grade')}]"
                    )
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
    from .redis_cache import ping as redis_ping
    session = get_session()
    try:
        session.query(Candidate).first()
        db_ok = True
    except Exception as e:
        db_ok = False
    finally:
        session.close()
 
    redis_ok = redis_ping()
 
    status = "healthy" if (db_ok and redis_ok) else "degraded"
    return {
        "status":   status,
        "database": "connected" if db_ok    else "error",
        "redis":    "connected" if redis_ok else "error",
    }
 

@app.post(
    "/admin/cache/cv-hashes/reset",
    response_model=CacheResetResponseSchema,
    tags=["Admin"],
)
async def reset_cv_hash_cache(x_admin_token: Optional[str] = Header(default=None)):
    """
    Clear only Redis CV hash cache keys (cv_hash:*).

    This endpoint is intended as a temporary production escape hatch for hosts
    without shell access. It is disabled unless CV_CACHE_RESET_TOKEN is set.
    """
    expected_token = os.getenv("CV_CACHE_RESET_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="CV cache reset endpoint is disabled. Set CV_CACHE_RESET_TOKEN to enable it.",
        )

    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected_token):
        raise HTTPException(status_code=403, detail="Invalid admin token")

    try:
        from .redis_cache import CV_HASH_PATTERN, clear_cv_hash_cache, count_cv_hash_cache

        matched_before = count_cv_hash_cache()
        deleted = clear_cv_hash_cache()
        matched_after = count_cv_hash_cache()
        return CacheResetResponseSchema(
            pattern=CV_HASH_PATTERN,
            matched_before=matched_before,
            deleted=deleted,
            matched_after=matched_after,
            status="cleared",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset CV hash cache: {e}")



@app.post("/upload", response_model=UploadResponseSchema, tags=["Upload"])
async def upload_pdf(
    file: UploadFile = File(...),
    evaluation_track: str = Form("researcher"),
    developer_role: Optional[str] = Form(None),
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
    try:
        evaluation_track, developer_role = normalize_upload_track(evaluation_track, developer_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
            "evaluation_track": evaluation_track,
            "developer_role": developer_role,
        }
        for c in cv_infos
    ]

    # Queue the heavy work
    if background_tasks is not None:
        background_tasks.add_task(process_pdf_background, tmp_path, evaluation_track, developer_role)
    else:
        asyncio.create_task(process_pdf_background(tmp_path, evaluation_track, developer_role))

    track_label = "developer" if evaluation_track == "developer" else "researcher"
    role_suffix = f" ({developer_role.replace('_', ' ')})" if developer_role else ""
    status_msg = (
        f"PDF uploaded. {candidates_count} CV(s) detected "
        f"({new_count} new, {existing_count} already in DB). "
        f"{track_label.title()}{role_suffix} processing queued."
    )

    return UploadResponseSchema(
        message=status_msg,
        evaluation_track=evaluation_track,
        developer_role=developer_role,
        candidates_count=candidates_count,
        new_count=new_count,
        existing_count=existing_count,
        candidates=candidates_info,
        status="processing",
    )


# ── Candidate list / detail ──────────────────────────────────────────────────

@app.get("/candidates", response_model=List[CandidateListSchema], tags=["Candidates"])
async def list_candidates():
    """List all candidates with basic info and cv_summary if available."""
    session = get_session()
    try:
        candidates = session.query(Candidate).all()
        result = []
        for c in candidates:
            # Get cv_summary if it exists
            cv_summary = session.query(CVSummary).filter(CVSummary.candidate_id == c.id).first()
            
            # Build candidate list with cv_summary
            cv_summary_data = None
            if cv_summary:
                try:
                    cv_summary_data = CVSummarySchema.model_validate(cv_summary)
                except Exception as e:
                    print(f"Failed to validate cv_summary for candidate {c.id}: {e}")
            
            candidate_data = {
                "id": c.id,
                "candidate_id": c.candidate_id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "cv_summary": cv_summary_data,
            }
            result.append(candidate_data)
        return result
    except Exception as e:
        print(f"Error in list_candidates: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve candidates: {str(e)}")
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


# ============================================================================
# EMAIL ENDPOINTS
# ============================================================================

class FetchEmailResponse(BaseModel):
    email: Optional[str] = None
    found: bool


class SendEmailResponse(BaseModel):
    success: bool
    error: Optional[str] = None


@app.get("/candidates/{candidate_id}/fetch-email",
         response_model=FetchEmailResponse, tags=["Email"])
async def fetch_candidate_email(candidate_id: int):
    """
    Fetch or infer candidate email.
    
    If candidate.email is populated, return it directly.
    Otherwise attempt to infer from available data.
    """
    session = get_session()
    try:
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        
        # Case 1: Email is already populated
        if candidate.email and candidate.email.strip():
            return FetchEmailResponse(email=candidate.email, found=True)
        
        # Case 2: No email found (could add lookup logic here in the future)
        return FetchEmailResponse(email=None, found=False)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch email: {str(e)}")
    finally:
        session.close()


@app.post("/candidates/{candidate_id}/send-recommendation-email",
          response_model=SendEmailResponse, tags=["Email"])
async def send_recommendation_email(candidate_id: int):
    """
    Send a recommendation email to the candidate.
    
    Fetches candidate data, CV summary, and research score recommendations,
    builds an HTML email, and sends it via SMTP.
    """
    session = get_session()
    try:
        # Fetch candidate
        candidate = session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        
        # Check email exists
        if not candidate.email or not candidate.email.strip():
            return SendEmailResponse(
                success=False,
                error="Candidate has no email address"
            )
        
        # Fetch CV summary
        cv_summary = session.query(CVSummary).filter(
            CVSummary.candidate_id == candidate.id
        ).first()
        
        if not cv_summary:
            return SendEmailResponse(
                success=False,
                error="CV summary not found for this candidate"
            )
        
        # Fetch research scores for recommendations
        research_scores = session.query(ResearchScore).filter(
            ResearchScore.candidate_id == candidate.id
        ).first()
        
        # Extract recommendations from research scores and summary
        recommendations = []
        
        if research_scores and research_scores.recommendations:
            try:
                rec_list = json.loads(research_scores.recommendations)
                if isinstance(rec_list, list):
                    recommendations.extend(rec_list)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Also try to extract from summary_data if available
        if cv_summary.summary_data:
            try:
                summary_data = json.loads(cv_summary.summary_data)
                if isinstance(summary_data, dict):
                    summary_recs = summary_data.get("recommendations", [])
                    if isinstance(summary_recs, list):
                        recommendations.extend(summary_recs)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recs.append(rec)
        recommendations = unique_recs[:10]  # Cap at 10 recommendations
        
        # Parse summary interpretation from summary_data
        summary_interpretation = ""
        if cv_summary.summary_data:
            try:
                summary_data = json.loads(cv_summary.summary_data)
                summary_interpretation = summary_data.get("summary_interpretation", "")
            except (json.JSONDecodeError, TypeError):
                pass
        
        if not summary_interpretation:
            summary_interpretation = f"Your CV demonstrates {cv_summary.overall_grade.lower() if cv_summary.overall_grade else 'good'} overall profile strength with a score of {cv_summary.overall_score:.1f}/100."
        
        # Build email HTML
        html_body = build_recommendation_email_html(
            candidate_name=candidate.name or "Candidate",
            overall_score=cv_summary.overall_score or 0,
            overall_grade=cv_summary.overall_grade or "N/A",
            recommendations=recommendations,
            summary_interpretation=summary_interpretation
        )
        
        # Send email
        result = await run_in_threadpool(
            send_email,
            to_email=candidate.email,
            subject=f"CV Evaluation Recommendations — {candidate.name or 'Candidate'}",
            html_body=html_body,
        )
        
        if result["success"]:
            return SendEmailResponse(success=True)
        else:
            return SendEmailResponse(
                success=False,
                error=result.get("error", "Unknown error sending email")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        return SendEmailResponse(
            success=False,
            error=f"Error: {str(e)}"
        )
    finally:
        session.close()
