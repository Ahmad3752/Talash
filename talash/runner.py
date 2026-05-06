# runner.py
# Fixes applied:
#   FIX 1 — all_results uses _last_value reducer instead of operator.add
#   FIX 2 — detect_cv_boundaries tightened
#   FIX 3 — llm_client.py: gemini-2.0-flash + openrouter/auto fallback
#   FIX 4 — Redis cache: CV hash checked before processing; written after DB save

import os
import re
import json
import operator
import hashlib
import asyncio
from dotenv import load_dotenv
import fitz
from typing import Annotated, List, Optional, Literal, TypedDict
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from llm_client import litellm_chat, openrouter_structured_call

load_dotenv()


openrouter_key= os.getenv("OPENROUTER_KEY")
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
    max_tokens=7000,
)


# ============================================================================
# CV Boundary Detection
# ============================================================================

_EMAIL_RE      = re.compile(r"\b[\w.+\-]+@[\w\-]+\.[a-z]{2,}\b", re.IGNORECASE)
_PHONE_RE      = re.compile(r"(\+?\d[\d\s\-\(\)]{7,}\d)")
_CV_KEYWORD_RE = re.compile(
    r"curriculum\s+vitae|\bresume\b|\bbiodata\b", re.IGNORECASE
)
_NAME_LABEL_RE = re.compile(r"^name\s*[:\-]", re.IGNORECASE | re.MULTILINE)


def _looks_like_cv_start(page_text: str) -> bool:
    sample = page_text[:600]
    has_cv_keyword = bool(_CV_KEYWORD_RE.search(sample))
    has_email      = bool(_EMAIL_RE.search(sample))
    has_phone      = bool(_PHONE_RE.search(sample))
    has_name_label = bool(_NAME_LABEL_RE.search(sample))

    if has_cv_keyword and (has_email or has_phone):
        return True
    if has_name_label and has_email:
        return True
    return False


def detect_cv_boundaries(pages: list) -> list:
    cvs: list[str] = []
    current: list[str] = []

    for page in pages:
        clean = page.strip()
        if not clean:
            if current:
                cvs.append("\n\n".join(current))
                current = []
        elif current and _looks_like_cv_start(clean):
            cvs.append("\n\n".join(current))
            current = [clean]
        else:
            current.append(clean)

    if current:
        cvs.append("\n\n".join(current))

    return [cv for cv in cvs if len(cv.strip()) >= 200]


def _cv_fingerprint(text: str) -> str:
    sample = text[:1000].strip()
    return hashlib.sha256(sample.encode("utf-8", errors="replace")).hexdigest()[:12]


# ============================================================================
# LangGraph State
# ============================================================================

def _last_value(left: List[dict], right: List[dict]) -> List[dict]:
    return right if right is not None else left


class CVState(TypedDict):
    pdf_path:    str
    raw_texts:   Annotated[List[tuple], operator.add]
    all_results: Annotated[List[dict],  _last_value]
    error:       Optional[str]


# ============================================================================
# Pydantic extraction models
# ============================================================================

class PersonalInfo(BaseModel):
    name:  Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class DegreeRecord(BaseModel):
    degree:      Optional[str]   = None
    field:       Optional[str]   = None
    institution: Optional[str]   = None
    start_year:  Optional[int]   = None
    end_year:    Optional[int]   = None
    cgpa:        Optional[float] = None
    cgpa_scale:  Optional[float] = None
    percentage:  Optional[float] = None
    board:       Optional[str]   = None

    @field_validator("start_year", "end_year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None

    @field_validator("cgpa","cgpa_scale","percentage", mode="before")
    @classmethod
    def parse_float(cls, v):
        if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
            return None
        try:
            return float(str(v).replace("%","").replace("/4.0","").replace("/5.0","").strip())
        except Exception:
            return None


class ExperienceRecord(BaseModel):
    company:         Optional[str] = None
    role:            Optional[str] = None
    employment_type: Optional[str] = None
    start_date:      Optional[str] = None
    end_date:        Optional[str] = None
    description:     Optional[str] = None

    @field_validator("start_date","end_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v is None or str(v).strip().lower() in {
            "n/a","na","none","null","","present","current","till date","to date"
        }:
            return None
        v = str(v).strip()
        if re.match(r"^\d{4}-\d{1,2}$", v):
            parts = v.split("-")
            return f"{parts[0]}-{int(parts[1]):02d}"
        months = {
            "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
            "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12
        }
        match = re.search(
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,.\-]+(\d{4})",
            v.lower()
        )
        if match:
            return f"{match.group(2)}-{months[match.group(1)[:3]]:02d}"
        match = re.search(
            r"(\d{4})[\s,.\-]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*",
            v.lower()
        )
        if match:
            return f"{match.group(1)}-{months[match.group(2)[:3]]:02d}"
        match = re.search(r"\b(19|20)\d{2}\b", v)
        if match:
            return match.group()
        return None


