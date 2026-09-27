import os
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.crypto import get_secret_vault
from models import Document, ProcessingJob, ProviderSetting, Tenant, User, Workspace
from modules.onboarding.schemas import (
    ProviderSettingsSaveRequest,
    WorkspaceSetupRequest,
)

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "../../sample_data")
SAMPLE_MANIFEST: List[Tuple[str, str, int]] = [
    ("sample_financials.xlsx", "tabular", 1024 * 12),
    ("sample_contract.pdf", "document", 1024 * 34),
    ("sample_tech_demo.mp4", "video", 1024 * 512),
    ("sample_audio_brief.mp3", "audio", 1024 * 128),
]


async def provision_workspace(
    request: WorkspaceSetupRequest,
    db: AsyncSession,
) -> Tuple[Tenant, Workspace, User]:
    """Provisions or fetches the tenant, creates workspace and admin user."""
    query = select(Tenant).where(Tenant.slug == request.tenant_slug)
    tenant = (await db.execute(query)).scalar_one_or_none()

    if tenant is None:
        tenant = Tenant(
            name=request.tenant_name,
            slug=request.tenant_slug,
            plan_tier="enterprise",
        )
        db.add(tenant)
        await db.flush()

    workspace = Workspace(
        tenant_id=tenant.id,
        name=request.workspace_name,
        description=request.description or "Default Enterprise Workspace",
        is_active=True,
    )
    db.add(workspace)
    await db.flush()

    user_query = select(User).where(User.email == request.admin_email)
    user = (await db.execute(user_query)).scalar_one_or_none()
    if user is None:
        user = User(
            tenant_id=tenant.id,
            email=request.admin_email,
            hashed_password="hashed_placeholder_auth",
            role="admin",
        )
        db.add(user)
        await db.flush()

    await db.commit()
    return tenant, workspace, user


async def save_encrypted_provider_settings(
    workspace: Workspace,
    request: ProviderSettingsSaveRequest,
    db: AsyncSession,
) -> Tuple[ProviderSetting, Optional[str]]:
    """Encrypts credentials with AES-256-GCM and persists them."""
    vault = get_secret_vault()
    if request.reranker_api_key:
        import json
        payload = json.dumps({"api_key": request.api_key or "", "reranker_api_key": request.reranker_api_key})
        encrypted_key = vault.encrypt_secret(payload)
    elif request.api_key:
        encrypted_key = vault.encrypt_secret(request.api_key)
    else:
        encrypted_key = None

    masked_key = vault.mask_secret(request.api_key) if request.api_key else None

    setting = ProviderSetting(
        tenant_id=workspace.tenant_id,
        workspace_id=workspace.id,
        provider_mode=request.provider_mode,
        encrypted_credentials=encrypted_key,
        default_llm_model=request.default_llm_model,
        default_embedding_model=request.default_embedding_model,
        default_reranker_model=request.default_reranker_model,
        base_url=request.base_url,
        is_verified=True,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting, masked_key


async def seed_sample_documents(
    workspace: Workspace,
    db: AsyncSession,
) -> List[uuid.UUID]:
    """Registers the multi-modal enterprise sample dataset for indexing."""
    created_document_ids: List[uuid.UUID] = []
    for filename, file_type, fallback_size in SAMPLE_MANIFEST:
        file_path = os.path.join(SAMPLE_DATA_DIR, filename)
        actual_size = os.path.getsize(file_path) if os.path.exists(file_path) else fallback_size
        s3_key = f"{workspace.tenant_id}/{workspace.id}/sample_data/{filename}"

        doc = Document(
            tenant_id=workspace.tenant_id,
            workspace_id=workspace.id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=actual_size,
            s3_raw_key=s3_key,
            status="UPLOADED",
            metadata_json={"sample_pack": True, "modality": file_type},
        )
        db.add(doc)
        await db.flush()
        created_document_ids.append(doc.id)

        job = ProcessingJob(
            tenant_id=workspace.tenant_id,
            document_id=doc.id,
            celery_task_id=f"sample-task-{uuid.uuid4()}",
            stage="QUEUED",
            progress_percent=0,
            status="PENDING",
        )
        db.add(job)

    await db.commit()
    return created_document_ids


async def check_onboarding_status(db: AsyncSession) -> dict:
    """Checks whether the system has completed onboarding."""
    stmt = (
        select(Workspace, Tenant, ProviderSetting)
        .join(Tenant, Workspace.tenant_id == Tenant.id)
        .outerjoin(ProviderSetting, Workspace.id == ProviderSetting.workspace_id)
        .order_by(Workspace.created_at.desc())
        .limit(1)
    )
    result = (await db.execute(stmt)).first()
    if not result:
        return {"is_onboarded": False}

    workspace, tenant, provider_setting = result
    is_onboarded = bool(provider_setting and provider_setting.is_verified)

    return {
        "is_onboarded": is_onboarded,
        "tenant_id": str(tenant.id) if tenant else None,
        "tenant_name": tenant.name if tenant else None,
        "workspace_id": str(workspace.id) if workspace else None,
        "workspace_name": workspace.name if workspace else None,
        "provider_mode": provider_setting.provider_mode if provider_setting else None,
        "default_llm_model": provider_setting.default_llm_model if provider_setting else None,
        "default_embedding_model": provider_setting.default_embedding_model if provider_setting else None,
        "default_reranker_model": provider_setting.default_reranker_model if provider_setting else None,
    }

