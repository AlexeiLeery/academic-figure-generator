"""Project CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies import get_current_active_user, get_db
from app.models.document import Document
from app.models.image import Image
from app.models.project import Project
from app.models.prompt import Prompt
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_owned_project(
    project_id: UUID,
    user: User,
    db: AsyncSession,
) -> Project:
    """Fetch a project and verify ownership. Raises on not-found / forbidden."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project: Project | None = result.scalar_one_or_none()
    if project is None or project.status == "deleted":
        raise NotFoundException("Project not found")
    if project.user_id != user.id:
        raise ForbiddenException("Not your project")
    return project


async def _enrich_response(project: Project, db: AsyncSession) -> ProjectResponse:
    """Build ProjectResponse with aggregate counts."""
    doc_count = (
        await db.execute(
            select(func.count()).select_from(Document).where(Document.project_id == project.id)
        )
    ).scalar_one()

    prompt_count = (
        await db.execute(
            select(func.count()).select_from(Prompt).where(Prompt.project_id == project.id)
        )
    ).scalar_one()

    image_count = (
        await db.execute(
            select(func.count()).select_from(Image).where(Image.project_id == project.id)
        )
    ).scalar_one()

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        paper_field=project.paper_field,
        color_scheme=project.color_scheme,
        custom_colors=project.custom_colors,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        document_count=doc_count,
        prompt_count=prompt_count,
        image_count=image_count,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(
        user_id=user.id,
        name=data.name,
        description=data.description,
        paper_field=data.paper_field,
        color_scheme=data.color_scheme,
        custom_colors=data.custom_colors,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return await _enrich_response(project, db)


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Filter by status (active/archived)"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's projects with pagination."""
    base_query = select(Project).where(
        Project.user_id == user.id,
        Project.status != "deleted",
    )

    if status is not None:
        base_query = base_query.where(Project.status == status)

    # Total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total: int = (await db.execute(count_query)).scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    rows_query = base_query.order_by(Project.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(rows_query)
    projects = result.scalars().all()

    items = [await _enrich_response(p, db) for p in projects]
    return ProjectListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project detail (verifies ownership)."""
    project = await _get_owned_project(project_id, user, db)
    return await _enrich_response(project, db)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project's metadata (verifies ownership)."""
    project = await _get_owned_project(project_id, user, db)

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.paper_field is not None:
        project.paper_field = data.paper_field
    if data.color_scheme is not None:
        project.color_scheme = data.color_scheme
    if data.custom_colors is not None:
        project.custom_colors = data.custom_colors
    if data.status is not None:
        project.status = data.status

    db.add(project)
    await db.flush()
    await db.refresh(project)
    return await _enrich_response(project, db)


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a project by setting status to 'deleted'."""
    project = await _get_owned_project(project_id, user, db)
    project.status = "deleted"
    db.add(project)
    await db.flush()
    return MessageResponse(message="Project deleted")
