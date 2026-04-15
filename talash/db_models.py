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
    candidate_id    = Column(String, unique=True, nullable=False)  # e.g. "cv_1"
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

    degree                = Column(String)   # "PhD", "MS", "BS", "HSSC", "SSC"
    degree_level          = Column(String)   # "school", "undergrad", "postgrad", "doctorate"
    field                 = Column(String)   # specialization
    institution           = Column(String)
    board                 = Column(String)   # for SSC/HSSC only
    start_year            = Column(Integer)
    end_year              = Column(Integer)
    cgpa                  = Column(Float)
    cgpa_scale            = Column(Float)    # 4.0 or 5.0
    percentage            = Column(Float)    # original percentage if given
    normalized_percentage = Column(Float)    # always computed — used for scoring

    candidate = relationship("Candidate", back_populates="education")

# ── Experience ────────────────────────────────────────────────────────────

class Experience(Base):
    __tablename__ = "experience"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    company         = Column(String)
    role            = Column(String)
    employment_type = Column(String)
    start_date      = Column(String)   # stored as "YYYY-MM"
    end_date        = Column(String)   # stored as "YYYY-MM" or null
    description     = Column(Text)

    candidate = relationship("Candidate", back_populates="experience")

# ── Skill ─────────────────────────────────────────────────────────────────

class Skill(Base):
    __tablename__ = "skills"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    skill_name   = Column(String)
    inferred     = Column(Boolean, default=False)  # True if LLM-inferred, not from CV

    candidate = relationship("Candidate", back_populates="skills")

# ── Publication ───────────────────────────────────────────────────────────

class Publication(Base):
    __tablename__ = "publications"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    pub_type         = Column(SAEnum(PublicationTypeEnum))   # "journal" or "conference"
    title            = Column(Text)
    venue            = Column(String)    # journal name OR conference name
    issn             = Column(String)
    year             = Column(Integer)
    authors          = Column(Text)      # stored as comma-separated string
    authorship_role  = Column(SAEnum(AuthorshipRoleEnum))

    # Journal-specific
    wos_indexed      = Column(Boolean)
    scopus_indexed   = Column(Boolean)
    quartile         = Column(String)    # "Q1", "Q2", "Q3", "Q4"
    impact_factor    = Column(Float)

    # Conference-specific
    core_rank        = Column(String)    # "A*", "A", "B", "C"
    indexed_in       = Column(String)    # "IEEE", "Scopus", "ACM", "Springer"

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