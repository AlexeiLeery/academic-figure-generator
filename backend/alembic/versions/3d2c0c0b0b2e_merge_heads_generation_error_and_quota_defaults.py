"""Merge heads: generation_error + quota defaults.

Revision ID: 3d2c0c0b0b2e
Revises: 0b7f1f2dd6a6, a1b2c3d4e5f6
Create Date: 2026-03-01
"""

# Alembic identifiers
revision = "3d2c0c0b0b2e"
down_revision = ("0b7f1f2dd6a6", "a1b2c3d4e5f6")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge revision: no-op
    pass


def downgrade() -> None:
    # Merge revision: no-op
    pass

