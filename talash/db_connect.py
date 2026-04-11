# db_connect.py — full file, replace everything in it

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_models import Base

DB_URL = "postgresql://talash:talash123@localhost:5432/talash_db"

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ All tables created")

def get_session():
    return SessionLocal()