import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.auth import User
from modules.admin.audit import list_project_audit_events
from modules.admin.metrics import get_project_metrics
from modules.auth.deps import get_current_user

router = APIRouter(tags=["Admin & Metrics"])


@router.get("/projects/{project_id}/metrics", response_model=Dict[str, Any])
async def get_metrics_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    return await get_project_metrics(db, project_id, user.id)


@router.get("/projects/{project_id}/audit", response_model=Dict[str, Any])
async def get_audit_endpoint(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    events, total = await list_project_audit_events(db, project_id, user.id, page, page_size)
    return {
        "items": [
            {
                "id": e.id,
                "action": e.action,
                "object_type": e.object_type,
                "object_id": e.object_id,
                "result": e.result,
                "created_at": e.created_at,
            }
            for e in events
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
