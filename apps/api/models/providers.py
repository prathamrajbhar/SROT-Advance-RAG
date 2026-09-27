import datetime
import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

if TYPE_CHECKING:
    from models.tenants import Tenant, Workspace


class ProviderSetting(Base):
    """Encrypted BYOK model provider credentials and default models."""

    __tablename__ = "provider_settings"

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
    provider_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    default_embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    default_reranker_model: Mapped[str] = mapped_column(String(100), default="ms-marco-MiniLM-L-12-v2", nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_tested_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="provider_settings")

    __table_args__ = (
        Index("ix_provider_settings_tenant_workspace", "tenant_id", "workspace_id"),
    )
