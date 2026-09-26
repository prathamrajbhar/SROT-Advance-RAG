import uuid
from typing import Any, Dict, List
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.auth import User
from models.project import ProjectMember, ProjectRole
from modules.projects.schemas import MemberAddRequest
from modules.projects.service import verify_project_access


async def list_members(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> List[Dict[str, Any]]:
    await verify_project_access(db, project_id, user_id)
    stmt = (
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "user": {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
            },
            "role": m.role.value,
            "joined_at": m.created_at,
        }
        for m, u in rows
    ]


async def add_member(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, request: MemberAddRequest
) -> Dict[str, Any]:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.OWNER)

    user_stmt = select(User).where(User.email == request.email.lower())
    target_user = (await db.execute(user_stmt)).scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == target_user.id,
    )
    if (await db.execute(existing_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a project member")

    new_member = ProjectMember(
        project_id=project_id,
        user_id=target_user.id,
        role=request.role,
    )
    db.add(new_member)
    await db.commit()

    return {
        "user": {
            "id": target_user.id,
            "email": target_user.email,
            "full_name": target_user.full_name,
        },
        "role": request.role.value,
        "joined_at": new_member.created_at,
    }


async def remove_member(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, target_user_id: uuid.UUID
) -> None:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.OWNER)

    if user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove self from project ownership directly",
        )

    stmt = delete(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == target_user_id,
    )
    await db.execute(stmt)
    await db.commit()
