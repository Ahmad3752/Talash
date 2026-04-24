from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, Text, ForeignKey, Enum as SAEnum, DateTime, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum
from datetime import datetime

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

    # ── Score relationships ────────────────────────────────────────────────
    education_scores                = relationship("EducationScore",                back_populates="candidate", cascade="all, delete-orphan")
    research_scores                 = relationship("ResearchScore",                back_populates="candidate", cascade="all, delete-orphan")
    professional_experience_scores  = relationship("ProfessionalExperienceScore", back_populates="candidate", cascade="all, delete-orphan")
    skill_alignment_scores          = relationship("SkillAlignmentScore",         back_populates="candidate", cascade="all, delete-orphan")
    topic_variability_scores        = relationship("TopicVariabilityScore",       back_populates="candidate", cascade="all, delete-orphan")
    coauthor_analysis_scores        = relationship("CoauthorAnalysisScore",       back_populates="candidate", cascade="all, delete-orphan")

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

    # Journal-specific
    wos_indexed           = Column(Boolean)
    scopus_indexed        = Column(Boolean)
    quartile              = Column(String)
    impact_factor         = Column(Float)

    # Conference-specific
    core_rank             = Column(String)
    indexed_in            = Column(String)

    # CrossRef enriched fields
    doi                   = Column(String)
    publisher             = Column(String)
    journal_name          = Column(String)
    conference_name       = Column(String)
    conference_maturity   = Column(String)
    proceedings_publisher = Column(String)

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


# ═══════════════════════════════════════════════════════════════════════════
# SCORE TABLES
# ═══════════════════════════════════════════════════════════════════════════

class EducationScore(Base):
    """Module 3.1 — Education Analysis Score"""
    __tablename__ = "education_scores"

    id                          = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    degree_level_score          = Column(Float)   # /25
    overall_gpa_score           = Column(Float)   # /30
    institution_quality_score   = Column(Float)   # /20
    consistency_score           = Column(Float)   # /10
    continuity_score            = Column(Float)   # /10
    data_completeness_bonus     = Column(Float)   # /5

    raw_score                   = Column(Float)   # /100
    grade                       = Column(String)  # WEAK / SATISFACTORY / GOOD / EXCELLENT

    created_at                  = Column(DateTime, default=datetime.utcnow)
    reasons                     = Column(Text)    # JSON

    candidate = relationship("Candidate", back_populates="education_scores")


class ResearchScore(Base):
    """Module 3.2 — Research Profile Score"""
    __tablename__ = "research_scores"

    id                          = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    # ── Component scores ──────────────────────────────────────────────────
    publication_quality_score   = Column(Float)   # /35
    authorship_strength_score   = Column(Float)   # /20
    research_collaboration_score= Column(Float)   # /15
    conference_maturity_score   = Column(Float)   # /12
    patents_books_score         = Column(Float)   # /10
    supervision_record_score    = Column(Float)   # /8

    # ── Final ─────────────────────────────────────────────────────────────
    raw_score                   = Column(Float)   # /100
    grade                       = Column(String)  # WEAK / SATISFACTORY / GOOD / EXCELLENT

    # ── Counts (useful for final aggregation) ────────────────────────
    total_publications          = Column(Integer)
    total_journal_papers        = Column(Integer)
    total_conference_papers     = Column(Integer)
    total_books                 = Column(Integer)
    total_patents               = Column(Integer)
    total_supervised_students   = Column(Integer)

    # ── Metadata ─────────────────────────────────────────────────────────
    created_at                  = Column(DateTime, default=datetime.utcnow)
    reasons                     = Column(Text)    # JSON — one entry per component
    warnings                    = Column(Text)    # JSON list of warning strings
    recommendations             = Column(Text)    # JSON list of recommendation strings

    candidate = relationship("Candidate", back_populates="research_scores")


