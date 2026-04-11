# db_models.py  (create this as a separate file in your project)

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

Base = declarative_base()

# ── Enums ─────────────────────────────────────────────────────────────────

class AuthorshipRole(str, enum.Enum):
    first = "first"
    corresponding = "corresponding"
    first_and_corresponding = "first_and_corresponding"
    co_author = "co_author"

class PublicationType(str, enum.Enum):
    journal = "journal"
    conference = "conference"

class SupervisionLevel(str, enum.Enum):
    MS = "MS"
    PhD = "PhD"

class SupervisionRole(str, enum.Enum):
    main = "main"
    co_supervisor = "co_supervisor"

class BookRole(str, enum.Enum):
    sole = "sole"
    lead = "lead"
    co_author = "co_author"
    contributing = "contributing"

# ── Candidate (root table) ────────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(255), nullable=True)
    email      = Column(String(255), nullable=True, unique=True)
    phone      = Column(String(50),  nullable=True)
    source_pdf = Column(String(255), nullable=True)  # which file they came from

    # Relationships — all cascade delete so removing a candidate cleans everything
    education           = relationship("Education",         back_populates="candidate", cascade="all, delete-orphan")
    experience          = relationship("Experience",        back_populates="candidate", cascade="all, delete-orphan")
    skills              = relationship("Skill",             back_populates="candidate", cascade="all, delete-orphan")
    publications        = relationship("Publication",       back_populates="candidate", cascade="all, delete-orphan")
    books               = relationship("Book",              back_populates="candidate", cascade="all, delete-orphan")
    patents             = relationship("Patent",            back_populates="candidate", cascade="all, delete-orphan")
    supervised_students = relationship("SupervisedStudent", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate id={self.id} name={self.name}>"

# ── Education ─────────────────────────────────────────────────────────────

class Education(Base):
    __tablename__ = "education"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    degree       = Column(String(100), nullable=True)   # "PhD", "MS", "SSC" etc.
    field        = Column(String(255), nullable=True)
    institution  = Column(String(255), nullable=True)
    start_year   = Column(Integer,     nullable=True)
    end_year     = Column(Integer,     nullable=True)
    cgpa         = Column(Float,       nullable=True)
    cgpa_scale   = Column(Float,       nullable=True)
    percentage   = Column(Float,       nullable=True)
    board        = Column(String(255), nullable=True)   # SSC/HSSC only

    candidate = relationship("Candidate", back_populates="education")

# ── Experience ────────────────────────────────────────────────────────────

class Experience(Base):
    __tablename__ = "experience"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    company         = Column(String(255), nullable=True)
    role            = Column(String(255), nullable=True)
    employment_type = Column(String(100), nullable=True)
    start_date      = Column(String(7),   nullable=True)  # "YYYY-MM"
    end_date        = Column(String(7),   nullable=True)  # "YYYY-MM" or null = current
    description     = Column(Text,        nullable=True)

    candidate = relationship("Candidate", back_populates="experience")

# ── Skills ────────────────────────────────────────────────────────────────

class Skill(Base):
    __tablename__ = "skills"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    skill_name   = Column(String(255), nullable=False)

    candidate = relationship("Candidate", back_populates="skills")

# ── Publications (journals + conferences unified) ─────────────────────────

class Publication(Base):
    __tablename__ = "publications"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    type             = Column(SAEnum(PublicationType), nullable=False)
    title            = Column(Text,        nullable=True)
    venue            = Column(String(500), nullable=True)   # journal or conference name
    issn             = Column(String(20),  nullable=True)
    year             = Column(Integer,     nullable=True)
    authors          = Column(Text,        nullable=True)   # stored as comma-separated string
    authorship_role  = Column(SAEnum(AuthorshipRole), nullable=True)
    # journal-specific
    wos_indexed      = Column(Boolean,     nullable=True)
    scopus_indexed   = Column(Boolean,     nullable=True)
    quartile         = Column(String(2),   nullable=True)   # "Q1" "Q2" etc.
    impact_factor    = Column(Float,       nullable=True)
    # conference-specific
    core_rank        = Column(String(10),  nullable=True)   # "A*" "A" "B" "C"
    indexed_in       = Column(String(100), nullable=True)   # "IEEE" "Scopus" etc.

    candidate = relationship("Candidate", back_populates="publications")

# ── Books ─────────────────────────────────────────────────────────────────

class Book(Base):
    __tablename__ = "books"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    title            = Column(Text,        nullable=True)
    authors          = Column(Text,        nullable=True)
    isbn             = Column(String(30),  nullable=True)
    publisher        = Column(String(255), nullable=True)
    year             = Column(Integer,     nullable=True)
    url              = Column(Text,        nullable=True)
    authorship_role  = Column(SAEnum(BookRole), nullable=True)

    candidate = relationship("Candidate", back_populates="books")

# ── Patents ───────────────────────────────────────────────────────────────

class Patent(Base):
    __tablename__ = "patents"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id     = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    patent_number    = Column(String(100), nullable=True)
    title            = Column(Text,        nullable=True)
    year             = Column(Integer,     nullable=True)
    inventors        = Column(Text,        nullable=True)
    country          = Column(String(100), nullable=True)
    verification_url = Column(Text,        nullable=True)

    candidate = relationship("Candidate", back_populates="patents")

# ── Supervised Students ───────────────────────────────────────────────────

class SupervisedStudent(Base):
    __tablename__ = "supervised_students"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    student_name    = Column(String(255), nullable=True)
    level           = Column(SAEnum(SupervisionLevel), nullable=True)
    role            = Column(SAEnum(SupervisionRole),  nullable=True)
    graduation_year = Column(Integer, nullable=True)

    candidate = relationship("Candidate", back_populates="supervised_students")