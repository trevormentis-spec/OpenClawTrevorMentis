"""TPS Database Engine — SQLAlchemy 2.x with PostgreSQL primary, SQLite fallback.

Connection string set via DATABASE_URL env var:
- PostgreSQL: DATABASE_URL=postgresql://user:pass@host/dbname
- SQLite (default): sqlite:///data/tps.db
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

TPS_ROOT = Path(__file__).resolve().parent.parent
TREVOR_ROOT = TPS_ROOT.parent
DEFAULT_SQLITE_PATH = TREVOR_ROOT / "data" / "tps.db"


def get_database_url() -> str:
    """Return database URL. PostgreSQL if DATABASE_URL is set, else SQLite."""
    pg_url = os.environ.get("DATABASE_URL", "")
    if pg_url:
        # Handle Heroku-style postgres:// → postgresql://
        if pg_url.startswith("postgres://"):
            pg_url = pg_url.replace("postgres://", "postgresql://", 1)
        return pg_url
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            # Ensure data directory exists for SQLite
            DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(url, connect_args=connect_args, echo=False)
    return _engine


def get_session() -> Session:
    """Get a new database session."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory()


def init_db() -> None:
    """Create all tables if they don't exist.

    For quick setup without running Alembic migrations.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)


def reset_db() -> None:
    """Drop and recreate all tables. USE WITH CAUTION."""
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
