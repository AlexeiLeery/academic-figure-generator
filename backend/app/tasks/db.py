"""Shared synchronous database helpers for Celery tasks.

Both prompt_tasks and image_tasks import from here to avoid
duplicate connection pools and DRY violations.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _build_sync_db_url() -> str:
    """
    Construct a synchronous PostgreSQL URL for use in Celery workers.

    Priority:
      1. SYNC_DATABASE_URL env var (explicit override, e.g. for testing)
      2. DATABASE_URL env var with asyncpg driver swapped to plain psycopg2
      3. Individual POSTGRES_* env vars (matches docker-compose / .env.example)
    """
    if url := os.environ.get("SYNC_DATABASE_URL"):
        return url
    if url := os.environ.get("DATABASE_URL"):
        # If the value includes ${VAR} placeholders (common in .env files),
        # it won't be expanded inside Docker env_file; ignore and build from
        # explicit POSTGRES_* vars instead.
        if "${" not in url:
            return (
                url
                .replace("postgresql+asyncpg://", "postgresql+psycopg://")
                .replace("postgresql+psycopg2://", "postgresql+psycopg://")
                .replace("postgresql://", "postgresql+psycopg://")
            )
    # Fall back to assembling from individual vars (always present in Docker)
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "afg_user")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    db = os.environ.get("POSTGRES_DB", "academic_figure_generator")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


_SYNC_DATABASE_URL: str = _build_sync_db_url()

_engine = None
_SessionLocal = None


def _get_session() -> Session:
    """Lazy-init sync SQLAlchemy session factory (shared singleton)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            _SYNC_DATABASE_URL,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _SessionLocal()
