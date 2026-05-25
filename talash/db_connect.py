# db_connect.py — database connection and helpers

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .db_models import Base

# Load environment variables from .env file
# Find the .env file in the parent directory of the talash module
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Get DATABASE_URL from environment variables. Render and Supabase both use
# DATABASE_URL, while older local setups may still use SUPABASE_DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set. Check your Render environment variables.")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with SSL mode required for Supabase
# Append sslmode to the DATABASE_URL if not already present
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    Base.metadata.create_all(engine)
    print("All tables created")


def get_session():
    """Get a database session. Remember to close it when done."""
    return SessionLocal()


def get_db():
    """Dependency function for FastAPI routes to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
