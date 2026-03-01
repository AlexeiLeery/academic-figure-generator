"""MinIO object storage service."""

from __future__ import annotations

import io
import logging
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.config import get_settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class StorageService:
    """Thin wrapper around the MinIO Python client for file upload / download."""

    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.MINIO_BUCKET_NAME
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL,
            )
            self.ensure_bucket()
        except AppException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("MinIO client initialization failed")
            raise AppException(
                status_code=503,
                detail=f"Object storage is unavailable: {type(exc).__name__}: {exc}",
                error_code="STORAGE_UNAVAILABLE",
            ) from exc

    # ------------------------------------------------------------------
    # Bucket management
    # ------------------------------------------------------------------

    def ensure_bucket(self) -> None:
        """Create the bucket if it does not already exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Created MinIO bucket: %s", self.bucket)
        except (S3Error, Exception) as exc:  # noqa: BLE001
            logger.exception("MinIO bucket check failed")
            raise AppException(
                status_code=503,
                detail=f"Object storage is unavailable: {type(exc).__name__}: {exc}",
                error_code="STORAGE_UNAVAILABLE",
            ) from exc

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to MinIO and return the object name (storage path).

        Parameters
        ----------
        file_data:
            Raw file bytes.
        object_name:
            The key / path under which to store the object, e.g.
            ``"documents/{user_id}/{uuid}.pdf"``.
        content_type:
            MIME type for the stored object.

        Returns
        -------
        str
            The object_name that was stored (can be used to retrieve later).
        """
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )
            logger.info(
                "Uploaded %s (%d bytes, %s)", object_name, len(file_data), content_type
            )
            return object_name
        except (S3Error, Exception) as exc:  # noqa: BLE001
            logger.exception("MinIO upload failed for %s", object_name)
            raise AppException(
                status_code=502,
                detail=f"Failed to upload file: {type(exc).__name__}: {exc}",
                error_code="STORAGE_UPLOAD_ERROR",
            ) from exc

    # ------------------------------------------------------------------
    # Pre-signed URL
    # ------------------------------------------------------------------

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """Generate a pre-signed GET URL for temporary download access.

        Parameters
        ----------
        object_name:
            The object key in MinIO.
        expires:
            URL validity in seconds (default 1 hour).

        Returns
        -------
        str
            The pre-signed URL.
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=expires),
            )
            return url
        except (S3Error, Exception) as exc:  # noqa: BLE001
            logger.exception("MinIO presign failed for %s", object_name)
            raise AppException(
                status_code=502,
                detail=f"Failed to generate download URL: {type(exc).__name__}: {exc}",
                error_code="STORAGE_PRESIGN_ERROR",
            ) from exc

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_file(self, object_name: str) -> bytes:
        """Download an object from MinIO and return its bytes."""
        response = None
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            return data
        except (S3Error, Exception) as exc:  # noqa: BLE001
            logger.exception("MinIO download failed for %s", object_name)
            raise AppException(
                status_code=502,
                detail=f"Failed to download file: {type(exc).__name__}: {exc}",
                error_code="STORAGE_DOWNLOAD_ERROR",
            ) from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_file(self, object_name: str) -> None:
        """Remove an object from MinIO."""
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info("Deleted %s", object_name)
        except (S3Error, Exception) as exc:  # noqa: BLE001
            logger.exception("MinIO delete failed for %s", object_name)
            raise AppException(
                status_code=502,
                detail=f"Failed to delete file: {type(exc).__name__}: {exc}",
                error_code="STORAGE_DELETE_ERROR",
            ) from exc

    # ------------------------------------------------------------------
    # Existence check
    # ------------------------------------------------------------------

    def file_exists(self, object_name: str) -> bool:
        """Check whether an object exists in the bucket."""
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except (S3Error, Exception):
            return False
