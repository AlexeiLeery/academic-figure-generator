"""Add PaddleOCR fields to users table.

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-03-06
"""

from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "paddleocr_server_url",
            sa.String(length=500),
            nullable=True,
            comment="User-configured PaddleOCR server URL",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "paddleocr_token_enc",
            sa.Text,
            nullable=True,
            comment="AES-256 encrypted PaddleOCR access token",
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "ocr_markdown",
            sa.Text,
            nullable=True,
            comment="Raw OCR Markdown output from PaddleOCR",
        ),
    )


def downgrade() -> None:
    op.drop_column("documents", "ocr_markdown")
    op.drop_column("users", "paddleocr_token_enc")
    op.drop_column("users", "paddleocr_server_url")
