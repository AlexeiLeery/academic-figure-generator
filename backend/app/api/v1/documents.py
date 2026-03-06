"""Document upload and retrieval endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.dependencies import get_current_active_user, get_db, get_storage_service
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="", tags=["Documents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_owned_project(
    project_id: UUID, user: User, db: AsyncSession
) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project: Project | None = result.scalar_one_or_none()
    if project is None or project.status == "deleted":
        raise NotFoundException("Project not found")
    if project.user_id != user.id:
        raise ForbiddenException("Not your project")
    return project


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_project_documents(
    project_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for a project, newest first."""
    await _get_owned_project(project_id, user, db)

    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in documents]


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    project_id: UUID,
    file: UploadFile,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    storage=Depends(get_storage_service),
):
    """Upload a document to a project.

    Accepts PDF, DOCX, or TXT files up to 50 MB. The raw file is stored in
    MinIO and a Celery task is dispatched to parse it asynchronously.
    """
    project = await _get_owned_project(project_id, user, db)

    contents = await file.read()
    file_size = len(contents)
    original_filename = file.filename or "unnamed"

    # Validate file using extension + magic bytes (more robust than browser MIME).
    from app.services.document_service import DocumentService  # noqa: PLC0415

    doc_service = DocumentService()
    file_type = doc_service.validate_file(original_filename, contents, file_size)

    # Pick a reasonable content-type for object storage
    content_type_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }
    content_type = content_type_map.get(file_type, "application/octet-stream")

    # --- upload to MinIO ---
    storage_path = f"documents/{user.id}/{project.id}/{original_filename}"
    storage.upload_file(contents, storage_path, content_type)

    # --- create DB record ---
    document = Document(
        project_id=project.id,
        user_id=user.id,
        original_filename=original_filename,
        file_type=file_type,
        file_size_bytes=file_size,
        storage_path=storage_path,
        parse_status="pending",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # --- dispatch Celery parsing task ---
    celery_app.send_task(
        "app.tasks.prompt_tasks.parse_document_task",
        args=[str(document.id)],
        queue="default",
    )

    return DocumentResponse.model_validate(document)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a document with its parsed sections (verifies ownership)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document: Document | None = result.scalar_one_or_none()
    if document is None:
        raise NotFoundException("Document not found")
    if document.user_id != user.id:
        raise ForbiddenException("Not your document")

    return DocumentResponse.model_validate(document)


@router.post(
    "/projects/{project_id}/documents/{document_id}/ocr",
    response_model=DocumentResponse,
)
async def trigger_ocr(
    project_id: UUID,
    document_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger PaddleOCR re-parsing on an existing PDF document.

    Requires the user to have a PaddleOCR server URL and token configured
    in their settings.  Only supported for PDF files.  Returns the updated
    Document record (with parse_status='parsing').
    """
    await _get_owned_project(project_id, user, db)

    result = await db.execute(select(Document).where(Document.id == document_id))
    document: Document | None = result.scalar_one_or_none()
    if document is None:
        raise NotFoundException("Document not found")
    if document.user_id != user.id:
        raise ForbiddenException("Not your document")
    if document.file_type != "pdf":
        raise BadRequestException("OCR 仅支持 PDF 文件")
    if document.parse_status == "parsing":
        raise BadRequestException("文档正在解析中，请稍后再试")

    if not user.paddleocr_server_url or not user.paddleocr_token_enc:
        raise BadRequestException(
            "请先在「设置」页面配置 PaddleOCR Server URL 和 Access Token"
        )

    # Reset parse status to pending before dispatching
    document.parse_status = "parsing"
    document.parse_error = None
    db.add(document)
    await db.flush()
    await db.refresh(document)

    celery_app.send_task(
        "app.tasks.ocr_tasks.run_paddleocr_task",
        args=[str(document.id), str(user.id)],
        queue="default",
    )

    return DocumentResponse.model_validate(document)
