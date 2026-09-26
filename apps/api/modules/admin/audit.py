import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.eval import AuditEvent
from models.project import ProjectRole
from modules.projects.service import verify_project_access


async def record_audit_event(
    db: AsyncSession,
    action: str,
    result: str = "success",
    actor_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
    object_type: Optional[str] = None,
    object_id: Optional[uuid.UUID] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor_id,
        project_id=project_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        ip=ip,
        user_agent=user_agent,
        result=result,
    )
    db.add(event)
    await db.commit()
    return event


async def list_project_audit_events(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[AuditEvent], int]:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.OWNER)
    offset = (page - 1) * page_size

    stmt = (
        select(AuditEvent)
        .where(AuditEvent.project_id == project_id)
        .order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    events = list((await db.execute(stmt)).scalars().all())

    count_stmt = select(func.count(AuditEvent.id)).where(AuditEvent.project_id == project_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    return events, total
