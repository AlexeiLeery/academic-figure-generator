"""Security utilities: JWT, password hashing, API key encryption."""

import base64
import os
from datetime import UTC, datetime, timedelta

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
import bcrypt

from app.config import get_settings


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def _jwt_secret() -> str:
    return get_settings().get_jwt_secret()


def _algorithm() -> str:
    return get_settings().JWT_ALGORITHM


def create_access_token(data: dict) -> str:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, _jwt_secret(), algorithm=_algorithm())


def create_refresh_token(data: dict) -> str:
    """Create a long-lived JWT refresh token."""
    settings = get_settings()
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(payload, _jwt_secret(), algorithm=_algorithm())


def verify_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Returns the decoded payload dict.
    Raises jose.JWTError on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_algorithm()])
    except JWTError:
        raise
    return payload


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# API key encryption  (AES-256-GCM)
# ---------------------------------------------------------------------------


def _get_aes_key() -> bytes:
    """Derive a 32-byte AES key from the master key setting.

    The master key is expected to be a base64-encoded 32-byte value.
    If it is not valid base64 it is zero-padded / truncated to 32 bytes.
    """
    raw = get_settings().ENCRYPTION_MASTER_KEY
    try:
        key = base64.b64decode(raw)
    except Exception:
        key = raw.encode()
    # Ensure exactly 32 bytes
    if len(key) < 32:
        key = key.ljust(32, b"\x00")
    return key[:32]


def encrypt_api_key(key: str) -> str:
    """Encrypt an API key using AES-256-GCM.

    Returns a base64-encoded string of the form:
        base64(nonce [12 bytes] + ciphertext_with_tag)
    """
    aesgcm = AESGCM(_get_aes_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, key.encode(), None)
    blob = nonce + ciphertext
    return base64.b64encode(blob).decode()


def decrypt_api_key(encrypted: str) -> str:
    """Decrypt an AES-256-GCM encrypted API key.

    Expects the base64-encoded string produced by ``encrypt_api_key``.
    Raises ValueError if decryption fails.
    """
    try:
        blob = base64.b64decode(encrypted)
        nonce, ciphertext = blob[:12], blob[12:]
        aesgcm = AESGCM(_get_aes_key())
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except (InvalidTag, Exception) as exc:
        raise ValueError("API key decryption failed") from exc


# ---------------------------------------------------------------------------
# Key masking
# ---------------------------------------------------------------------------


def mask_api_key(key: str) -> str:
    """Return a masked representation like 'sk-xxxx****'.

    Shows up to the first 7 characters then masks the rest.
    """
    if not key:
        return "****"
    visible = key[:7]
    return f"{visible}****"
