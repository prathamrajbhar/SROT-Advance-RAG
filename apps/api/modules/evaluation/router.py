import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.auth import User
from modules.auth.deps import get_current_user
from modules.evaluation.schemas import (
    EvalRunDetailResponse,
    EvalRunResponse,
    EvalTriggerRequest,
)
from modules.evaluation.service import get_eval, list_evals, trigger_eval

router = APIRouter(prefix="/projects/{project_id}/eval", tags=["Evaluation"])


@router.post("/run", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def trigger_eval_endpoint(
    project_id: uuid.UUID,
    request: EvalTriggerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    run = await trigger_eval(db, project_id, user.id, request.notes)
    return {"eval_run_id": run.id}


@router.get("/runs", response_model=Dict[str, Any])
async def list_evals_endpoint(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    runs = await list_evals(db, project_id, user.id)
    return {"items": [EvalRunResponse.model_validate(r) for r in runs]}


@router.get("/runs/{run_id}", response_model=EvalRunDetailResponse)
async def get_eval_endpoint(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvalRunDetailResponse:
    run = await get_eval(db, project_id, run_id, user.id)
    return EvalRunDetailResponse.model_validate(run)
