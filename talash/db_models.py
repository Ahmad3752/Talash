from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, Text, ForeignKey, Enum as SAEnum, DateTime, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum
from datetime import datetime

Base = declarative_base()

#  Enums 

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

#  Candidate 

class Candidate(Base):
    __tablename__ = "candidates"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(String, unique=True, nullable=False)
    name            = Column(String)
    email           = Column(String)
    phone           = Column(String)

    #  Data relationships 
    education           = relationship("Education",         back_populates="candidate", cascade="all, delete-orphan")
    experience          = relationship("Experience",        back_populates="candidate", cascade="all, delete-orphan")
    skills              = relationship("Skill",             back_populates="candidate", cascade="all, delete-orphan")
    publications        = relationship("Publication",       back_populates="candidate", cascade="all, delete-orphan")
    books               = relationship("Book",              back_populates="candidate", cascade="all, delete-orphan")
    patents             = relationship("Patent",            back_populates="candidate", cascade="all, delete-orphan")
    supervised_students = relationship("SupervisedStudent", back_populates="candidate", cascade="all, delete-orphan")

    #  Score relationships 
    education_scores               = relationship("EducationScore",               back_populates="candidate", cascade="all, delete-orphan")
    research_scores                = relationship("ResearchScore",                back_populates="candidate", cascade="all, delete-orphan")
    professional_experience_scores = relationship("ProfessionalExperienceScore",  back_populates="candidate", cascade="all, delete-orphan")
    skill_alignment_scores         = relationship("SkillAlignmentScore",          back_populates="candidate", cascade="all, delete-orphan")
    topic_variability_scores       = relationship("TopicVariabilityScore",        back_populates="candidate", cascade="all, delete-orphan")
    coauthor_analysis_scores       = relationship("CoauthorAnalysisScore",        back_populates="candidate", cascade="all, delete-orphan")

    #  Summary relationship (uselist=False  one-to-one) 
    cv_summary = relationship(
        "CVSummary",
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', candidate_id='{self.candidate_id}')>"


#  Education 

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

    def __repr__(self):
        return f"<Education(degree='{self.degree}', institution='{self.institution}')>"


#  Experience 

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

    def __repr__(self):
        return f"<Experience(company='{self.company}', role='{self.role}')>"


#  Skill 

class Skill(Base):
    __tablename__ = "skills"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    skill_name   = Column(String)
    inferred     = Column(Boolean, default=False)

    candidate = relationship("Candidate", back_populates="skills")

    def __repr__(self):
        return f"<Skill(name='{self.skill_name}', inferred={self.inferred})>"


#  Publication 

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

    wos_indexed           = Column(Boolean)
    scopus_indexed        = Column(Boolean)
    quartile              = Column(String)
    impact_factor         = Column(Float)

    core_rank             = Column(String)
    indexed_in            = Column(String)

    doi                   = Column(String)
    publisher             = Column(String)
    journal_name          = Column(String)
    conference_name       = Column(String)
    conference_maturity   = Column(String)
    proceedings_publisher = Column(String)

    candidate = relationship("Candidate", back_populates="publications")

    def __repr__(self):
        return f"<Publication(title='{self.title[:30]}...', year={self.year})>"


#  Book 

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

    def __repr__(self):
        return f"<Book(title='{self.title}', year={self.year})>"


#  Patent 

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

    def __repr__(self):
        return f"<Patent(patent_number='{self.patent_number}', year={self.year})>"


#  SupervisedStudent 

class SupervisedStudent(Base):
    __tablename__ = "supervised_students"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id    = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    student_name    = Column(String)
    level           = Column(SAEnum(SupervisionLevelEnum))
    role            = Column(SAEnum(SupervisionRoleEnum))
    graduation_year = Column(Integer)

    candidate = relationship("Candidate", back_populates="supervised_students")

    def __repr__(self):
        return f"<SupervisedStudent(name='{self.student_name}', level={self.level})>"


# 
# SCORE TABLES
# 

class EducationScore(Base):
    """Module 3.1  Education Analysis Score"""
    __tablename__ = "education_scores"

    id                        = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id              = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    degree_level_score        = Column(Float)   # /25
    overall_gpa_score         = Column(Float)   # /30
    institution_quality_score = Column(Float)   # /20
    consistency_score         = Column(Float)   # /10
    continuity_score          = Column(Float)   # /10
    data_completeness_bonus   = Column(Float)   # /5

    raw_score                 = Column(Float)   # /100
    grade                     = Column(String)  # WEAK / AVERAGE / GOOD / EXCELLENT

    created_at                = Column(DateTime, default=datetime.utcnow)
    reasons                   = Column(Text)    # JSON

    candidate = relationship("Candidate", back_populates="education_scores")


class ResearchScore(Base):
    """Module 3.2-3.7  Research Profile Score"""
    __tablename__ = "research_scores"

    id                           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                 = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    publication_quality_score    = Column(Float)   # /35
    authorship_strength_score    = Column(Float)   # /20
    research_collaboration_score = Column(Float)   # /15
    conference_maturity_score    = Column(Float)   # /12
    patents_books_score          = Column(Float)   # /10
    supervision_record_score     = Column(Float)   # /8

    raw_score                    = Column(Float)   # /100
    grade                        = Column(String)  # WEAK / MODERATE / STRONG

    total_publications           = Column(Integer)
    total_journal_papers         = Column(Integer)
    total_conference_papers      = Column(Integer)
    total_books                  = Column(Integer)
    total_patents                = Column(Integer)
    total_supervised_students    = Column(Integer)

    created_at                   = Column(DateTime, default=datetime.utcnow)
    reasons                      = Column(Text)    # JSON
    warnings                     = Column(Text)    # JSON list
    recommendations              = Column(Text)    # JSON list

    candidate = relationship("Candidate", back_populates="research_scores")


class ProfessionalExperienceScore(Base):
    """Module 3.8  Professional Experience & Timeline Analysis Score"""
    __tablename__ = "professional_experience_scores"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id          = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    gap_detection_score   = Column(Float)   # /8
    overlap_analysis_score= Column(Float)   # /6
    gap_justification_score=Column(Float)   # /6
    role_seniority_score  = Column(Float)   # /10
    tenure_consistency_score=Column(Float)  # /8
    domain_continuity_score=Column(Float)   # /7
    data_quality_bonus    = Column(Float)   # /15

    raw_score             = Column(Float)   # /60
    grade                 = Column(String)  # WEAK / SATISFACTORY / EXCELLENT

    gaps                  = Column(Text)    # JSON
    job_overlaps          = Column(Text)    # JSON
    edu_overlaps          = Column(Text)    # JSON
    flags                 = Column(Text)    # JSON

    seniority_trajectory  = Column(Text)    # JSON
    seniority_trend       = Column(String)
    avg_tenure_months     = Column(Float)
    total_experience_months=Column(Integer)
    domain_continuity     = Column(String)
    career_notes          = Column(Text)    # JSON

    created_at            = Column(DateTime, default=datetime.utcnow)
    reasons               = Column(Text)    # JSON

    candidate = relationship("Candidate", back_populates="professional_experience_scores")


class SkillAlignmentScore(Base):
    """Module 3.9  Skill Alignment Score"""
    __tablename__ = "skill_alignment_scores"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id            = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    applicable              = Column(Boolean)
    applicability_reason    = Column(Text)

    skill_experience_score  = Column(Float)   # /18
    skill_publication_score = Column(Float)   # /12
    skill_consistency_score = Column(Float)   # /10

    raw_score               = Column(Float)   # /40
    grade                   = Column(String)

    skill_details           = Column(Text)    # JSON

    total_skills_evaluated  = Column(Integer)
    strong_count            = Column(Integer)
    partial_count           = Column(Integer)
    weak_count              = Column(Integer)
    unsupported_count       = Column(Integer)

    created_at              = Column(DateTime, default=datetime.utcnow)
    reasons                 = Column(Text)    # JSON

    candidate = relationship("Candidate", back_populates="skill_alignment_scores")


class TopicVariabilityScore(Base):
    """Module 3.6  Topic Variability Analysis"""
    __tablename__ = "topic_variability_scores"

    id                     = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id           = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    applicable             = Column(Boolean)
    reason                 = Column(Text)

    dominant_theme         = Column(String)
    diversity_score        = Column(Float)    # 0.010.0
    focus_type             = Column(String)

    topic_trend            = Column(String)
    trend_explanation      = Column(Text)
    overall_interpretation = Column(Text)

    themes                 = Column(Text)     # JSON

    total_publications     = Column(Integer)
    themes_identified      = Column(Integer)
    id_coverage_ok         = Column(Boolean)
    missing_pub_ids        = Column(Text)     # JSON
    extra_pub_ids          = Column(Text)     # JSON

    created_at             = Column(DateTime, default=datetime.utcnow)
    reasons                = Column(Text)    # JSON

    candidate = relationship("Candidate", back_populates="topic_variability_scores")


class CoauthorAnalysisScore(Base):
    """Module 3.7  Co-author Collaboration Analysis"""
    __tablename__ = "coauthor_analysis_scores"

    id                       = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id             = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    applicable               = Column(Boolean)
    reason                   = Column(Text)

    unique_coauthors         = Column(Integer)
    total_collaborations     = Column(Integer)
    solo_papers              = Column(Integer)
    avg_authors_per_paper    = Column(Float)
    max_authors_in_one_paper = Column(Integer)

    recurring_collaborators  = Column(Integer)
    collaboration_style      = Column(String)
    network_diversity_score  = Column(Float)    # 0.010.0
    collaboration_type       = Column(String)

    international_flag       = Column(Boolean)
    interpretation           = Column(Text)

    top_collaborators        = Column(Text)     # JSON
    all_coauthor_freq        = Column(Text)     # JSON

    total_publications       = Column(Integer)
    candidate_name_used      = Column(String)
    parse_warnings           = Column(Text)     # JSON

    created_at               = Column(DateTime, default=datetime.utcnow)
    reasons                  = Column(Text)    # JSON

    candidate = relationship("Candidate", back_populates="coauthor_analysis_scores")


# 
# COMPREHENSIVE SUMMARY TABLE
# 

class CVSummary(Base):
    """
    Comprehensive CV Evaluation Summary  Final output of the summarizers node.

    Weighted overall score:
      - Module 3.1  Education                        25%
      - Module 3.2-3.7  Research                     35%
      - Module 3.8-3.9  Experience & Skills          20%
      - Module 3.6-3.7  Topic Variability & Collab   10%
    """
    __tablename__ = "cv_summaries"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id   = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True)

    #  Overall 
    overall_score  = Column(Float)    # 0100
    overall_grade  = Column(String)   # EXCELLENT / GOOD / SATISFACTORY / WEAK
    overall_status = Column(String)   #  /  /  / 

    #  Per-module quick reference 
    education_score  = Column(Float)
    education_grade  = Column(String)

    research_score   = Column(Float)
    research_grade   = Column(String)

    experience_score = Column(Float)
    experience_grade = Column(String)

    tvs_score        = Column(Float)
    tvs_grade        = Column(String)

    #  Full JSON dump 
    summary_data   = Column(Text)     # complete summary dict as JSON
    reasons        = Column(Text)     # General summary reasons

    #  Metadata 
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #  Relationship back to Candidate (matches uselist=False on that side) 
    candidate = relationship("Candidate", back_populates="cv_summary")

    def __repr__(self):
        return f"<CVSummary(candidate_id={self.candidate_id}, overall_score={self.overall_score})>"
