"""Local filesystem storage service — replaces MinIO."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Local filesystem-based storage for uploads and generated figures."""

    def __init__(self) -> None:
        settings = get_settings()
        self.data_dir = Path(settings.DATA_DIR)
        self.uploads_dir = self.data_dir / "uploads"
        self.figures_dir = self.data_dir / "figures"

        # Ensure directories exist
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, relative_path: str, data: bytes) -> str:
        """Save uploaded file bytes to uploads directory.

        Returns the relative path from data_dir.
        """
        target = self.uploads_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        logger.info("Saved upload: %s (%d bytes)", target, len(data))
        return f"uploads/{relative_path}"

    def save_figure(self, relative_path: str, data: bytes) -> str:
        """Save generated figure bytes to figures directory.

        Returns the relative path from data_dir.
        """
        target = self.figures_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        logger.info("Saved figure: %s (%d bytes)", target, len(data))
        return f"figures/{relative_path}"

    def get_file(self, storage_path: str) -> bytes:
        """Read file bytes from storage path (relative to data_dir)."""
        target = self.data_dir / storage_path
        if not target.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        return target.read_bytes()

    def get_file_path(self, storage_path: str) -> Path:
        """Get absolute path for a storage path."""
        return self.data_dir / storage_path

    def delete_file(self, storage_path: str) -> None:
        """Delete a file from storage."""
        target = self.data_dir / storage_path
        if target.exists():
            target.unlink()
            logger.info("Deleted: %s", target)

    def file_exists(self, storage_path: str) -> bool:
        """Check if a file exists in storage."""
        return (self.data_dir / storage_path).exists()
