from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .project import Project
    from .user import User


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    __table_args__ = (
        Index("ix_documents_project_id", "project_id"),
        Index("ix_documents_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="pdf/docx/txt",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    full_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sections: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Parsed chapter structure",
    )
    page_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    parse_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending/parsing/completed/failed",
    )
    parse_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    user: Mapped["User"] = relationship("User", back_populates="documents")