class Publication(BaseModel):
    type:            Literal["journal","conference"] = "journal"
    title:           Optional[str]   = None
    venue:           Optional[str]   = None
    issn:            Optional[str]   = None
    year:            Optional[int]   = None
    authors:         List[str]       = Field(default_factory=list)
    authorship_role: Optional[Literal[
        "first","corresponding","first_and_corresponding","co_author"
    ]] = None
    wos_indexed:     Optional[bool]  = None
    scopus_indexed:  Optional[bool]  = None
    quartile:        Optional[Literal["Q1","Q2","Q3","Q4"]] = None
    impact_factor:   Optional[float] = None
    core_rank:       Optional[str]   = None
    indexed_in:      Optional[str]   = None

    @field_validator("year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class Book(BaseModel):
    title:           Optional[str] = None
    authors:         List[str]     = Field(default_factory=list)
    isbn:            Optional[str] = None
    publisher:       Optional[str] = None
    year:            Optional[int] = None
    url:             Optional[str] = None
    authorship_role: Optional[Literal["sole","lead","co_author","contributing"]] = None

    @field_validator("year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class Patent(BaseModel):
    patent_number:    Optional[str] = None
    title:            Optional[str] = None
    year:             Optional[int] = None
    inventors:        List[str]     = Field(default_factory=list)
    country:          Optional[str] = None
    verification_url: Optional[str] = None

    @field_validator("year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class SupervisionRecord(BaseModel):
    student_name:    Optional[str] = None
    level:           Optional[Literal["MS","PhD"]] = None
    role:            Optional[Literal["main","co_supervisor"]] = None
    graduation_year: Optional[int] = None

    @field_validator("graduation_year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a","na","none","null",""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class CVExtraction(BaseModel):
    personal_info:       PersonalInfo            = Field(default_factory=PersonalInfo)
    education:           List[DegreeRecord]      = Field(default_factory=list)
    experience:          List[ExperienceRecord]  = Field(default_factory=list)
    skills:              List[str]               = Field(default_factory=list)
    publications:        List[Publication]       = Field(default_factory=list)
    books:               List[Book]              = Field(default_factory=list)
    patents:             List[Patent]            = Field(default_factory=list)
    supervised_students: List[SupervisionRecord] = Field(default_factory=list)


structured_llm = llm.with_structured_output(CVExtraction)


# ============================================================================
# Extraction prompt
# ============================================================================

EXTRACTION_PROMPT = """
You are a CV data extraction assistant. Extract structured information from the CV text below.
Return a JSON object that EXACTLY matches this schema. Use these EXACT field names.

SCHEMA:
{{
  "personal_info": {{
    "name": string or null,
    "email": string or null,
    "phone": string or null
  }},
  "education": [
    {{
      "degree": string or null,
      "field": string or null,
      "institution": string or null,
      "start_year": integer or null,
      "end_year": integer or null,
      "cgpa": float or null,
      "cgpa_scale": float or null,
      "percentage": float or null,
      "board": string or null
    }}
  ],
  "experience": [
    {{
      "company": string or null,
      "role": string or null,
      "employment_type": string or null,
      "start_date": string or null,
      "end_date": string or null,
      "description": string or null
    }}
  ],
  "skills": [string],
  "publications": [
    {{
      "type": "journal" or "conference",
      "title": string or null,
      "venue": string or null,
      "issn": string or null,
      "year": integer or null,
      "authors": [string],
      "authorship_role": "first" or "corresponding" or "first_and_corresponding" or "co_author" or null,
      "wos_indexed": boolean or null,
      "scopus_indexed": boolean or null,
      "quartile": "Q1" or "Q2" or "Q3" or "Q4" or null,
      "impact_factor": float or null,
      "core_rank": string or null,
      "indexed_in": string or null
    }}
  ],
  "books": [
    {{
      "title": string or null,
      "authors": [string],
      "isbn": string or null,
      "publisher": string or null,
      "year": integer or null,
      "url": string or null,
      "authorship_role": "sole" or "lead" or "co_author" or "contributing" or null
    }}
  ],
  "patents": [
    {{
      "patent_number": string or null,
      "title": string or null,
      "year": integer or null,
      "inventors": [string],
      "country": string or null,
      "verification_url": string or null
    }}
  ],
  "supervised_students": [
    {{
      "student_name": string or null,
      "level": "MS" or "PhD" or null,
      "role": "main" or "co_supervisor" or null,
      "graduation_year": integer or null
    }}
  ]
}}

STRICT RULES:
- Use null for every missing/unknown field — NEVER use "N/A", "Present", ""
- SSC and HSSC go inside "education" with degree="SSC" or degree="HSSC"
- ALL publications (journals + conferences) go in the single "publications" list
- Dates MUST be "YYYY-MM": convert "Sep-2017" → "2017-09"
- If end_date is "Present" or "current" use null
- Years must be integers, CGPA must be floats
- Extract ALL entries, never truncate

CV TEXT:
{cv_text}
"""


# ============================================================================
# Post-processing helpers
# ============================================================================

def clean_nulls(obj):
    NULL_STRINGS = {
        "n/a","na","none","null","not mentioned","not available",
        "not applicable","","-","present","current"
    }
    if isinstance(obj, dict):
        return {k: clean_nulls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nulls(i) for i in obj]
    if isinstance(obj, str) and obj.strip().lower() in NULL_STRINGS:
        return None
    return obj


def normalize_education(education_list: list) -> list:
    for edu in education_list:
        cgpa  = edu.get("cgpa")
        scale = edu.get("cgpa_scale")
        pct   = edu.get("percentage")
        if pct is not None:
            edu["normalized_percentage"] = round(float(pct), 2)
        elif cgpa is not None:
            if scale is None:
                scale = 4.0 if float(cgpa) <= 4.0 else 5.0
                edu["cgpa_scale"] = scale
            edu["normalized_percentage"] = round((float(cgpa) / float(scale)) * 100, 2)
        else:
            edu["normalized_percentage"] = None
    return education_list


SKILL_INFERENCE_PROMPT = """
Based ONLY on the job titles and publication titles below, list the most likely
technical and professional skills this person has.

Return ONLY a valid JSON array of strings. No explanation. No markdown. No preamble.
Maximum 12 skills.

Example: ["Python", "Machine Learning", "Research", "Teaching"]

Job titles: {roles}
Publication titles: {pub_titles}
"""


def infer_skills_if_missing(extracted: dict, llm_unused) -> dict:
    if extracted.get("skills"):
        return extracted

    roles = [
        e.get("role","") for e in extracted.get("experience", []) if e.get("role")
    ]
    pub_titles = [
        p.get("title","") for p in extracted.get("publications", []) if p.get("title")
    ][:8]

    if not roles and not pub_titles:
        return extracted

    try:
        prompt = SKILL_INFERENCE_PROMPT.format(
            roles=", ".join(roles),
            pub_titles="; ".join(pub_titles),
        )
        response = litellm_chat(prompt, SKILL_INFERENCE_PROMPT)
        raw = response.content.strip()
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
        inferred = json.loads(raw)
        if isinstance(inferred, list):
            extracted["skills"] = [s for s in inferred if isinstance(s, str)]
            print(f"    🔧 Inferred {len(extracted['skills'])} skill(s) from job/publication titles")
    except Exception as e:
        print(f"    ⚠️  Skill inference failed: {e}")
        extracted["skills"] = []

    return extracted


# ============================================================================
# Parser  (standalone — called before graph invocation)
# ============================================================================

def parser(state: "CVState") -> dict:
    path      = state["pdf_path"]
    raw_texts = []

    try:
        if os.path.isdir(path):
            pdf_files = sorted(f for f in os.listdir(path) if f.endswith(".pdf"))
            print(f"  📁 Folder mode — {len(pdf_files)} PDF(s) found")
            for fname in pdf_files:
                doc   = fitz.open(os.path.join(path, fname))
                pages = [p.get_text() for p in doc]
                doc.close()
                cvs = detect_cv_boundaries(pages)
                print(f"      {fname} — {len(cvs)} CV(s) detected")
                for cv_text in cvs:
                    label = f"cv_{_cv_fingerprint(cv_text)}"
                    raw_texts.append((label, cv_text))

        elif os.path.isfile(path):
            doc   = fitz.open(path)
            pages = [p.get_text() for p in doc]
            doc.close()
            cvs = detect_cv_boundaries(pages)
            print(f"  📄 Single PDF — {len(cvs)} CV(s) detected")
            for cv_text in cvs:
                label = f"cv_{_cv_fingerprint(cv_text)}"
                raw_texts.append((label, cv_text))
        else:
            return {"error": f"Path not found: {path}"}

        if not raw_texts:
            return {"error": "No CV text extracted"}

        return {"raw_texts": raw_texts, "error": None}

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"error": f"Parsing failed: {str(e)}"}


# ============================================================================
# LangGraph Nodes
# ============================================================================

def llm_extractor(state: CVState) -> dict:
    """Extract structured data from CV text via LLM."""
    if state.get("error"):
        return {"error": state.get("error")}

    all_results = []
    raw_texts   = state.get("raw_texts", [])

    print(f"\n  🔍 LLM Extraction — {len(raw_texts)} CV(s)")

    for idx, (candidate_id, text) in enumerate(raw_texts, 1):
        if len(text) < 100:
            print(f"    ⚠️  [{idx}] Too short, skipping")
            continue

        try:
            prompt = EXTRACTION_PROMPT.format(cv_text=text)
            result: CVExtraction = structured_llm.invoke(prompt)
            extracted = result.model_dump()

            if "journal_publications" in extracted or "ssc_hssc" in extracted:
                print(f"    ⚠️  Schema mismatch — using raw JSON fallback")
                raw_resp = litellm_chat(prompt, EXTRACTION_PROMPT)
                raw_text = re.sub(
                    r"^```json\s*|^```\s*|```$", "",
                    raw_resp.content.strip(), flags=re.MULTILINE
                ).strip()
                extracted = json.loads(raw_text)

            extracted = clean_nulls(extracted)
            if extracted.get("education"):
                extracted["education"] = normalize_education(extracted["education"])
            extracted = infer_skills_if_missing(extracted, None)
            extracted["_candidate_id"] = candidate_id

            # Store the original CV text so database_storage can cache it in Redis
            extracted["_cv_text"] = text

            info = extracted.get("personal_info", {})
            name  = info.get("name", "Unknown")
            email = info.get("email", "—")
            print(f"    ✅ Extracted: {name} ({email})")
            print(f"       Education: {len(extracted.get('education',[]))} | "
                  f"Experience: {len(extracted.get('experience',[]))} | "
                  f"Publications: {len(extracted.get('publications',[]))} | "
                  f"Skills: {len(extracted.get('skills',[]))}")

            all_results.append(extracted)

        except Exception as e:
            print(f"    ❌ Extraction failed: {e}")
            all_results.append({"_candidate_id": candidate_id, "error": str(e)})

    return {"all_results": all_results}


def database_storage(state: "CVState") -> dict:
    """Upsert extracted candidate data into the database, then write hash to Redis."""
    from db_models import (
        Candidate, Education, Experience, Skill,
        Publication, Book, Patent, SupervisedStudent,
    )
    from db_connect import get_session
    # FIX 4: import Redis helper
    from redis_cache import mark_as_cached

    if state.get("error"):
        return {"error": state.get("error")}

    session     = get_session()
    all_results = state.get("all_results", [])

    if not all_results:
        return {"all_results": all_results}

    degree_level_map = {
        "ssc":"school","ssic":"school","hssc":"school","matric":"school",
        "intermediate":"school","ics":"school",
        "bs":"undergrad","bsc":"undergrad","be":"undergrad","b.e":"undergrad",
        "b.s":"undergrad","b.eng":"undergrad","b.tech":"undergrad",
        "bachelor":"undergrad","b.arch":"undergrad","diploma":"undergrad",
        "ms":"postgrad","msc":"postgrad","mphil":"postgrad","mba":"postgrad",
        "m.engg":"postgrad","m.eng":"postgrad","master":"postgrad","m.s":"postgrad",
        "me":"postgrad","m.tech":"postgrad","m.arch":"postgrad","pgdip":"postgrad",
        "phd":"doctorate","ph.d":"doctorate","d.sc":"doctorate",
        "d.phil":"doctorate","dphil":"doctorate",
    }

    try:
        for extracted in all_results:
            if "error" in extracted:
                continue

            cid      = extracted.get("_candidate_id", "unknown")
            cv_text  = extracted.get("_cv_text", "")   # FIX 4: retrieved for Redis
            info     = extracted.get("personal_info", {})
            name     = info.get("name", "Unknown")

            candidate = session.query(Candidate).filter_by(candidate_id=cid).first()
            is_new    = candidate is None

            if is_new:
                candidate = Candidate(candidate_id=cid)
                session.add(candidate)
                print(f"\n  💾 NEW candidate: {name}")
            else:
                print(f"\n  🔄 UPDATING existing: {candidate.name}")

            candidate.name  = info.get("name")
            candidate.email = info.get("email")
            candidate.phone = info.get("phone")
            session.flush()
            print(f"     DB ID: {candidate.id} | candidate_id: {cid}")

            for model in (Education, Experience, Skill, Publication,
                          Book, Patent, SupervisedStudent):
                session.query(model).filter_by(candidate_id=candidate.id).delete()

            for edu in extracted.get("education", []):
                deg   = (edu.get("degree") or "").lower()
                level = degree_level_map.get(deg.split()[0] if deg else "", "other")
                session.add(Education(
                    candidate_id          = candidate.id,
                    degree                = edu.get("degree"),
                    degree_level          = level,
                    field                 = edu.get("field"),
                    institution           = edu.get("institution"),
                    board                 = edu.get("board"),
                    start_year            = edu.get("start_year"),
                    end_year              = edu.get("end_year"),
                    cgpa                  = edu.get("cgpa"),
                    cgpa_scale            = edu.get("cgpa_scale"),
                    percentage            = edu.get("percentage"),
                    normalized_percentage = edu.get("normalized_percentage"),
                ))

            for exp in extracted.get("experience", []):
                session.add(Experience(
                    candidate_id    = candidate.id,
                    company         = exp.get("company"),
                    role            = exp.get("role"),
                    employment_type = exp.get("employment_type"),
                    start_date      = exp.get("start_date"),
                    end_date        = exp.get("end_date"),
                    description     = exp.get("description"),
                ))

            for skill in extracted.get("skills", []):
                session.add(Skill(
                    candidate_id = candidate.id,
                    skill_name   = skill,
                    inferred     = not bool(extracted.get("_skills_from_cv", True)),
                ))

            for pub in extracted.get("publications", []):
                session.add(Publication(
                    candidate_id          = candidate.id,
                    pub_type              = pub.get("type", "journal"),
                    title                 = pub.get("title"),
                    venue                 = pub.get("venue"),
                    issn                  = pub.get("issn"),
                    year                  = pub.get("year"),
                    authors               = ", ".join(pub.get("authors", [])),
                    authorship_role       = pub.get("authorship_role"),
                    wos_indexed           = pub.get("wos_indexed"),
                    scopus_indexed        = pub.get("scopus_indexed"),
                    quartile              = pub.get("quartile"),
                    impact_factor         = pub.get("impact_factor"),
                    core_rank             = pub.get("core_rank"),
                    indexed_in            = pub.get("indexed_in"),
                    doi                   = pub.get("doi"),
                    publisher             = pub.get("publisher"),
                    journal_name          = pub.get("journal_name"),
                    conference_name       = pub.get("conference_name"),
                    conference_maturity   = pub.get("conference_maturity"),
                    proceedings_publisher = pub.get("proceedings_publisher"),
                ))

            for book in extracted.get("books", []):
                session.add(Book(
                    candidate_id    = candidate.id,
                    title           = book.get("title"),
                    authors         = ", ".join(book.get("authors", [])),
                    isbn            = book.get("isbn"),
                    publisher       = book.get("publisher"),
                    year            = book.get("year"),
                    url             = book.get("url"),
                    authorship_role = book.get("authorship_role"),
                ))

            for pat in extracted.get("patents", []):
                session.add(Patent(
                    candidate_id     = candidate.id,
                    patent_number    = pat.get("patent_number"),
                    title            = pat.get("title"),
                    year             = pat.get("year"),
                    inventors        = ", ".join(pat.get("inventors", [])),
                    country          = pat.get("country"),
                    verification_url = pat.get("verification_url"),
                ))

            for stu in extracted.get("supervised_students", []):
                session.add(SupervisedStudent(
                    candidate_id    = candidate.id,
                    student_name    = stu.get("student_name"),
                    level           = stu.get("level"),
                    role            = stu.get("role"),
                    graduation_year = stu.get("graduation_year"),
                ))

            edu_c  = len(extracted.get("education",    []))
            exp_c  = len(extracted.get("experience",   []))
            skl_c  = len(extracted.get("skills",       []))
            pub_c  = len(extracted.get("publications", []))
            bk_c   = len(extracted.get("books",        []))
            pat_c  = len(extracted.get("patents",      []))
            stu_c  = len(extracted.get("supervised_students", []))
            print(f"     ✓ Education:{edu_c}  Exp:{exp_c}  Skills:{skl_c}  "
                  f"Pubs:{pub_c}  Books:{bk_c}  Patents:{pat_c}  Students:{stu_c}")

        session.commit()
        print(f"\n  ✅ Database commit successful")

        # FIX 4: Write hash to Redis AFTER successful DB commit
        for extracted in all_results:
            if "error" not in extracted:
                cv_text = extracted.get("_cv_text", "")
                cid     = extracted.get("_candidate_id", "unknown")
                if cv_text:
                    mark_as_cached(cv_text, cid)

    except Exception as e:
        session.rollback()
        import traceback; traceback.print_exc()
        print(f"  ❌ Database error: {e}")
        raise
    finally:
        session.close()

    return {"all_results": all_results}


async def education_analysis(state: CVState) -> dict:
    """Score education profile and persist to EducationScore table."""
    from db_connect import get_session
    from db_models import Candidate
    from edu_scores import score_education, save_education_score

    all_results = state.get("all_results", [])

    for result in all_results:
        if "error" in result:
            continue

        candidate_id_str = result.get("_candidate_id", "unknown")
        try:
            session = get_session()
            cand = session.query(Candidate).filter_by(candidate_id=candidate_id_str).first()
            if not cand:
                session.close()
                result["education_analysis"] = {"error": "Candidate not in database"}
                continue

            candidate_data = {
                "id": cand.id, "candidate_id": cand.candidate_id,
                "name": cand.name, "email": cand.email, "phone": cand.phone,
                "education": [
                    {"id":e.id,"degree":e.degree,"degree_level":e.degree_level,
                     "field":e.field,"institution":e.institution,"board":e.board,
                     "start_year":e.start_year,"end_year":e.end_year,"cgpa":e.cgpa,
                     "cgpa_scale":e.cgpa_scale,"percentage":e.percentage,
                     "normalized_percentage":e.normalized_percentage}
                    for e in cand.education
                ],
                "experience": [
                    {"id":ex.id,"company":ex.company,"role":ex.role,
                     "employment_type":ex.employment_type,"start_date":ex.start_date,
                     "end_date":ex.end_date,"description":ex.description}
                    for ex in cand.experience
                ],
            }
            session.close()

            edu_result = score_education(candidate_data)
            save_education_score(cand.id, edu_result)
            score = edu_result["final_total"]
            grade = edu_result["label"]
            print(f"  📚 Education    : {score:6.1f}/100  [{grade}]")

            result["education_analysis"] = {
                "score": score, "grade": grade,
                "base_total": edu_result["base_total"],
                "bonus": edu_result["bonus"],
                "components": edu_result["components"],
            }

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ❌ Education analysis error: {e}")
            result["education_analysis"] = {"error": str(e)}

    return {"all_results": all_results}


async def research_analysis(state: CVState) -> dict:
    """Score research profile and persist to ResearchScore table."""
    from db_connect import get_session
    from db_models import Candidate
    from research_scores import score_candidate_research

    all_results = state.get("all_results", [])

    for result in all_results:
        if "error" in result:
            continue

        candidate_id_str = result.get("_candidate_id", "unknown")
        try:
            session = get_session()
            cand = session.query(Candidate).filter_by(candidate_id=candidate_id_str).first()
            session.close()
            if not cand:
                result["research_analysis"] = {"error": "Candidate not in database"}
                continue

            research_result = await score_candidate_research(cand.id)
            if "error" in research_result:
                result["research_analysis"] = research_result
                continue

            score = research_result["score"]
            grade = research_result["grade"]
            print(f"  🔬 Research     : {score:6.1f}/100  [{grade}]")

            result["research_analysis"] = {
                "score": score, "grade": grade,
                "base_total": research_result["base_total"],
                "components": research_result["components"],
                "counts":     research_result["counts"],
                "warnings":   research_result.get("warnings", []),
                "recommendations": research_result.get("recommendations", []),
            }

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ❌ Research analysis error: {e}")
            result["research_analysis"] = {"error": str(e)}

    return {"all_results": all_results}


async def experiance_skill_analysis(state: CVState) -> dict:
    """Score experience + skill alignment and persist to DB."""
    from db_connect import get_session
    from db_models import Candidate
    from experiance_skill_score import run_candidate, save_professional_and_skill_scores

    all_results = state.get("all_results", [])

    for result in all_results:
        if "error" in result:
            continue

        candidate_id_str = result.get("_candidate_id", "unknown")
        try:
            session = get_session()
            cand = session.query(Candidate).filter_by(candidate_id=candidate_id_str).first()
            session.close()
            if not cand:
                result["experience_skill_analysis"] = {"error": "Candidate not in database"}
                continue

            pipeline_result = run_candidate(candidate_id=cand.id)
            if not pipeline_result:
                result["experience_skill_analysis"] = {"error": "Pipeline returned no results"}
                continue

            combined = pipeline_result.get("combined", {})
            s38      = pipeline_result.get("score_38", {})
            s39      = pipeline_result.get("score_39", {})
            score    = combined.get("final_score", 0)
            grade    = combined.get("grade", "?")

            save_professional_and_skill_scores(cand.id, pipeline_result)
            print(f"  💼 Exp & Skills : {score:6.1f}/100  [{grade}]  "
                  f"(3.8: {s38.get('raw',0):.1f}/60 | 3.9: {s39.get('raw',0):.1f}/40)")

            result["experience_skill_analysis"] = {
                "final_score": score, "grade": grade,
                "module_38": {"score": s38.get("raw",0), "max": s38.get("max",60),
                              "components": s38.get("scores",{})},
                "module_39": {"applicable": s39.get("applicable",False),
                              "score": s39.get("raw",0) if s39.get("applicable") else None,
                              "max": s39.get("max",40) if s39.get("applicable") else None,
                              "components": s39.get("scores",{}) if s39.get("applicable") else None,
                              "reason": s39.get("reason","")},
                "combined_note":   combined.get("note",""),
                "timeline_flags":  pipeline_result.get("timeline",{}).get("flags",[]),
                "career_notes":    pipeline_result.get("career",{}).get("notes",[]),
                "inquiry_email_draft": pipeline_result.get("email_draft"),
            }

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ❌ Experience/skill analysis error: {e}")
            result["experience_skill_analysis"] = {"error": str(e)}

    return {"all_results": all_results}


async def tvs_ccs_analysis(state: CVState) -> dict:
    """Analyse topic variability & co-author collaboration (informational)."""
    from db_connect import get_session
    from db_models import Candidate
    from tvs_ccs_score import run_36_37, save_topic_and_coauthor_scores

    all_results = state.get("all_results", [])

    for result in all_results:
        if "error" in result:
            continue

        candidate_id_str = result.get("_candidate_id", "unknown")
        try:
            session = get_session()
            cand = session.query(Candidate).filter_by(candidate_id=candidate_id_str).first()
            if not cand:
                session.close()
                result["tvs_ccs_analysis"] = {"error": "Candidate not in database"}
                continue

            candidate_data = {
                "id": cand.id, "candidate_id": cand.candidate_id, "name": cand.name,
                "publications": [
                    {"id":p.id,"title":p.title,"authors":p.authors,"year":p.year,
                     "pub_type": p.pub_type.value if p.pub_type else None,
                     "venue":p.venue,"journal_name":p.journal_name,
                     "conference_name":p.conference_name}
                    for p in cand.publications
                ],
            }
            session.close()

            pipeline_result = run_36_37(candidate=candidate_data)
            if not pipeline_result:
                result["tvs_ccs_analysis"] = {"error": "Pipeline returned no results"}
                continue

            topic    = pipeline_result.get("topic_variability", {})
            coauthor = pipeline_result.get("coauthor_analysis", {})
            t_ok     = topic.get("applicable", False)
            c_ok     = coauthor.get("applicable", False)

            save_topic_and_coauthor_scores(cand.id, pipeline_result)
            print(f"  📊 TVS/CCS      :  Topic {'✓' if t_ok else '–'}  "
                  f"Co-author {'✓' if c_ok else '–'}")

            result["tvs_ccs_analysis"] = {
                "module_36": {
                    "applicable": t_ok,
                    "reason": topic.get("reason",""),
                    "diversity_score": topic.get("diversity_score"),
                    "focus_type": topic.get("focus_type"),
                    "dominant_theme": topic.get("dominant_theme"),
                    "topic_trend": topic.get("topic_trend"),
                    "themes_count": len(topic.get("themes",[])),
                    "overall_interpretation": topic.get("overall_interpretation",""),
                },
                "module_37": {
                    "applicable": c_ok,
                    "reason": coauthor.get("reason",""),
                    "unique_coauthors": coauthor.get("unique_coauthors"),
                    "network_diversity_score": coauthor.get("network_diversity_score"),
                    "collaboration_style": coauthor.get("collaboration_style"),
                    "collaboration_type": coauthor.get("collaboration_type"),
                    "international_flag": coauthor.get("international_flag"),
                    "recurring_collaborators": coauthor.get("recurring_collaborators"),
                    "interpretation": coauthor.get("interpretation",""),
                },
            }

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ❌ TVS/CCS analysis error: {e}")
            result["tvs_ccs_analysis"] = {"error": str(e)}

    return {"all_results": all_results}


async def summarizers(state: CVState) -> dict:
    """Generate weighted overall summary and persist to CVSummary table."""
    from db_connect import get_session
    from db_models import Candidate
    from summarizers import (
        generate_education_report,
        generate_research_report,
        generate_experience_skills_report,
        generate_tvs_ccs_report,
        generate_overall_summary,
        save_summary_to_database,
    )

    all_results = state.get("all_results", [])

    for result in all_results:
        if "error" in result or result.get("_summarized"):
            continue

        candidate_id_str = result.get("_candidate_id", "unknown")

        required_keys = [
            "education_analysis","research_analysis",
            "experience_skill_analysis","tvs_ccs_analysis",
        ]
        missing = [k for k in required_keys if k not in result]
        if missing:
            print(f"  ⚠️  Summarizer skipping {candidate_id_str} — missing: {missing}")
            continue

        try:
            session = get_session()
            cand = session.query(Candidate).filter_by(candidate_id=candidate_id_str).first()
            session.close()
            if not cand:
                result["summary"] = {"error": "Candidate not in database"}
                continue

            edu_report      = generate_education_report(result.get("education_analysis",{}))
            research_report = generate_research_report(result.get("research_analysis",{}))
            exp_report      = generate_experience_skills_report(result.get("experience_skill_analysis",{}))
            tvs_report      = generate_tvs_ccs_report(result.get("tvs_ccs_analysis",{}))

            all_reports = {
                "education": edu_report,
                "research":  research_report,
                "experience":exp_report,
                "tvs_ccs":   tvs_report,
            }

            overall = generate_overall_summary(
                candidate_name=cand.name or "Unknown",
                candidate_id=candidate_id_str,
                all_reports=all_reports,
            )

            save_summary_to_database(cand.id, overall)

            score  = overall["overall_score"]
            grade  = overall["overall_grade"]
            status = overall["overall_status"]
            print(f"  📝 OVERALL      : {score:6.1f}/100  [{grade}]  → {status}")

            result["summary"] = {
                "overall_score":   score,
                "overall_grade":   grade,
                "overall_status":  status,
                "module_summary":  overall["module_summary"],
                "top_strengths":   overall["top_strengths"],
                "top_weaknesses":  overall["top_weaknesses"],
                "recommendations": overall["recommendations"],
                "interpretation":  overall["summary_interpretation"],
            }
            result["_summarized"] = True

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  ❌ Summarizer error: {e}")
            result["summary"] = {"error": str(e)}

    return {"all_results": all_results}


# ============================================================================
# LangGraph — SEQUENTIAL pipeline
# ============================================================================

_graph = StateGraph(CVState)
_graph.add_node("llm_extractor",             llm_extractor)
_graph.add_node("database_storage",          database_storage)
_graph.add_node("education_analysis",        education_analysis)
_graph.add_node("research_analysis",         research_analysis)
_graph.add_node("experiance_skill_analysis", experiance_skill_analysis)
_graph.add_node("tvs_ccs_analysis",          tvs_ccs_analysis)
_graph.add_node("summarizers",               summarizers)

_graph.add_edge(START,                        "llm_extractor")
_graph.add_edge("llm_extractor",              "database_storage")
_graph.add_edge("database_storage",           "education_analysis")
_graph.add_edge("education_analysis",         "research_analysis")
_graph.add_edge("research_analysis",          "experiance_skill_analysis")
_graph.add_edge("experiance_skill_analysis",  "tvs_ccs_analysis")
_graph.add_edge("tvs_ccs_analysis",           "summarizers")
_graph.add_edge("summarizers",                END)

app = _graph.compile()


# ============================================================================
# Public API
# ============================================================================

_DIVIDER = "─" * 60


async def process_single_cv(
    cv_label: str,
    cv_text:  str,
    cv_num:   int = 0,
    cv_total: int = 0,
) -> dict:
    num_tag = f"[{cv_num}/{cv_total}]" if cv_total else ""

    print(f"\n{_DIVIDER}")
    print(f"▶  CV {num_tag}  {cv_label}")
    print(_DIVIDER)

    state = CVState(
        pdf_path="",
        raw_texts=[(cv_label, cv_text)],
        all_results=[],
        error=None,
    )

    try:
        final_state = await app.ainvoke(state)
        results     = final_state.get("all_results", [])

        if not results:
            print(f"  ❌ No results returned")
            return {"_candidate_id": cv_label, "error": "No results"}

        result = results[0]

        info   = result.get("personal_info", {}) or {}
        name   = info.get("name") or result.get("_candidate_id", "Unknown")
        summ   = result.get("summary", {}) or {}
        score  = summ.get("overall_score", "—")
        grade  = summ.get("overall_grade", "—")
        status = summ.get("overall_status", "—")

        if "error" not in result:
            print(f"\n  ✅ CV {num_tag} COMPLETE")
            print(f"     Name   : {name}")
            print(f"     Score  : {score}/100  [{grade}]  → {status}")
        else:
            print(f"\n  ⚠️  CV {num_tag} had errors: {result.get('error')}")

        return result

    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"\n  ❌ Fatal error processing {cv_label}: {e}")
        return {"_candidate_id": cv_label, "error": str(e)}


async def process_all_cvs_sequential(pdf_path: str) -> list:
    # FIX 4: import Redis helper
    from redis_cache import is_cached, get_cached_candidate_id
    from db_connect import get_session
    from db_models import Candidate

    _WIDE = "═" * 60

    print(f"\n{_WIDE}")
    print("  CV PROCESSING PIPELINE")
    print(_WIDE)
    print(f"  PDF: {pdf_path}")

    print(f"\n{'─'*60}")
    print("  STEP 1 — PARSING")
    print(f"{'─'*60}")

    parser_state  = CVState(pdf_path=pdf_path, raw_texts=[], all_results=[], error=None)
    parser_result = parser(parser_state)

    if parser_result.get("error"):
        print(f"  ❌ Parser error: {parser_result['error']}")
        return []

    raw_texts = parser_result.get("raw_texts", [])

    if not raw_texts:
        print("  ⚠️  No CVs found in this PDF")
        return []

    print(f"\n{'─'*60}")
    print("  STEP 2 — REDIS CACHE CHECK")
    print(f"{'─'*60}")

    # ── FIX 4: Split into cached vs needs-processing ──────────────────────────
    to_process: list[tuple[str, str]] = []
    skipped_results: list[dict]       = []

    for label, text in raw_texts:
        cached_id = get_cached_candidate_id(text)   # returns candidate_id str or None
        if cached_id:
            print(f"  ⚡ CACHE HIT  — {label}  (already processed as {cached_id})")
            # Return a lightweight result so callers still get a record
            session = get_session()
            cand = session.query(Candidate).filter_by(candidate_id=cached_id).first()
            session.close()
            if cand:
                skipped_results.append({
                    "_candidate_id": cached_id,
                    "_from_cache":   True,
                    "personal_info": {
                        "name":  cand.name,
                        "email": cand.email,
                        "phone": cand.phone,
                    },
                })
            else:
                # Hash was in Redis but candidate was deleted from DB — reprocess
                print(f"    ⚠️  Candidate not found in DB — will reprocess")
                to_process.append((label, text))
        else:
            print(f"  🆕 CACHE MISS — {label}  (will process)")
            to_process.append((label, text))

    # ── Show queue status ─────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  STEP 3 — QUEUE")
    print(f"{'─'*60}")

    total_found  = len(raw_texts)
    total_skip   = len(skipped_results)
    total_new    = len(to_process)

    print(f"  Total CVs in PDF : {total_found}")
    print(f"  Skipped (cached) : {total_skip}")
    print(f"  To process       : {total_new}")

    if not to_process:
        print("\n  ✅ All CVs already in cache — nothing to process!")
        return skipped_results

    print(f"\n{'─'*60}")
    print("  STEP 4 — PROCESSING")
    print(f"{'─'*60}")

    all_results = list(skipped_results)   # start with the cached ones
    for i, (label, text) in enumerate(to_process, 1):
        result = await process_single_cv(
            cv_label = label,
            cv_text  = text,
            cv_num   = i,
            cv_total = total_new,
        )
        all_results.append(result)

        if i < total_new:
            name = (result.get("personal_info") or {}).get("name", "")
            print(f"\n  → Saved to database: {name or label}")
            print(f"  → Starting CV [{i+1}/{total_new}] ...")

    print(f"\n{_WIDE}")
    success = sum(1 for r in all_results if "error" not in r)
    total   = len(all_results)
    print(f"  🎉 ALL {total} CV(s) DONE  ({success} succeeded, {total-success} errors, {total_skip} from cache)")
    print(_WIDE)

    for r in all_results:
        info   = (r.get("personal_info") or {})
        name   = info.get("name") or r.get("_candidate_id", "?")
        summ   = r.get("summary") or {}
        score  = summ.get("overall_score", "—")
        grade  = summ.get("overall_grade", "—")
        status = summ.get("overall_status", "—")
        cached_tag = " [cache]" if r.get("_from_cache") else ""
        marker = "⚡" if r.get("_from_cache") else ("✅" if "error" not in r else "❌")
        print(f"    {marker}  {name:<30}  {str(score):>6}/100  [{grade}]  {status}{cached_tag}")

    print()
    return all_results


def run_pipeline(pdf_path: str) -> list:
    """Synchronous wrapper — spawns its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process_all_cvs_sequential(pdf_path))
    finally:
        loop.close()


# ============================================================================
# Initialise DB on import / direct run
# ============================================================================

from db_connect import init_db
init_db()

if __name__ == "__main__":
    pdf_path = r"C:\Projects\Talash\Cvs\output_first_10_pages.pdf"
    results  = run_pipeline(pdf_path)
    print(f"\nDone — {len(results)} CV(s) processed")
    for r in results:
        if "error" not in r:
            name = (r.get("personal_info") or {}).get("name", "Unknown")
            tag  = " [from cache]" if r.get("_from_cache") else ""
            print(f"  ✓  {name}{tag}")
        else:
            print(f"  ✗  {r.get('error')}")