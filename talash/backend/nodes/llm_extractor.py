import os
import re
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
        if v is None or v == "N/A" or v == "":
            return None
        match = re.search(r"\b(19|20)\d{2}\b", str(v))
        return int(match.group()) if match else None

    @field_validator("cgpa", "cgpa_scale", "percentage", mode="before")
    @classmethod
    def parse_float(cls, v):
        if v is None or v == "N/A" or v == "":
            return None
        try:
            return float(str(v).replace("%", "").strip())
        except Exception:
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
        if v is None or v == "N/A" or v == "" or str(v).lower() == "present":
            return None
        v = str(v)
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
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,.-]+(\d{4})",
            v.lower(),
        )
        if match:
            return f"{match.group(2)}-{months[match.group(1)[:3]]:02d}"
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
        if v is None or v == "N/A" or v == "":
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
        if v is None or v == "N/A" or v == "":
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
        if v is None or v == "N/A" or v == "":
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
        if v is None or v == "N/A" or v == "":
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


EXTRACTION_PROMPT = """
You are a CV data extraction assistant. Extract structured information from the CV below.

STRICT OUTPUT RULES:
- Use null for ANY missing, unknown, or not-mentioned field - NEVER use "N/A", "n/a", "Not mentioned", or empty strings
- Years must be integers: 2023 not "2023" and not "Nov-2023"
- Dates must be "YYYY-MM" format: "2023-02" not "Feb 2023" not "02/2023"
- CGPA and percentages must be floats: 3.83 not "3.83/4.0"
- Combine ALL publications (journals + conferences) into one "publications" list
- Set "type" field to "journal" or "conference" accordingly
- For authorship_role use only: "first", "corresponding", "first_and_corresponding", "co_author"
- For supervision level use only: "MS" or "PhD"
- For supervision role use only: "main" or "co_supervisor"
- Extract ALL entries - do not truncate any list
- Education includes SSC, HSSC, BS, MS, MPhil, PhD - extract all levels found

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
    }
    if isinstance(obj, dict):
        return {k: clean_nulls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nulls(i) for i in obj]
    if isinstance(obj, str) and obj.strip().lower() in null_strings:
        return None
    return obj


def llm_extractor(state: dict) -> dict:
    if state.get("error"):
        return {}

    all_results = []
    raw_texts = state.get("raw_texts", [])
    total = len(raw_texts)

    for idx, (candidate_id, text) in enumerate(raw_texts, 1):
        print(f"[{idx}/{total}] Extracting -> {candidate_id}")

        if len(text) < 100:
            print(f"Skipped - too short ({len(text)} chars)")
            continue

        try:
            prompt = EXTRACTION_PROMPT.format(cv_text=text)
            result: CVExtraction = structured_llm.invoke(prompt)
            extracted = clean_nulls(result.model_dump())
            extracted["_candidate_id"] = candidate_id
            all_results.append(extracted)
        except Exception as e:
            print(f"Failed: {e}")
            all_results.append({"_candidate_id": candidate_id, "error": str(e)})

    return {"all_results": all_results}
