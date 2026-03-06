"""Celery task: run PaddleOCR on an uploaded PDF document.

Flow:
  1. Load document record and user's PaddleOCR credentials from DB.
  2. Download raw file bytes from MinIO.
  3. Call OCRService.process() → markdown, sections, page_count.
  4. Update Document row (full_text, sections, page_count, ocr_markdown, parse_status).

Retry policy: up to 2 retries with exponential back-off on transient errors.
Soft time limit: 600 s (large PDFs can be slow).
Hard time limit: 660 s.
"""

from __future__ import annotations

import json as _json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any

from celery import Task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import decrypt_api_key
from app.tasks.celery_app import celery_app
from app.tasks.db import _get_session

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    queue="default",
    max_retries=2,
    soft_time_limit=600,
    time_limit=660,
    name="app.tasks.ocr_tasks.run_paddleocr_task",
)
def run_paddleocr_task(self: Task, document_id: str, user_id: str) -> dict[str, Any]:
    """Run PaddleOCR on a PDF document and update the Document record.

    Args:
        document_id: UUID of the Document to process.
        user_id:     UUID of the owning User (to fetch their OCR credentials).

    Returns:
        dict with keys: document_id, page_count, section_count.
    """
    logger.info(
        "run_paddleocr_task started | document_id=%s user_id=%s",
        document_id,
        user_id,
    )

    db: Session = _get_session()

    try:
        # ------------------------------------------------------------------
        # 1. Mark document as parsing
        # ------------------------------------------------------------------
        db.execute(
            text(
                "UPDATE documents SET parse_status = 'parsing', "
                "updated_at = :now WHERE id = :doc_id"
            ),
            {"now": datetime.now(UTC), "doc_id": document_id},
        )
        db.commit()

        # ------------------------------------------------------------------
        # 2. Load document record + user OCR credentials
        # ------------------------------------------------------------------
        doc_row = db.execute(
            text("SELECT storage_path, file_type FROM documents WHERE id = :doc_id"),
            {"doc_id": document_id},
        ).fetchone()

        if not doc_row:
            raise ValueError(f"Document not found: document_id={document_id}")

        storage_path = doc_row[0]

        user_row = db.execute(
            text(
                "SELECT paddleocr_server_url, paddleocr_token_enc "
                "FROM users WHERE id = :uid"
            ),
            {"uid": user_id},
        ).fetchone()

        if not user_row or not user_row[0] or not user_row[1]:
            raise ValueError(
                f"User {user_id} has no PaddleOCR credentials configured."
            )

        server_url: str = user_row[0]
        token: str = decrypt_api_key(user_row[1])

        # ------------------------------------------------------------------
        # 3. Download raw file from MinIO
        # ------------------------------------------------------------------
        from app.services.storage_service import StorageService

        storage = StorageService()
        file_bytes = storage.download_file(storage_path)
        logger.info(
            "Downloaded document from MinIO | storage_path=%s size=%d",
            storage_path,
            len(file_bytes),
        )

        # ------------------------------------------------------------------
        # 4. Call PaddleOCR
        # ------------------------------------------------------------------
        from app.services.ocr_service import OCRService

        ocr_service = OCRService()
        parse_result = ocr_service.process(file_bytes, server_url, token, file_type=0)

        full_text = parse_result.get("full_text", "")
        sections = parse_result.get("sections", [])
        page_count = parse_result.get("page_count")
        ocr_markdown = parse_result.get("ocr_markdown", "")

        logger.info(
            "OCR completed | document_id=%s sections=%d page_count=%s",
            document_id,
            len(sections),
            page_count,
        )

        # ------------------------------------------------------------------
        # 5. Persist results
        # ------------------------------------------------------------------
        now = datetime.now(UTC)
        db.execute(
            text(
                """
                UPDATE documents SET
                    full_text    = :full_text,
                    sections     = :sections,
                    page_count   = :page_count,
                    ocr_markdown = :ocr_markdown,
                    parse_status = 'completed',
                    parse_error  = NULL,
                    updated_at   = :now
                WHERE id = :doc_id
                """
            ),
            {
                "full_text": full_text,
                "sections": _json.dumps(sections, ensure_ascii=False),
                "page_count": page_count,
                "ocr_markdown": ocr_markdown,
                "now": now,
                "doc_id": document_id,
            },
        )
        db.commit()

        logger.info(
            "run_paddleocr_task completed | document_id=%s sections=%d",
            document_id,
            len(sections),
        )
        return {
            "document_id": document_id,
            "page_count": page_count,
            "section_count": len(sections),
        }

    except SoftTimeLimitExceeded:
        logger.error(
            "run_paddleocr_task soft time limit exceeded | document_id=%s",
            document_id,
        )
        raise

    except Exception as exc:
        logger.error(
            "run_paddleocr_task failed | document_id=%s\n%s",
            document_id,
            traceback.format_exc(),
        )
        try:
            db.execute(
                text(
                    "UPDATE documents SET parse_status = 'failed', "
                    "parse_error = :err, updated_at = :now WHERE id = :doc_id"
                ),
                {
                    "err": str(exc)[:2000],
                    "now": datetime.now(UTC),
                    "doc_id": document_id,
                },
            )
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        try:
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            raise

    finally:
        try:
            db.close()
        except Exception:
            pass
