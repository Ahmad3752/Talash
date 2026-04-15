from pydantic import BaseModel, Field


class UploadSummaryResponse(BaseModel):
    message: str
    extracted_candidates: int
    newly_stored_candidates: int
    errors: list[str]


class CandidateSummaryResponse(BaseModel):
    id: int
    candidate_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education_count: int
    experience_count: int
    publications_count: int


class EducationItem(BaseModel):
    degree: str | None = None
    degree_level: str | None = None
    field: str | None = None
    institution: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    normalized_percentage: float | None = None


class ExperienceItem(BaseModel):
    company: str | None = None
    role: str | None = None
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class PublicationItem(BaseModel):
    type: str | None = None
    title: str | None = None
    venue: str | None = None
    year: int | None = None


class SkillItem(BaseModel):
    skill_name: str | None = None
    inferred: bool = False


class BookItem(BaseModel):
    title: str | None = None
    publisher: str | None = None
    year: int | None = None


class PatentItem(BaseModel):
    patent_number: str | None = None
    title: str | None = None
    year: int | None = None


class CandidateResponse(CandidateSummaryResponse):
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    publications: list[PublicationItem] = Field(default_factory=list)
    skills: list[SkillItem] = Field(default_factory=list)
    books: list[BookItem] = Field(default_factory=list)
    patents: list[PatentItem] = Field(default_factory=list)
