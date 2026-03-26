"""Database helpers — SQLite version."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


def get_sync_engine():
    """Get sync engine for scripts."""
    settings = get_settings()
    db_path = settings.DATABASE_PATH
    return create_engine(f"sqlite:///{db_path}")


def get_sync_session():
    """Get sync session factory for scripts."""
    engine = get_sync_engine()
    return sessionmaker(bind=engine)
