import uuid
from typing import Any, Dict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.chat import AssistantTurn, Conversation, Message, Verdict
from models.document import Document, IngestStatus
from modules.projects.service import verify_project_access


async def get_project_metrics(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> Dict[str, Any]:
    await verify_project_access(db, project_id, user_id)

    # 1. Chat Turns Aggregates
    turn_stats_stmt = (
        select(
            func.count(AssistantTurn.message_id).label("total_turns"),
            func.avg(AssistantTurn.latency_ms).label("avg_latency"),
            func.avg(AssistantTurn.faithfulness).label("avg_faithfulness"),
            func.sum(AssistantTurn.cost_usd).label("total_cost"),
        )
        .join(Message, AssistantTurn.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.project_id == project_id)
    )
    turn_stats = (await db.execute(turn_stats_stmt)).one()

    # 2. Verdict Distribution
    verdict_stmt = (
        select(AssistantTurn.verdict, func.count(AssistantTurn.message_id))
        .join(Message, AssistantTurn.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.project_id == project_id)
        .group_by(AssistantTurn.verdict)
    )
    verdict_rows = (await db.execute(verdict_stmt)).all()
    verdicts = {v.value if hasattr(v, "value") else str(v): count for v, count in verdict_rows}

    # 3. Ingestion stats
    doc_stats_stmt = (
        select(
            func.count(Document.id).label("total_docs"),
            func.count(Document.id).filter(Document.status == IngestStatus.FAILED).label("failed_docs"),
        )
        .where(Document.project_id == project_id)
    )
    doc_stats = (await db.execute(doc_stats_stmt)).one()

    return {
        "chat_volume": turn_stats.total_turns or 0,
        "avg_latency_ms": round(float(turn_stats.avg_latency or 0), 1),
        "avg_faithfulness": round(float(turn_stats.avg_faithfulness or 0.95), 2),
        "total_cost_usd": round(float(turn_stats.total_cost or 0), 5),
        "verdict_distribution": verdicts,
        "total_documents": doc_stats.total_docs or 0,
        "failed_documents": doc_stats.failed_docs or 0,
    }
