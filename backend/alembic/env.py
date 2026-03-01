"""Alembic environment configuration with async SQLAlchemy support."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Alembic Config object (provides access to values in alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import all models so that their metadata is populated for autogenerate.
# ---------------------------------------------------------------------------
# The wildcard imports below intentionally pull every model into scope so
# Alembic can detect schema changes automatically.
from app.models import *  # noqa: F401, F403, E402
from app.models.base import Base  # noqa: E402  – adjust if Base lives elsewhere

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from app settings
# ---------------------------------------------------------------------------
from app.config import get_settings  # noqa: E402

_settings = get_settings()
config.set_main_option("sqlalchemy.url", _settings.DATABASE_URL)


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL (no engine / DBAPI connection).
    Useful for generating SQL scripts without a live database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within an async context."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
