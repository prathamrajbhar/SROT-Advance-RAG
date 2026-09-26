import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from core.qdrant import delete_project_collection, ensure_project_collection
from core.s3 import delete_s3_prefix
from models.auth import User
from models.document import Chunk, Document, IngestStatus
from models.project import Project, ProjectMember, ProjectRole
from modules.projects.schemas import ProjectCreateRequest, ProjectUpdateRequest


async def verify_project_access(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, min_role: Optional[ProjectRole] = None
) -> ProjectMember:
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
    )
    membership = (await db.execute(stmt)).scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your scope",
        )
    if min_role:
        role_hierarchy = {ProjectRole.VIEWER: 1, ProjectRole.EDITOR: 2, ProjectRole.OWNER: 3}
        if role_hierarchy[membership.role] < role_hierarchy[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {min_role.value}",
            )
    return membership


async def create_project(
    db: AsyncSession, user_id: uuid.UUID, request: ProjectCreateRequest
) -> Project:
    project = Project(
        owner_id=user_id,
        name=request.name,
        description=request.description,
    )
    db.add(project)
    await db.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=user_id,
        role=ProjectRole.OWNER,
    )
    db.add(member)
    await db.commit()
    await db.refresh(project)

    await ensure_project_collection(str(project.id))
    return project


async def list_user_projects(
    db: AsyncSession, user_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    offset = (page - 1) * page_size
    stmt = (
        select(Project, ProjectMember.role)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(ProjectMember.user_id == user_id)
        .offset(offset)
        .limit(page_size)
    )
    results = (await db.execute(stmt)).all()

    count_stmt = (
        select(func.count(ProjectMember.project_id))
        .where(ProjectMember.user_id == user_id)
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    items = []
    for proj, role in results:
        doc_count_stmt = select(func.count(Document.id)).where(Document.project_id == proj.id)
        doc_count = (await db.execute(doc_count_stmt)).scalar() or 0
        items.append({
            "id": proj.id,
            "name": proj.name,
            "description": proj.description,
            "role": role.value,
            "document_count": doc_count,
            "updated_at": proj.updated_at,
        })
    return items, total


async def get_project_detail(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> Dict[str, Any]:
    await verify_project_access(db, project_id, user_id)
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs_stmt = select(
        func.count(Document.id).label("total"),
        func.count(Document.id).filter(Document.status == IngestStatus.INDEXED).label("indexed"),
        func.count(Document.id).filter(Document.status == IngestStatus.FAILED).label("failed"),
        func.max(Document.indexed_at).label("last_indexed"),
    ).where(Document.project_id == project_id)
    doc_stats = (await db.execute(docs_stmt)).one()

    chunks_stmt = select(func.count(Chunk.id)).where(Chunk.project_id == project_id)
    total_chunks = (await db.execute(chunks_stmt)).scalar() or 0

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "document_count": doc_stats.total or 0,
        "indexed_count": doc_stats.indexed or 0,
        "failed_count": doc_stats.failed or 0,
        "total_chunks": total_chunks,
        "last_indexed_at": doc_stats.last_indexed,
    }


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, request: ProjectUpdateRequest
) -> Project:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.EDITOR)
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.name is not None and request.name.strip():
        project.name = request.name.strip()
    if request.description is not None:
        project.description = request.description.strip()

    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.OWNER)
    await delete_project_collection(str(project_id))
    await delete_s3_prefix(f"projects/{project_id}/")

    stmt = delete(Project).where(Project.id == project_id)
    await db.execute(stmt)
    await db.commit()
