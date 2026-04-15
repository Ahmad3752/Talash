import os
import json
import re
import time
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class DegreeRecord(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa: Optional[float] = None
    cgpa_scale: Optional[float] = None
    percentage: Optional[float] = None
    board: Optional[str] = None

    @field_validator("start_year", "end_year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a", "na", "none", "null", ""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None

    @field_validator("cgpa", "cgpa_scale", "percentage", mode="before")
    @classmethod
    def parse_float(cls, v):
        if v is None or str(v).strip().lower() in {"n/a", "na", "none", "null", ""}:
            return None
        try:
            return float(str(v).replace("%", "").replace("/4.0", "").replace("/5.0", "").strip())
        except:
            return None


class ExperienceRecord(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v is None or str(v).strip().lower() in {
            "n/a",
            "na",
            "none",
            "null",
            "",
            "present",
            "current",
            "till date",
            "to date",
        }:
            return None
        v = str(v).strip()
        if re.match(r"^\d{4}-\d{1,2}$", v):
            parts = v.split("-")
            return f"{parts[0]}-{int(parts[1]):02d}"
        months = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        match = re.search(
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,.\-]+(\d{4})",
            v.lower(),
        )
        if match:
            return f"{match.group(2)}-{months[match.group(1)[:3]]:02d}"
        match = re.search(
            r"(\d{4})[\s,.\-]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*",
            v.lower(),
        )
        if match:
            return f"{match.group(1)}-{months[match.group(2)[:3]]:02d}"
        match = re.search(r"\b(19|20)\d{2}\b", v)
        if match:
            return match.group()
        return None


class Publication(BaseModel):
    type: Literal["journal", "conference"] = "journal"
    title: Optional[str] = None
    venue: Optional[str] = None
    issn: Optional[str] = None
    year: Optional[int] = None
    authors: List[str] = Field(default_factory=list)
    authorship_role: Optional[
        Literal["first", "corresponding", "first_and_corresponding", "co_author"]
    ] = None
    wos_indexed: Optional[bool] = None
    scopus_indexed: Optional[bool] = None
    quartile: Optional[Literal["Q1", "Q2", "Q3", "Q4"]] = None
    impact_factor: Optional[float] = None
    core_rank: Optional[str] = None
    indexed_in: Optional[str] = None

    @field_validator("year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a", "na", "none", "null", ""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class Book(BaseModel):
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    authorship_role: Optional[Literal["sole", "lead", "co_author", "contributing"]] = None

    @field_validator("year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a", "na", "none", "null", ""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class Patent(BaseModel):
    patent_number: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    inventors: List[str] = Field(default_factory=list)
    country: Optional[str] = None
    verification_url: Optional[str] = None

    @field_validator("year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a", "na", "none", "null", ""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class SupervisionRecord(BaseModel):
    student_name: Optional[str] = None
    level: Optional[Literal["MS", "PhD"]] = None
    role: Optional[Literal["main", "co_supervisor"]] = None
    graduation_year: Optional[int] = None

    @field_validator("graduation_year", mode="before")
    @classmethod
    def parse_year(cls, v):
        if v is None or str(v).strip().lower() in {"n/a", "na", "none", "null", ""}:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None


class CVExtraction(BaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    education: List[DegreeRecord] = Field(default_factory=list)
    experience: List[ExperienceRecord] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    books: List[Book] = Field(default_factory=list)
    patents: List[Patent] = Field(default_factory=list)
    supervised_students: List[SupervisionRecord] = Field(default_factory=list)


openrouter_key = os.getenv("OPENROUTER_API_KEY")
llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
)
structured_llm = llm.with_structured_output(CVExtraction)

MAX_INFERRED_SKILLS = 15


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
- Use null for every missing/unknown field - NEVER use "N/A", "Present", ""
- SSC and HSSC go inside the "education" list with degree="SSC" or degree="HSSC"
- ALL publications (journals + conferences) go in the single "publications" list
- Return a comprehensive skills list from the CV, with up to 15 unique items
- Prioritize technical/research skills over generic soft skills
- Dates MUST be "YYYY-MM": convert "Sep-2017" to "2017-09"
- If end_date is "Present" or "current" use null
- Years must be integers, CGPA must be floats
- Extract ALL entries, never truncate

CV TEXT:
{cv_text}
"""


def clean_nulls(obj):
    null_strings = {
        "n/a",
        "na",
        "none",
        "null",
        "not mentioned",
        "not available",
        "not applicable",
        "",
        "-",
    "present",
    "current",
    }
    if isinstance(obj, dict):
        return {k: clean_nulls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nulls(i) for i in obj]
    if isinstance(obj, str) and obj.strip().lower() in null_strings:
        return None
    return obj


def normalize_education(education_list: list) -> list:
    for edu in education_list:
        cgpa = edu.get("cgpa")
        scale = edu.get("cgpa_scale")
        pct = edu.get("percentage")

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
Based ONLY on the job titles, roles, and publication titles below, list the most likely
technical AND research skills this person has. Include both soft skills AND
domain-specific technical skills extracted from publication topics.

Return ONLY a valid JSON array of strings. No explanation. No markdown. No preamble.
Maximum {max_skills} skills. Prioritize technical/research skills over generic ones.

Job titles / roles: {roles}
Publication titles: {pub_titles}

Example: ["Wireless Sensor Networks", "Deep Learning", "Python", "Research", "Teaching"]
"""



def infer_skills_if_missing(extracted: dict) -> dict:
    if extracted.get("skills"):
        extracted["_skills_from_cv"] = True
        return extracted

    roles = [e.get("role", "") for e in extracted.get("experience", []) if e.get("role")]
    pub_titles = [p.get("title", "") for p in extracted.get("publications", []) if p.get("title")][:8]

    if not roles and not pub_titles:
        extracted["_skills_from_cv"] = True
        return extracted

    extracted["_skills_from_cv"] = False
    try:
        prompt = SKILL_INFERENCE_PROMPT.format(
            roles=", ".join(roles),
            pub_titles="; ".join(pub_titles),
            max_skills=MAX_INFERRED_SKILLS,
        )
        response = llm.invoke(prompt)
        raw = response.content.strip()
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
        inferred = json.loads(raw)
        if isinstance(inferred, list):
            extracted["skills"] = [s for s in inferred if isinstance(s, str)][:MAX_INFERRED_SKILLS]
        else:
            extracted["skills"] = []
    except Exception as e:
        print(f"Skill inference failed: {e}")
        extracted["skills"] = []

    return extracted


def infer_skills_from_text(cv_text: str, max_items: int = MAX_INFERRED_SKILLS) -> list[str]:
    """Best-effort deterministic skill extraction from raw CV text."""
    if not cv_text:
        return []

    text = cv_text.lower()
    keyword_map = {
        "python": "Python",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "data science": "Data Science",
        "sql": "SQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scikit": "Scikit-learn",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "git": "Git",
        "linux": "Linux",
        "excel": "Excel",
        "power bi": "Power BI",
        "tableau": "Tableau",
        "research": "Research",
        "teaching": "Teaching",
        "supervision": "Supervision",
    }

    found = []
    for needle, label in keyword_map.items():
        if needle in text and label not in found:
            found.append(label)
        if len(found) >= max_items:
            break
    return found


def heuristic_extract(cv_text: str) -> dict:
    """Fallback extractor used when LLM calls are unavailable."""
    text = cv_text or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(?:\+?\d[\d\-\s()]{7,}\d)", text)

    name = None
    for ln in lines[:8]:
        if any(tok in ln.lower() for tok in ["curriculum", "vitae", "resume", "email", "phone"]):
            continue
        if len(ln.split()) >= 2 and len(ln.split()) <= 5 and re.search(r"[A-Za-z]", ln):
            name = ln
            break

    return {
        "personal_info": {
            "name": name,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0).strip() if phone_match else None,
        },
        "education": [],
        "experience": [],
        "skills": infer_skills_from_text(text),
        "publications": [],
        "books": [],
        "patents": [],
        "supervised_students": [],
        "_skills_from_cv": False,
        "_fallback_extraction": True,
    }


def invoke_with_retries(callable_fn, max_attempts: int = 3, base_delay: float = 1.2):
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return callable_fn()
        except Exception as exc:
            last_err = exc
            if attempt >= max_attempts:
                break
            wait_s = round(base_delay * (2 ** (attempt - 1)), 2)
            print(f"Attempt {attempt}/{max_attempts} failed: {exc}. Retrying in {wait_s}s")
            time.sleep(wait_s)
    raise last_err


def llm_extractor(state: dict) -> dict:
    if state.get("error"):
        return {}

    all_results = []
    raw_texts = state.get("raw_texts", [])
    total = len(raw_texts)

    for idx, (candidate_id, text) in enumerate(raw_texts, 1):
        print(f"[{idx}/{total}] Extracting -> {candidate_id}")

        if len(text) < 100:
            print(f"Very short text ({len(text)} chars), continuing with best-effort extraction")

        try:
            prompt = EXTRACTION_PROMPT.format(cv_text=text)
            result: CVExtraction = invoke_with_retries(
                lambda: structured_llm.invoke(prompt),
                max_attempts=3,
                base_delay=1.2,
            )
            extracted = result.model_dump()

            if "journal_publications" in extracted or "ssc_hssc" in extracted:
                print("Schema mismatch detected, using raw JSON fallback")
                raw_resp = invoke_with_retries(
                    lambda: llm.invoke(prompt),
                    max_attempts=2,
                    base_delay=1.0,
                )
                raw_text = re.sub(
                    r"^```json\s*|^```\s*|```$",
                    "",
                    raw_resp.content.strip(),
                    flags=re.MULTILINE,
                ).strip()
                extracted = json.loads(raw_text)

            extracted = clean_nulls(extracted)
            if extracted.get("education"):
                extracted["education"] = normalize_education(extracted["education"])
            extracted = infer_skills_if_missing(extracted)
            if not extracted.get("skills"):
                extracted["skills"] = infer_skills_from_text(text)
                if extracted["skills"]:
                    extracted["_skills_from_cv"] = False
            extracted["_candidate_id"] = candidate_id
            all_results.append(extracted)
        except Exception as e:
            print(f"LLM extraction failed for {candidate_id}: {e}. Using heuristic fallback.")
            fallback = heuristic_extract(text)
            fallback["_candidate_id"] = candidate_id
            fallback["_fallback_reason"] = str(e)
            all_results.append(fallback)

    return {"all_results": all_results}
