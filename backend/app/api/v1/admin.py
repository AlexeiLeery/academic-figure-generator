"""Admin endpoints: system settings management."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_api_key
from app.dependencies import get_current_admin_user, get_db
from app.models.system_settings import SystemSettings
from app.schemas.system_settings import SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_create_settings(db: AsyncSession) -> SystemSettings:
    """Return the single SystemSettings row, creating it if absent."""
    result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = SystemSettings(id=1)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return settings


def _settings_to_response(s: SystemSettings) -> SystemSettingsResponse:
    return SystemSettingsResponse(
        claude_api_key_set=s.claude_api_key_enc is not None,
        claude_api_base_url=s.claude_api_base_url,
        claude_model=s.claude_model,
        nanobanana_api_key_set=s.nanobanana_api_key_enc is not None,
        nanobanana_api_base_url=s.nanobanana_api_base_url,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/settings", response_model=SystemSettingsResponse)
async def get_system_settings(
    _admin=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current system-wide API settings (admin only)."""
    settings = await _get_or_create_settings(db)
    return _settings_to_response(settings)


@router.put("/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    data: SystemSettingsUpdate,
    _admin=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update system-wide API settings (admin only)."""
    settings = await _get_or_create_settings(db)
    updates = data.model_dump(exclude_unset=True)

    # Handle API key encryption separately
    if "claude_api_key" in updates:
        raw_key = updates.pop("claude_api_key")
        if raw_key:
            settings.claude_api_key_enc = encrypt_api_key(raw_key)
        else:
            settings.claude_api_key_enc = None

    if "nanobanana_api_key" in updates:
        raw_key = updates.pop("nanobanana_api_key")
        if raw_key:
            settings.nanobanana_api_key_enc = encrypt_api_key(raw_key)
        else:
            settings.nanobanana_api_key_enc = None

    # Apply remaining scalar updates (base URLs, model)
    for field, value in updates.items():
        setattr(settings, field, value)

    db.add(settings)
    await db.flush()
    await db.refresh(settings)
    return _settings_to_response(settings)
