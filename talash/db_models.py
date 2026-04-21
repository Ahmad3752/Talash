# db_models.py — full updated file

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

Base = declarative_base()

# ── Enums ─────────────────────────────────────────────────────────────────

class AuthorshipRoleEnum(str, enum.Enum):
    first = "first"
    corresponding = "corresponding"
    first_and_corresponding = "first_and_corresponding"
    co_author = "co_author"

class PublicationTypeEnum(str, enum.Enum):
    journal = "journal"
    conference = "conference"

class SupervisionRoleEnum(str, enum.Enum):
    main = "main"
    co_supervisor = "co_supervisor"

class SupervisionLevelEnum(str, enum.Enum):
    MS = "MS"
    PhD = "PhD"

# ── Candidate ─────────────────────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(String, unique=True, nullable=False)
    name            = Column(String)
    email           = Column(String)
    phone           = Column(String)

    education           = relationship("Education",         back_populates="candidate", cascade="all, delete-orphan")
    experience          = relationship("Experience",        back_populates="candidate", cascade="all, delete-orphan")
    skills              = relationship("Skill",             back_populates="candidate", cascade="all, delete-orphan")
    publications        = relationship("Publication",       back_populates="candidate", cascade="all, delete-orphan")
    books               = relationship("Book",              back_populates="candidate", cascade="all, delete-orphan")
    patents             = relationship("Patent",            back_populates="candidate", cascade="all, delete-orphan")
    supervised_students = relationship("SupervisedStudent", back_populates="candidate", cascade="all, delete-orphan")

# ── Education ─────────────────────────────────────────────────────────────

class Education(Base):
    __tablename__ = "education"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id          = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    degree                = Column(String)
    degree_level          = Column(String)
    field                 = Column(String)
    institution           = Column(String)
    board                 = Column(String)
    start_year            = Column(Integer)
    end_year              = Column(Integer)
    cgpa                  = Column(Float)
    cgpa_scale            = Column(Float)
    percentage            = Column(Float)
    normalized_percentage = Column(Float)

    candidate = relationship("Candidate", back_populates="education")

# ── Experience ────────────────────────────────────────────────────────────

class Experience(Base):
    __tablename__ = "experience"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    company         = Column(String)
    role            = Column(String)
    employment_type = Column(String)
    start_date      = Column(String)
    end_date        = Column(String)
    description     = Column(Text)

    candidate = relationship("Candidate", back_populates="experience")

# ── Skill ─────────────────────────────────────────────────────────────────

class Skill(Base):
    __tablename__ = "skills"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    skill_name   = Column(String)
    inferred     = Column(Boolean, default=False)

    candidate = relationship("Candidate", back_populates="skills")

# ── Publication ───────────────────────────────────────────────────────────

class Publication(Base):
    __tablename__ = "publications"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    pub_type         = Column(SAEnum(PublicationTypeEnum))
    title            = Column(Text)
    venue            = Column(String)
    issn             = Column(String)
    year             = Column(Integer)
    authors          = Column(Text)
    authorship_role  = Column(SAEnum(AuthorshipRoleEnum))

    # Journal-specific (original + enriched)
    wos_indexed           = Column(Boolean)
    scopus_indexed        = Column(Boolean)
    quartile              = Column(String)
    impact_factor         = Column(Float)

    # Conference-specific (original + enriched)
    core_rank             = Column(String)
    indexed_in            = Column(String)

    # ── NEW: CrossRef enriched fields ─────────────────────────────────────
    doi                   = Column(String)   # e.g. "10.1016/j.ins.2021.01.001"
    publisher             = Column(String)   # e.g. "Elsevier", "IEEE"
    journal_name          = Column(String)   # full journal name from CrossRef
    conference_name       = Column(String)   # full conference name from CrossRef
    conference_maturity   = Column(String)   # e.g. "Annual", "Biennial"
    proceedings_publisher = Column(String)   # e.g. "ACM", "IEEE", "Springer"

    candidate = relationship("Candidate", back_populates="publications")

# ── Book ──────────────────────────────────────────────────────────────────

class Book(Base):
    __tablename__ = "books"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    title            = Column(String)
    authors          = Column(Text)
    isbn             = Column(String)
    publisher        = Column(String)
    year             = Column(Integer)
    url              = Column(String)
    authorship_role  = Column(String)

    candidate = relationship("Candidate", back_populates="books")

# ── Patent ────────────────────────────────────────────────────────────────

class Patent(Base):
    __tablename__ = "patents"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    patent_number    = Column(String)
    title            = Column(String)
    year             = Column(Integer)
    inventors        = Column(Text)
    country          = Column(String)
    verification_url = Column(String)

    candidate = relationship("Candidate", back_populates="patents")

# ── SupervisedStudent ─────────────────────────────────────────────────────

class SupervisedStudent(Base):
    __tablename__ = "supervised_students"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    student_name    = Column(String)
    level           = Column(SAEnum(SupervisionLevelEnum))
    role            = Column(SAEnum(SupervisionRoleEnum))
    graduation_year = Column(Integer)

    candidate = relationship("Candidate", back_populates="supervised_students")