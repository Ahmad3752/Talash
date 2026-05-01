"""
db_connect.py — Database connection and initialization.

IMPORTANT: init_db() must be called AFTER all models are imported so that
Base.metadata.create_all() can see every table.  Call it explicitly from
main.py after all model imports, not at module load time here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env BEFORE reading any env vars
# Look for .env in parent directory (project root) since we run uvicorn from talash/ subdirectory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://talash:talash123@localhost:5432/talash_db"
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def init_db():
    """
    Create all tables.  Must be called AFTER every model module has been
    imported so SQLAlchemy's metadata registry is complete.
    """
    from db_models import (                                        # noqa: F401
        Base as ModelBase,
        Candidate, Education, Experience, Skill,
        Publication, Book, Patent, SupervisedStudent,
        EducationScore, ResearchScore, ProfessionalExperienceScore,
        SkillAlignmentScore, TopicVariabilityScore, CoauthorAnalysisScore,
        CVSummary,
    )

    try:
        ModelBase.metadata.create_all(bind=engine, checkfirst=True)
        # Quick sanity-check: verify the candidates table exists
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM candidates LIMIT 1"))
        print("[db] ✅ Database initialised — all tables present")
    except Exception as e:
        print(f"[db] ❌ Failed to create tables: {e}")
        raise


def get_session():
    """Return a new SQLAlchemy session.  Caller is responsible for closing it."""
    return SessionLocal()