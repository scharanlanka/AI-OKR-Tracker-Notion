import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Always load the root .env file explicitly (repo/.env), even when running from backend/.
ROOT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ROOT_ENV_PATH)

# Default works with docker-compose service name.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5433/okr_tracker",
)
# Optional compatibility fallback if user has POSTGRES_URI from other projects.
if not os.getenv("DATABASE_URL") and os.getenv("POSTGRES_URI"):
    DATABASE_URL = os.getenv("POSTGRES_URI")

# If driver is omitted (postgresql://...), default it to psycopg (v3).
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
