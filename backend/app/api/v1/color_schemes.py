"""Color scheme CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.dependencies import get_current_active_user, get_db
from app.models.color_scheme import ColorScheme
from app.models.user import User
from app.schemas.color_scheme import (
    ColorSchemeCreate,
    ColorSchemeResponse,
    ColorSchemeUpdate,
)

router = APIRouter(prefix="/color-schemes", tags=["Color Schemes"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_scheme(
    scheme_id: UUID, db: AsyncSession
) -> ColorScheme:
    result = await db.execute(select(ColorScheme).where(ColorScheme.id == scheme_id))
    scheme: ColorScheme | None = result.scalar_one_or_none()
    if scheme is None:
        raise NotFoundException("Color scheme not found")
    return scheme


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[ColorSchemeResponse])
async def list_color_schemes(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all color schemes visible to the current user.

    Returns system presets (user_id IS NULL) plus the user's own custom schemes.
    """
    result = await db.execute(
        select(ColorScheme)
        .where(
            or_(
                ColorScheme.user_id.is_(None),  # system presets
                ColorScheme.user_id == user.id,  # user's custom
            )
        )
        .order_by(ColorScheme.is_default.desc(), ColorScheme.name.asc())
    )
    schemes = result.scalars().all()
    return [ColorSchemeResponse.model_validate(s) for s in schemes]


@router.post("/", response_model=ColorSchemeResponse, status_code=201)
async def create_color_scheme(
    data: ColorSchemeCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom color scheme for the current user."""
    scheme = ColorScheme(
        user_id=user.id,
        name=data.name,
        type="custom",
        colors=data.colors.model_dump(),
        is_default=False,
    )
    db.add(scheme)
    await db.flush()
    await db.refresh(scheme)
    return ColorSchemeResponse.model_validate(scheme)


@router.put("/{scheme_id}", response_model=ColorSchemeResponse)
async def update_color_scheme(
    scheme_id: UUID,
    data: ColorSchemeUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom color scheme. System presets cannot be edited."""
    scheme = await _get_scheme(scheme_id, db)

    if scheme.type == "preset":
        raise BadRequestException("Cannot edit a system preset color scheme")
    if scheme.user_id != user.id:
        raise ForbiddenException("Not your color scheme")

    if data.name is not None:
        scheme.name = data.name
    if data.colors is not None:
        scheme.colors = data.colors.model_dump()

    db.add(scheme)
    await db.flush()
    await db.refresh(scheme)
    return ColorSchemeResponse.model_validate(scheme)


@router.delete("/{scheme_id}", status_code=204)
async def delete_color_scheme(
    scheme_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom color scheme. System presets cannot be deleted."""
    scheme = await _get_scheme(scheme_id, db)

    if scheme.type == "preset":
        raise BadRequestException("Cannot delete a system preset color scheme")
    if scheme.user_id != user.id:
        raise ForbiddenException("Not your color scheme")

    await db.delete(scheme)
    await db.flush()
