from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .document import Document
    from .image import Image
    from .prompt import Prompt
    from .user import User


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    paper_field: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="e.g. 'computer vision', 'NLP'",
    )
    color_scheme: Mapped[str] = mapped_column(
        String(50),
        default="okabe-ito",
        nullable=False,
    )
    custom_colors: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        comment="active/archived/deleted",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="project", cascade="all, delete-orphan"
    )
    prompts: Mapped[list["Prompt"]] = relationship(
        "Prompt", back_populates="project", cascade="all, delete-orphan"
    )
    images: Mapped[list["Image"]] = relationship(
        "Image", back_populates="project", cascade="all, delete-orphan"
    )
