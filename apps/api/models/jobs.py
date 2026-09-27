import datetime
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

if TYPE_CHECKING:
    from models.documents import Document


class ProcessingJob(Base):
    """Background ingestion and indexing job tracked via Celery task ID."""

    __tablename__ = "processing_jobs"

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
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    celery_task_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(100), default="QUEUED", nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    document: Mapped["Document"] = relationship("Document", back_populates="jobs")

    __table_args__ = (
        Index("ix_processing_jobs_tenant_doc", "tenant_id", "document_id"),
    )