class ProfessionalExperienceScore(Base):
    """Module 3.8 — Professional Experience & Timeline Analysis Score"""
    __tablename__ = "professional_experience_scores"

    id                          = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    # ── Timeline Consistency Components ────────────────────────────────────
    gap_detection_score         = Column(Float)   # /8
    overlap_analysis_score      = Column(Float)   # /6
    gap_justification_score     = Column(Float)   # /6

    # ── Career Progression Components ─────────────────────────────────────
    role_seniority_score        = Column(Float)   # /10
    tenure_consistency_score    = Column(Float)   # /8
    domain_continuity_score     = Column(Float)   # /7

    # ── Data Quality Bonus ────────────────────────────────────────────────
    data_quality_bonus          = Column(Float)   # /15

    # ── Final Score ───────────────────────────────────────────────────────
    raw_score                   = Column(Float)   # /60
    grade                       = Column(String)  # WEAK / SATISFACTORY / GOOD / EXCELLENT

    # ── Timeline Analysis Details (JSON) ──────────────────────────────────
    gaps                        = Column(Text)    # JSON list of gap details
    job_overlaps                = Column(Text)    # JSON list of job overlap details
    edu_overlaps                = Column(Text)    # JSON list of education-job overlap details
    flags                       = Column(Text)    # JSON list of flag strings

    # ── Career Analysis Details (JSON) ────────────────────────────────────
    seniority_trajectory        = Column(Text)    # JSON list of trajectory entries
    seniority_trend             = Column(String)  # rising / flat / declining
    avg_tenure_months           = Column(Float)   # Average tenure across all jobs
    total_experience_months     = Column(Integer) # Total months of experience
    domain_continuity           = Column(String)  # strong / moderate / weak
    career_notes                = Column(Text)    # JSON list of career analysis notes

    # ── Metadata ──────────────────────────────────────────────────────────
    created_at                  = Column(DateTime, default=datetime.utcnow)
    reasons                     = Column(Text)    # JSON — one entry per component

    candidate = relationship("Candidate", back_populates="professional_experience_scores")


class SkillAlignmentScore(Base):
    """Module 3.9 — Skill Alignment Score"""
    __tablename__ = "skill_alignment_scores"

    id                          = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    # ── Applicability ─────────────────────────────────────────────────────
    applicable                  = Column(Boolean)  # True if explicit skills exist
    applicability_reason        = Column(Text)     # Reason why module was/wasn't scored

    # ── Component Scores ──────────────────────────────────────────────────
    skill_experience_score      = Column(Float)   # /18 — experience evidence
    skill_publication_score     = Column(Float)   # /12 — publication evidence
    skill_consistency_score     = Column(Float)   # /10 — consistency & diversity

    # ── Final Score ───────────────────────────────────────────────────────
    raw_score                   = Column(Float)   # /40
    grade                       = Column(String)  # WEAK / SATISFACTORY / GOOD / EXCELLENT

    # ── Skill Evidence Breakdown (JSON) ───────────────────────────────────
    skill_details               = Column(Text)    # JSON list of detailed skill analysis

    # ── Skill Count Summary ────────────────────────────────────────────────
    total_skills_evaluated      = Column(Integer) # Total explicit skills
    strong_count                = Column(Integer) # STRONG evidence count
    partial_count               = Column(Integer) # PARTIAL evidence count
    weak_count                  = Column(Integer) # WEAK evidence count
    unsupported_count           = Column(Integer) # UNSUPPORTED evidence count

    # ── Metadata ──────────────────────────────────────────────────────────
    created_at                  = Column(DateTime, default=datetime.utcnow)
    reasons                     = Column(Text)    # JSON — one entry per component

    candidate = relationship("Candidate", back_populates="skill_alignment_scores")


