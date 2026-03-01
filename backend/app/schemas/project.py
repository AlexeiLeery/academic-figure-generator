from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    paper_field: str | None = None
    color_scheme: str = "okabe-ito"
    custom_colors: dict | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    paper_field: str | None = None
    color_scheme: str | None = None
    custom_colors: dict | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    paper_field: str | None
    color_scheme: str
    custom_colors: dict | None
    status: str
    created_at: datetime
    updated_at: datetime | None
    document_count: int = 0
    prompt_count: int = 0
    image_count: int = 0


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
