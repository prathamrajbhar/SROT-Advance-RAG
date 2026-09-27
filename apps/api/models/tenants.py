import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.documents import Document, DocumentChunk
    from models.jobs import ProcessingJob
    from models.providers import ProviderSetting
    from models.queries import QuerySession


class Tenant(Base, TimestampMixin):
    """Multi-tenant root organization entity."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)

    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )


class Workspace(Base):
    """Logical tenant workspace isolating documents and sessions."""

    __tablename__ = "workspaces"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="workspaces")
    provider_settings: Mapped[List["ProviderSetting"]] = relationship(
        "ProviderSetting",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    query_sessions: Mapped[List["QuerySession"]] = relationship(
        "QuerySession",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_workspaces_tenant_active", "tenant_id", "is_active"),
    )


class User(Base):
    """Authenticated user belonging to a tenant."""

    __tablename__ = "users"

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
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    query_sessions: Mapped[List["QuerySession"]] = relationship(
        "QuerySession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