class TopicVariabilityScore(Base):
    """Module 3.6 — Topic Variability Analysis (INFORMATIONAL - not scored)"""
    __tablename__ = "topic_variability_scores"

    id                          = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    # ── Applicability ─────────────────────────────────────────────────────
    applicable                  = Column(Boolean)  # True if publications exist
    reason                      = Column(Text)     # Why analysis was/wasn't run

    # ── Core Analysis ─────────────────────────────────────────────────────
    dominant_theme              = Column(String)   # Name of largest theme cluster
    diversity_score             = Column(Float)    # 0.0 to 10.0 (0=mono-topic, 10=max breadth)
    focus_type                  = Column(String)   # 'deep_specialist' | 'broad_specialist' |
                                                   # 'generalist' | 'interdisciplinary'

    # ── Trend Analysis ────────────────────────────────────────────────────
    topic_trend                 = Column(String)   # 'stable' | 'shifting' | 'expanding' |
                                                   # 'insufficient_data'
    trend_explanation           = Column(Text)     # 1-sentence explanation

    # ── Overall Interpretation ────────────────────────────────────────────
    overall_interpretation      = Column(Text)     # 2-3 sentence evaluator summary

    # ── Theme Details (JSON) ──────────────────────────────────────────────
    themes                      = Column(Text)    # JSON list of theme clusters:
                                                   # [{theme_name, description, paper_count,
                                                   #   percentage, paper_ids}, ...]

    # ── Metadata ──────────────────────────────────────────────────────────
    total_publications          = Column(Integer) # Total publications analysed
    themes_identified           = Column(Integer) # Number of themes found
    id_coverage_ok              = Column(Boolean) # All pub IDs assigned to a theme
    missing_pub_ids             = Column(Text)    # JSON list of unassigned pub IDs
    extra_pub_ids               = Column(Text)    # JSON list of extra pub IDs

    created_at                  = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="topic_variability_scores")


class CoauthorAnalysisScore(Base):
    """Module 3.7 — Co-author Collaboration Analysis (INFORMATIONAL - not scored)"""
    __tablename__ = "coauthor_analysis_scores"

    id                          = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id                = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    # ── Applicability ─────────────────────────────────────────────────────
    applicable                  = Column(Boolean)  # True if publications exist
    reason                      = Column(Text)     # Why analysis was/wasn't run

    # ── Core Collaboration Counts ─────────────────────────────────────────
    unique_coauthors            = Column(Integer) # Total unique co-author count
    total_collaborations        = Column(Integer) # Papers with ≥1 co-author
    solo_papers                 = Column(Integer) # Papers with only candidate
    avg_authors_per_paper       = Column(Float)   # Mean author count per paper
    max_authors_in_one_paper    = Column(Integer) # Max authors in a single paper

    # ── Collaboration Patterns ────────────────────────────────────────────
    recurring_collaborators     = Column(Integer) # Co-authors in 2+ papers
    collaboration_style         = Column(String)  # 'solo_researcher' | 'small_team' |
                                                  # 'large_group' | 'mixed'
    network_diversity_score     = Column(Float)   # 0.0 to 10.0 (HHI-based diversity)
    collaboration_type          = Column(String)  # 'narrow_network' | 'moderate_network' |
                                                  # 'broad_network'

    # ── International Flag ────────────────────────────────────────────────
    international_flag          = Column(Boolean) # True if intl collaboration detected

    # ── Interpretation ───────────────────────────────────────────────────
    interpretation              = Column(Text)    # 2-3 sentence evaluator summary

    # ── Top Collaborators (JSON) ─────────────────────────────────────────
    top_collaborators           = Column(Text)    # JSON list of top 5 co-authors:
                                                  # [{name, count, papers}, ...]

    # ── Full Co-author Frequency Table (JSON) ───────────────────────────
    all_coauthor_freq           = Column(Text)    # JSON {coauthor_name: frequency, ...}

    # ── Metadata ──────────────────────────────────────────────────────────
    total_publications          = Column(Integer) # Total publications analysed
    candidate_name_used         = Column(String)  # Normalized candidate name
    parse_warnings              = Column(Text)    # JSON list of parsing warnings

    created_at                  = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="coauthor_analysis_scores")