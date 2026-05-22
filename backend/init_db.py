"""Initialize PostgreSQL schema for OKR Tracker.

Usage:
  cd backend
  python init_db.py
"""

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from db import Base, engine

# Ensure .env is loaded when this script is run directly.
load_dotenv()


def init_schema() -> None:
    """Create all tables defined in models.py if they do not exist."""
    # Import models so SQLAlchemy metadata is fully registered before create_all.
    import models  # noqa: F401

    print("[init_db] Creating tables if missing...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    expected = {"objectives", "key_results", "agent_logs"}
    missing = expected - existing

    if missing:
        raise RuntimeError(f"Schema creation incomplete. Missing tables: {sorted(missing)}")

    print("[init_db] Schema ready. Tables:", ", ".join(sorted(existing)))


def smoke_test_connection() -> None:
    """Run a tiny query to verify DB connectivity and credentials."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[init_db] Connection test passed.")


if __name__ == "__main__":
    try:
        smoke_test_connection()
        init_schema()
    except SQLAlchemyError as exc:
        print("[init_db] Database error:", exc)
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001
        print("[init_db] Failed:", exc)
        raise SystemExit(1)
