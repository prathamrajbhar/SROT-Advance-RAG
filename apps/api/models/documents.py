import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import BigInteger, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.jobs import ProcessingJob
    from models.queries import QueryCitation
    from models.tenants import Workspace


class Document(Base, TimestampMixin):
    """Uploaded catalog document awaiting or completing ingestion."""

    __tablename__ = "documents"

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
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    s3_raw_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    s3_upload_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="UPLOADED", nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="documents")
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_documents_tenant_workspace", "tenant_id", "workspace_id"),
    )



class DocumentChunk(Base):
    """Hierarchical indexed chunk containing text, bounding box, or media timestamps."""

    __tablename__ = "document_chunks"

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
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    modality: Mapped[str] = mapped_column(String(50), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounding_box: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    s3_asset_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    parent_chunk: Mapped[Optional["DocumentChunk"]] = relationship(
        "DocumentChunk",
        remote_side=[id],
        back_populates="child_chunks",
    )
    child_chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="parent_chunk",
    )
    citations: Mapped[List["QueryCitation"]] = relationship(
        "QueryCitation",
        back_populates="chunk",
    )

    __table_args__ = (
        Index("ix_document_chunks_tenant_workspace", "tenant_id", "workspace_id"),
        Index("ix_document_chunks_document_index", "document_id", "chunk_index"),
    )
