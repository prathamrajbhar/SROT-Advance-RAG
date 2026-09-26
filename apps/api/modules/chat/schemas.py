import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from models.chat import Verdict


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = None


class ConversationUpdateRequest(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime


class ChatMessageRequest(BaseModel):
    content: str
    debug: bool = False


class CitationItem(BaseModel):
    index: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    locator: Optional[Dict[str, Any]] = None
    snippet: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content_md: str
    created_at: datetime
    verdict: Optional[Verdict] = None
    confidence: Optional[float] = None
    faithfulness: Optional[float] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    citations: Optional[List[CitationItem]] = None
