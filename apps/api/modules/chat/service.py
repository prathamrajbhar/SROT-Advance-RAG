import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.chat import AssistantTurn, Conversation, Message
from modules.projects.service import verify_project_access


async def create_conversation(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, title: Optional[str] = None
) -> Conversation:
    await verify_project_access(db, project_id, user_id)
    conv = Conversation(
        project_id=project_id,
        user_id=user_id,
        title=title or "New Conversation",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def list_conversations(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> List[Conversation]:
    await verify_project_access(db, project_id, user_id)
    stmt = (
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .order_by(Conversation.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def update_conversation(
    db: AsyncSession, conv_id: uuid.UUID, user_id: uuid.UUID, title: str
) -> Conversation:
    stmt = select(Conversation).where(Conversation.id == conv_id)
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await verify_project_access(db, conv.project_id, user_id)
    conv.title = title.strip()
    await db.commit()
    await db.refresh(conv)
    return conv


async def delete_conversation(
    db: AsyncSession, conv_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    stmt = select(Conversation).where(Conversation.id == conv_id)
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        return
    await verify_project_access(db, conv.project_id, user_id)
    await db.execute(delete(Conversation).where(Conversation.id == conv_id))
    await db.commit()


async def get_conversation_messages(
    db: AsyncSession, conv_id: uuid.UUID, user_id: uuid.UUID
) -> List[Dict[str, Any]]:
    conv = (await db.execute(select(Conversation).where(Conversation.id == conv_id))).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await verify_project_access(db, conv.project_id, user_id)

    stmt = (
        select(Message, AssistantTurn)
        .outerjoin(AssistantTurn, Message.id == AssistantTurn.message_id)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
    )
    rows = (await db.execute(stmt)).all()

    items = []
    for msg, turn in rows:
        item: Dict[str, Any] = {
            "id": msg.id,
            "role": msg.role,
            "content_md": msg.content_md,
            "created_at": msg.created_at,
        }
        if turn:
            item.update({
                "verdict": turn.verdict,
                "confidence": float(turn.confidence) if turn.confidence else None,
                "faithfulness": float(turn.faithfulness) if turn.faithfulness else None,
                "latency_ms": turn.latency_ms,
                "cost_usd": float(turn.cost_usd) if turn.cost_usd else None,
                "model_provider": turn.model_provider,
                "model_name": turn.model_name,
                "citations": turn.citations,
            })
        items.append(item)
    return items
