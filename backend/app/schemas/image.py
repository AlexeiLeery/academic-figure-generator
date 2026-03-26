from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageGenerateRequest(BaseModel):
    resolution: str = "2K"
    aspect_ratio: str = "16:9"
    color_scheme: str | None = None


class ImageDirectGenerateRequest(BaseModel):
    prompt: str
    resolution: str = "2K"
    aspect_ratio: str = "16:9"
    color_scheme: str = "okabe-ito"
    project_id: str | None = None


class ImageEditRequest(BaseModel):
    edit_instruction: str
    resolution: str = "2K"


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prompt_id: str | None
    project_id: str | None
    resolution: str
    aspect_ratio: str
    color_scheme: str | None
    storage_path: str | None
    file_size_bytes: int | None
    width_px: int | None
    height_px: int | None
    generation_status: str
    generation_duration_ms: int | None
    generation_error: str | None
    retry_count: int
    download_url: str | None = None
    created_at: datetime


class ImageStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    generation_status: str
    generation_error: str | None = None
