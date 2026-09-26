import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.auth import User
from modules.auth.deps import get_current_user
from modules.chat.schemas import (
    ChatMessageRequest,
    ConversationCreateRequest,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageResponse,
)
from modules.chat.service import (
    create_conversation,
    delete_conversation,
    get_conversation_messages,
    list_conversations,
    update_conversation,
)
from modules.chat.stream_service import stream_chat_response

router = APIRouter(tags=["Chat"])


@router.get("/projects/{project_id}/conversations", response_model=List[ConversationResponse])
async def list_project_conversations(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConversationResponse]:
    convs = await list_conversations(db, project_id, user.id)
    return [ConversationResponse.model_validate(c) for c in convs]


@router.post("/projects/{project_id}/conversations", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    project_id: uuid.UUID,
    request: ConversationCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    conv = await create_conversation(db, project_id, user.id, request.title)
    return {"id": conv.id}


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation_endpoint(
    conversation_id: uuid.UUID,
    request: ConversationUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    conv = await update_conversation(db, conversation_id, user.id, request.title)
    return ConversationResponse.model_validate(conv)


@router.get("/conversations/{conversation_id}/messages", response_model=Dict[str, Any])
async def get_messages_endpoint(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    items = await get_conversation_messages(db, conversation_id, user.id)
    return {"items": items}


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_endpoint(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await delete_conversation(db, conversation_id, user.id)


@router.post("/conversations/{conversation_id}/messages")
async def send_chat_message(
    conversation_id: uuid.UUID,
    request: ChatMessageRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    generator = stream_chat_response(
        conversation_id=conversation_id,
        user_id=user.id,
        query_text=request.content,
        debug=request.debug,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
