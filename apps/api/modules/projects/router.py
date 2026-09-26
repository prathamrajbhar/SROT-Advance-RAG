import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.auth import User
from models.project import ProjectRole
from modules.auth.deps import get_current_user
from modules.projects.members import add_member, list_members, remove_member
from modules.projects.schemas import (
    MemberAddRequest,
    MemberResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from modules.projects.service import (
    create_project,
    delete_project,
    get_project_detail,
    list_user_projects,
    update_project,
    verify_project_access,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=Dict[str, Any])
async def list_projects_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    items, total = await list_user_projects(db, user.id, page, page_size)
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_project_endpoint(
    request: ProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    proj = await create_project(db, user.id, request)
    return {"id": proj.id, "name": proj.name, "created_at": proj.created_at}


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailResponse:
    detail = await get_project_detail(db, project_id, user.id)
    return ProjectDetailResponse.model_validate(detail)


@router.patch("/{project_id}", response_model=ProjectDetailResponse)
async def update_project_endpoint(
    project_id: uuid.UUID,
    request: ProjectUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailResponse:
    await update_project(db, project_id, user.id, request)
    detail = await get_project_detail(db, project_id, user.id)
    return ProjectDetailResponse.model_validate(detail)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await delete_project(db, project_id, user.id)


@router.get("/{project_id}/members", response_model=List[MemberResponse])
async def list_members_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MemberResponse]:
    members = await list_members(db, project_id, user.id)
    return [MemberResponse.model_validate(m) for m in members]


@router.post("/{project_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member_endpoint(
    project_id: uuid.UUID,
    request: MemberAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    result = await add_member(db, project_id, user.id, request)
    return MemberResponse.model_validate(result)


@router.delete("/{project_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    project_id: uuid.UUID,
    target_user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await remove_member(db, project_id, user.id, target_user_id)
