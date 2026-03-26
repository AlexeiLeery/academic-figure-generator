"""API v1 router registry — personal-use (no auth/admin/payment/usage)."""

from app.api.v1.color_schemes import router as color_schemes_router
from app.api.v1.documents import router as documents_router
from app.api.v1.images import router as images_router
from app.api.v1.projects import router as projects_router
from app.api.v1.prompts import router as prompts_router

__all__ = [
    "color_schemes_router",
    "documents_router",
    "images_router",
    "projects_router",
    "prompts_router",
]
