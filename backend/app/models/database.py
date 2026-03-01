"""Database session management.

The canonical async engine and session factory are in app.dependencies.
This module re-exports for convenience.
"""
# For Alembic and other tools that need sync access
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings


def get_sync_engine():
    """Get sync engine for Alembic migrations and scripts."""
    settings = get_settings()
    return create_engine(settings.DATABASE_URL_SYNC)


def get_sync_session():
    """Get sync session factory for scripts."""
    engine = get_sync_engine()
    return sessionmaker(bind=engine)
