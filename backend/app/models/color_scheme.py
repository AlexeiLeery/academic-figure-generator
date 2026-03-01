from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class ColorScheme(Base, TimestampMixin):
    __tablename__ = "color_schemes"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        comment="null = system preset",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="preset/custom",
    )
    colors: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment=(
            "Keys: primary, secondary, tertiary, text, fill, "
            "section_bg, border, arrow"
        ),
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
