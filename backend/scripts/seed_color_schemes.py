"""
Seed script: insert preset color schemes into the color_schemes table.

Idempotent — skips rows that already exist (matched by name + type='preset').

Usage (from backend/ directory):
    python scripts/seed_color_schemes.py

Or inside Docker:
    docker compose exec backend python scripts/seed_color_schemes.py

Schema reference (from app/models/color_scheme.py):
    color_schemes:
        id          UUID PRIMARY KEY
        user_id     UUID nullable (null = system preset)
        name        TEXT NOT NULL
        type        TEXT NOT NULL  ('preset' | 'custom')
        colors      JSONB NOT NULL
        is_default  BOOLEAN NOT NULL DEFAULT FALSE
        created_at  TIMESTAMPTZ
        updated_at  TIMESTAMPTZ

Requires:
    - POSTGRES_* env vars (recommended), or DATABASE_URL / ASYNC_DATABASE_URL
    - sqlalchemy[asyncio] and asyncpg installed
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the backend package root is on sys.path when run as a script
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.prompts.color_schemes import (
    COLOR_SCHEME_DISPLAY_NAMES,
    PRESET_COLOR_SCHEMES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database URL resolution (async)
# ---------------------------------------------------------------------------

def _build_async_url() -> str:
    """
    Derive an async SQLAlchemy URL from the environment.

    Priority:
      1. ASYNC_DATABASE_URL (explicit override)
      2. DATABASE_URL (only if already concrete, i.e. no ${VAR} placeholders)
      3. Individual POSTGRES_* env vars (recommended; matches app config)
    """
    if url := os.environ.get("ASYNC_DATABASE_URL"):
        return url

    if url := os.environ.get("DATABASE_URL"):
        # If .env contains ${POSTGRES_USER} placeholders, Compose env_file will not expand them.
        # In that case, ignore DATABASE_URL and build from POSTGRES_* below.
        if "${" not in url:
            return url

    # Matches the vars set by docker-compose env_file and backend Settings()
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "afg_user")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    db = os.environ.get("POSTGRES_DB", "academic_figure_generator")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# ---------------------------------------------------------------------------
# Extra metadata per scheme (description, default flag)
# Stored in the DB for UI display only — not part of the colors dict.
# ---------------------------------------------------------------------------

SEED_METADATA: dict[str, dict] = {
    "okabe-ito": {
        "is_default": True,
        "description": (
            "Okabe-Ito (2008): designed for deuteranopia and protanopia. "
            "Recommended by Nature Methods. Default for CVPR / NeurIPS / Science."
        ),
    },
    "blue-monochrome": {
        "is_default": False,
        "description": (
            "Single-hue blue ramp; reproduces in grayscale. "
            "Ideal for module detail figures or print-only venues."
        ),
    },
    "warm-earth": {
        "is_default": False,
        "description": (
            "Warm reds and ambers for biology, ecology, and medical imaging papers."
        ),
    },
    "purple-green": {
        "is_default": False,
        "description": (
            "High-contrast complementary palette for IEEE papers and ablation grids."
        ),
    },
    "grayscale": {
        "is_default": False,
        "description": (
            "Full grayscale for venues that print without color. "
            "Fully accessible to all forms of color blindness."
        ),
    },
    "teal-coral": {
        "is_default": False,
        "description": (
            "Modern teal-coral complementary scheme popular in HCI/CHI papers."
        ),
    },
    "ml-topconf-tab10": {
        "is_default": False,
        "description": (
            "Top-ML-conference common palette based on Matplotlib Tab10 defaults "
            "(blue/orange/green)."
        ),
    },
    "ml-topconf-colorblind": {
        "is_default": False,
        "description": (
            "Top-ML-conference common Seaborn colorblind palette "
            "(accessible categorical contrast)."
        ),
    },
    "ml-topconf-deep": {
        "is_default": False,
        "description": (
            "Top-ML-conference common Seaborn deep palette "
            "(balanced contrast for ablation figures)."
        ),
    },
}


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

async def seed(session: AsyncSession) -> None:
    """Insert each preset color scheme into the color_schemes table (idempotent)."""
    now = datetime.now(UTC)
    inserted = 0
    skipped = 0

    for slug, colors in PRESET_COLOR_SCHEMES.items():
        display_name = COLOR_SCHEME_DISPLAY_NAMES.get(slug, slug)

        # Idempotency check: match on name + type
        existing = (await session.execute(
            text(
                "SELECT id FROM color_schemes "
                "WHERE name = :name AND type = 'preset' "
                "LIMIT 1"
            ),
            {"name": display_name},
        )).fetchone()

        if existing:
            logger.info("SKIP  %-45s (already exists, id=%s)", display_name, existing.id)
            skipped += 1
            continue

        meta = SEED_METADATA.get(slug, {})
        row_id = str(uuid.uuid4())

        await session.execute(
            text(
                """
                INSERT INTO color_schemes (
                    id,
                    user_id,
                    name,
                    type,
                    colors,
                    is_default,
                    created_at,
                    updated_at
                ) VALUES (
                    :id,
                    NULL,
                    :name,
                    'preset',
                    :colors,
                    :is_default,
                    :now,
                    :now
                )
                """
            ),
            {
                "id": row_id,
                "name": display_name,
                "colors": json.dumps(colors),
                "is_default": meta.get("is_default", False),
                "now": now,
            },
        )
        logger.info("INSERT %-45s (id=%s)", display_name, row_id)
        inserted += 1

    await session.commit()
    logger.info(
        "Seeding complete: %d inserted, %d skipped (already existed).",
        inserted, skipped,
    )


async def main() -> None:
    db_url = _build_async_url()
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
    logger.info("Connecting to database: ...@%s", safe_url)

    engine = create_async_engine(db_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(bind=engine, autoflush=False, autocommit=False)

    async with SessionLocal() as session:
        try:
            await seed(session)
        except Exception as exc:
            await session.rollback()
            logger.error("Seeding failed: %s", exc)
            raise
        finally:
            await session.close()

    await engine.dispose()
    logger.info("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        sys.exit(1)
