"""Structured-output schemas for developer CV extraction."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class DeveloperProjectExtraction(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)
    evidence_source: Optional[str] = None
    production_evidence: Optional[str] = None
    measurable_impact: Optional[str] = None
    ownership_signal: Optional[str] = None
    links: list[str] = Field(default_factory=list)


class DeveloperProfileExtraction(BaseModel):
    target_role: str
    current_role: Optional[str] = None
    seniority_level: Optional[
        Literal["intern", "junior", "mid", "senior", "lead", "principal", "manager"]
    ] = None
    total_relevant_experience_months: Optional[int] = None
    programming_languages: list[str] = Field(default_factory=list)
    frameworks_libraries: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_devops_tools: list[str] = Field(default_factory=list)
    testing_tools: list[str] = Field(default_factory=list)
    architecture_practices: list[str] = Field(default_factory=list)
    projects: list[DeveloperProjectExtraction] = Field(default_factory=list)
    work_highlights: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    extraction_warnings: list[str] = Field(default_factory=list)
    extraction_confidence: Literal["low", "medium", "high"] = "medium"
