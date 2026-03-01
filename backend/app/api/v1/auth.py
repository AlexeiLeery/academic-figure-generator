"""Authentication endpoints: register, login, refresh, profile."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    encrypt_api_key,
    hash_password,
    verify_password,
    verify_token,
)
from app.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_to_response(user: User) -> UserResponse:
    """Map a User ORM object to UserResponse, computing derived fields."""
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        default_color_scheme=user.default_color_scheme,
        default_resolution=user.default_resolution,
        default_aspect_ratio=user.default_aspect_ratio,
        claude_api_key_set=user.claude_api_key_enc is not None,
        nanobanana_api_key_set=user.nanobanana_api_key_enc is not None,
        claude_api_base_url=user.claude_api_base_url,
        nanobanana_api_base_url=user.nanobanana_api_base_url,
        claude_tokens_quota=user.claude_tokens_quota,
        nanobanana_images_quota=user.nanobanana_images_quota,
        created_at=user.created_at,
    )


def _build_tokens(user_id: str) -> tuple[str, str]:
    """Create an access + refresh token pair for the given user id."""
    data = {"sub": str(user_id)}
    return create_access_token(data), create_refresh_token(data)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check for existing email
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise BadRequestException("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return _user_to_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email + password and receive JWT tokens."""
    result = await db.execute(select(User).where(User.email == data.email))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        raise BadRequestException("Invalid email or password")

    if not user.is_active:
        raise BadRequestException("Account is deactivated")

    access, refresh = _build_tokens(user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new token pair."""
    try:
        payload = verify_token(data.refresh_token)
    except Exception as exc:
        raise BadRequestException("Invalid or expired refresh token") from exc

    if payload.get("type") != "refresh":
        raise BadRequestException("Token is not a refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise BadRequestException("Invalid token payload")

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise NotFoundException("User not found")
    if not user.is_active:
        raise BadRequestException("Account is deactivated")

    access, new_refresh = _build_tokens(user.id)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_active_user),
):
    """Return the current authenticated user's profile."""
    return _user_to_response(user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile and preferences."""
    updates = data.model_dump(exclude_unset=True)

    # Handle API key encryption separately
    if "claude_api_key" in updates:
        raw_key = updates.pop("claude_api_key")
        if raw_key:
            user.claude_api_key_enc = encrypt_api_key(raw_key)
        else:
            user.claude_api_key_enc = None

    if "nanobanana_api_key" in updates:
        raw_key = updates.pop("nanobanana_api_key")
        if raw_key:
            user.nanobanana_api_key_enc = encrypt_api_key(raw_key)
        else:
            user.nanobanana_api_key_enc = None

    # Apply remaining scalar updates
    for field, value in updates.items():
        setattr(user, field, value)

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return _user_to_response(user)
