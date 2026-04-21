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
    issn: str | None = None
    year: int | None = None
    authorship_role: str | None = None
    doi: str | None = None
    publisher: str | None = None
    journal_name: str | None = None
    conference_name: str | None = None
    conference_maturity: str | None = None
    proceedings_publisher: str | None = None


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


class CandidateProfileEducationItem(BaseModel):
    id: int
    degree: str | None = None
    degree_level: str | None = None
    field: str | None = None
    institution: str | None = None
    board: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    cgpa: float | None = None
    cgpa_scale: float | None = None
    percentage: float | None = None
    normalized_percentage: float | None = None


class CandidateProfileExperienceItem(BaseModel):
    id: int
    company: str | None = None
    role: str | None = None
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class CandidateProfileSkillItem(BaseModel):
    id: int
    skill_name: str | None = None
    inferred: bool


class CandidateProfilePublicationItem(BaseModel):
    id: int
    pub_type: str | None = None
    title: str | None = None
    venue: str | None = None
    issn: str | None = None
    year: int | None = None
    authors: str | None = None
    authorship_role: str | None = None
    wos_indexed: bool | None = None
    scopus_indexed: bool | None = None
    quartile: str | None = None
    impact_factor: float | None = None
    core_rank: str | None = None
    indexed_in: str | None = None
    doi: str | None = None
    publisher: str | None = None
    journal_name: str | None = None
    conference_name: str | None = None
    conference_maturity: str | None = None
    proceedings_publisher: str | None = None


class CandidateProfileBookItem(BaseModel):
    id: int
    title: str | None = None
    authors: str | None = None
    isbn: str | None = None
    publisher: str | None = None
    year: int | None = None
    url: str | None = None
    authorship_role: str | None = None


class CandidateProfilePatentItem(BaseModel):
    id: int
    patent_number: str | None = None
    title: str | None = None
    year: int | None = None
    inventors: str | None = None
    country: str | None = None
    verification_url: str | None = None


class CandidateProfileSupervisedStudentItem(BaseModel):
    id: int
    student_name: str | None = None
    level: str | None = None
    role: str | None = None
    graduation_year: int | None = None


class CandidateProfileResponse(BaseModel):
    id: int
    candidate_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education: list[CandidateProfileEducationItem] = Field(default_factory=list)
    experience: list[CandidateProfileExperienceItem] = Field(default_factory=list)
    skills: list[CandidateProfileSkillItem] = Field(default_factory=list)
    publications: list[CandidateProfilePublicationItem] = Field(default_factory=list)
    books: list[CandidateProfileBookItem] = Field(default_factory=list)
    patents: list[CandidateProfilePatentItem] = Field(default_factory=list)
    supervised_students: list[CandidateProfileSupervisedStudentItem] = Field(default_factory=list)
