"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.core.security import verify_token

settings = get_settings()

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

_AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session, closing it after the request."""
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Yield a Redis connection from the shared pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    yield _redis_pool


# ---------------------------------------------------------------------------
# Storage service
# ---------------------------------------------------------------------------


def get_storage_service():  # noqa: ANN201
    """Return a StorageService instance."""
    # Import here to avoid circular imports at module load time.
    from app.services.storage_service import StorageService  # noqa: PLC0415

    return StorageService()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode the bearer token and return the corresponding User record."""
    # Import here to avoid circular imports.
    from app.models.user import User  # noqa: PLC0415

    try:
        payload = verify_token(token)
    except JWTError as exc:
        raise UnauthorizedException("Invalid or expired token") from exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Token payload missing subject")

    from sqlalchemy import select  # noqa: PLC0415

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException("User not found")
    return user


def get_async_session_factory():
    """Return the async session factory for use outside of FastAPI dependency injection (e.g., SSE)."""
    return _AsyncSessionLocal


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """Return the current user only if their account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


async def get_current_admin_user(
    current_user=Depends(get_current_active_user),
):
    """Return the current user only if they are an active admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
