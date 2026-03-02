"""Add NanoBanana model setting.

Revision ID: 9a4d2f3c1b10
Revises: 7c1a9d2f4b21
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa


revision = "9a4d2f3c1b10"
down_revision = "7c1a9d2f4b21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column(
            "nanobanana_model",
            sa.String(length=100),
            nullable=False,
            server_default="gemini-3-pro-image-preview",
        ),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "nanobanana_model")

