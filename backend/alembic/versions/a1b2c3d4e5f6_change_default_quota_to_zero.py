"""Change default quota values to 0 for new users.

Revision ID: a1b2c3d4e5f6
Revises: 5e5d8670cbfe
Create Date: 2026-03-01 21:50:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "5e5d8670cbfe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change default values for new user quotas to 0
    op.alter_column(
        "users",
        "nanobanana_images_quota",
        server_default="0",
    )
    op.alter_column(
        "users",
        "claude_tokens_quota",
        server_default="0",
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "nanobanana_images_quota",
        server_default="100",
    )
    op.alter_column(
        "users",
        "claude_tokens_quota",
        server_default="1000000",
    )
