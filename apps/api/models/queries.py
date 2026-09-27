import datetime
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

if TYPE_CHECKING:
    from models.documents import Document, DocumentChunk
    from models.tenants import User, Workspace


class QuerySession(Base):
    """Analytical multi-turn chat session scoped to a tenant and workspace."""

    __tablename__ = "query_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="query_sessions")
    user: Mapped["User"] = relationship("User", back_populates="query_sessions")
    messages: Mapped[List["QueryMessage"]] = relationship(
        "QueryMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_query_sessions_tenant_workspace", "tenant_id", "workspace_id"),
    )


class QueryMessage(Base):
    """Individual prompt or AI response in a query session."""

    __tablename__ = "query_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sql_execution_trace: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["QuerySession"] = relationship("QuerySession", back_populates="messages")
    citations: Mapped[List["QueryCitation"]] = relationship(
        "QueryCitation",
        back_populates="message",
        cascade="all, delete-orphan",
    )


class QueryCitation(Base):
    """Grounded reference supporting an AI response with bounding boxes or timestamps."""

    __tablename__ = "query_citations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("query_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    message: Mapped["QueryMessage"] = relationship("QueryMessage", back_populates="citations")
    chunk: Mapped[Optional["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="citations",
    )
    document: Mapped["Document"] = relationship("Document")
