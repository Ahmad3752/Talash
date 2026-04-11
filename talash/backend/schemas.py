from pydantic import BaseModel


class UploadSummaryResponse(BaseModel):
    message: str
    extracted_candidates: int
    newly_stored_candidates: int
    errors: list[str]


class CandidateSummaryResponse(BaseModel):
    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education_count: int
    experience_count: int
    publications_count: int
