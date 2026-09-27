import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import (
    Document,
    DocumentChunk,
    ProcessingJob,
    ProviderSetting,
    QueryCitation,
    QueryMessage,
    QuerySession,
    Tenant,
    User,
    Workspace,
)


@pytest.mark.asyncio
async def test_full_domain_models_lifecycle(db_session: AsyncSession) -> None:
    # 1. Create Tenant
    tenant_slug = f"acme-{uuid.uuid4().hex[:8]}"
    tenant = Tenant(
        name="Acme Corp",
        slug=tenant_slug,
        plan_tier="enterprise",
    )
    db_session.add(tenant)
    await db_session.flush()
    assert tenant.id is not None
    assert tenant.created_at is not None

    # 2. Create Workspace
    workspace = Workspace(
        tenant_id=tenant.id,
        name="Legal AI Research",
        description="Workspace for analyzing enterprise contracts",
        is_active=True,
    )
    db_session.add(workspace)
    await db_session.flush()
    assert workspace.id is not None

    # 3. Create User
    user = User(
        tenant_id=tenant.id,
        email=f"admin-{uuid.uuid4().hex[:6]}@acme.com",
        hashed_password="hashed_secure_pass_123",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None

    # 4. Create ProviderSetting
    provider_setting = ProviderSetting(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        provider_mode="cloud",
        encrypted_credentials="enc_payload_vault_123",
        default_llm_model="gemini-2.0-flash",
        default_embedding_model="text-embedding-3-large",
        is_verified=True,
    )
    db_session.add(provider_setting)
    await db_session.flush()
    assert provider_setting.id is not None

    # 5. Create Document
    document = Document(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        filename="master_service_agreement.pdf",
        file_type="pdf",
        file_size_bytes=1048576,
        s3_raw_key=f"{tenant.id}/{workspace.id}/msa.pdf",
        status="UPLOADED",
        metadata_json={"pages": 12, "author": "Legal Team"},
    )
    db_session.add(document)
    await db_session.flush()
    assert document.id is not None

    # 6. Create DocumentChunk with bounding box
    bbox_payload = {
        "ymin": 0.1250,
        "xmin": 0.0500,
        "ymax": 0.3500,
        "xmax": 0.9500,
        "page_width": 612.0,
        "page_height": 792.0,
    }
    chunk = DocumentChunk(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        document_id=document.id,
        chunk_index=0,
        modality="document",
        text_content="Section 4.1 Indemnification terms and liabilities...",
        page_number=1,
        bounding_box=bbox_payload,
        metadata_json={"token_count": 48},
    )
    db_session.add(chunk)
    await db_session.flush()
    assert chunk.id is not None

    # 7. Create ProcessingJob
    job = ProcessingJob(
        tenant_id=tenant.id,
        document_id=document.id,
        celery_task_id=f"task-{uuid.uuid4()}",
        stage="CHUNKING",
        progress_percent=50,
        status="PROCESSING",
    )
    db_session.add(job)
    await db_session.flush()
    assert job.id is not None

    # 8. Create QuerySession, Message, and Citation
    query_session = QuerySession(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        user_id=user.id,
        title="Contract Indemnity Analysis",
    )
    db_session.add(query_session)
    await db_session.flush()

    message = QueryMessage(
        session_id=query_session.id,
        role="assistant",
        content="According to Section 4.1, the indemnification liability is capped...",
        latency_ms=210,
        tokens_used=180,
    )
    db_session.add(message)
    await db_session.flush()

    citation = QueryCitation(
        message_id=message.id,
        chunk_id=chunk.id,
        document_id=document.id,
        citation_type="document",
        relevance_score=0.945,
        page_number=1,
        bounding_box=bbox_payload,
    )
    db_session.add(citation)
    await db_session.flush()
    assert citation.id is not None

    # Verify query and relationship resolution
    query = select(Document).where(Document.id == document.id)
    retrieved_doc = (await db_session.execute(query)).scalar_one()
    assert retrieved_doc.filename == "master_service_agreement.pdf"
    assert retrieved_doc.metadata_json["pages"] == 12
