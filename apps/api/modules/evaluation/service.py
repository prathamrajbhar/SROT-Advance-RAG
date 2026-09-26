import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_settings
from models.eval import EvalRun
from models.project import ProjectRole
from modules.evaluation.evaluator import run_evaluation_on_golden_set
from modules.projects.service import verify_project_access

settings = get_settings()


def load_golden_set_fixtures() -> List[Dict[str, Any]]:
    eval_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "docs" / "eval"
    demo_file = eval_dir / "demo.yaml"
    if demo_file.exists():
        try:
            data = yaml.safe_load(demo_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "questions" in data:
                return data["questions"]
        except Exception:
            pass

    # Default fixture
    return [
        {"question": "What is the platform's core architecture?", "ground_truth": "Multimodal RAG with hybrid retrieval"},
        {"question": "What object storage is supported?", "ground_truth": "AWS S3 or LocalStack in dev"},
    ]


async def trigger_eval(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, notes: Optional[str] = None
) -> EvalRun:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.EDITOR)
    golden_items = load_golden_set_fixtures()

    eval_run = EvalRun(
        project_id=project_id,
        triggered_by=user_id,
        status="running",
        model_provider=settings.LLM_PROVIDER,
        model_name=settings.LLM_MODEL,
        question_count=len(golden_items),
    )
    db.add(eval_run)
    await db.commit()
    await db.refresh(eval_run)

    # Run evaluation
    metrics = await run_evaluation_on_golden_set(db, project_id, golden_items)
    eval_run.status = "completed"
    eval_run.faithfulness = metrics["faithfulness"]
    eval_run.context_precision = metrics["context_precision"]
    eval_run.context_recall = metrics["context_recall"]
    eval_run.answer_relevancy = metrics["answer_relevancy"]
    eval_run.report_json = metrics["report_json"]

    await db.commit()
    await db.refresh(eval_run)
    return eval_run


async def list_evals(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> List[EvalRun]:
    await verify_project_access(db, project_id, user_id)
    stmt = select(EvalRun).where(EvalRun.project_id == project_id).order_by(EvalRun.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_eval(
    db: AsyncSession, project_id: uuid.UUID, run_id: uuid.UUID, user_id: uuid.UUID
) -> EvalRun:
    await verify_project_access(db, project_id, user_id)
    stmt = select(EvalRun).where(EvalRun.id == run_id, EvalRun.project_id == project_id)
    run = (await db.execute(stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return run
