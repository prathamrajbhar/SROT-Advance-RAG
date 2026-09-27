import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.crypto import get_secret_vault
from models import Document, ProviderSetting, Workspace


@pytest.mark.asyncio
async def test_test_provider_endpoint(client: AsyncClient):
    # Test valid mock cloud key
    res = await client.post(
        "/api/v1/onboarding/test-provider",
        json={
            "provider_mode": "cloud",
            "provider_name": "gemini",
            "model": "gemini-2.0-flash",
            "api_key": "mock_valid_gemini_key",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["healthy"] is True
    assert data["latency_ms"] > 0
    assert data["resolved_model"] == "gemini-2.0-flash"

    # Test invalid / missing key
    err_res = await client.post(
        "/api/v1/onboarding/test-provider",
        json={
            "provider_mode": "cloud",
            "provider_name": "openai",
            "model": "gpt-4o",
            "api_key": None,
        },
    )
    assert err_res.status_code == 200
    assert err_res.json()["healthy"] is False


@pytest.mark.asyncio
async def test_onboarding_full_flow(client: AsyncClient, db_session: AsyncSession):
    slug = f"test-corp-{uuid.uuid4().hex[:6]}"
    # 1. Setup workspace
    ws_res = await client.post(
        "/api/v1/onboarding/workspace",
        json={
            "tenant_name": "Test Corporation",
            "tenant_slug": slug,
            "workspace_name": "Legal Intelligence",
            "admin_email": f"admin-{slug}@testcorp.com",
            "description": "Enterprise legal RAG workspace",
        },
    )
    assert ws_res.status_code == 200
    ws_data = ws_res.json()
    workspace_id = ws_data["workspace_id"]
    assert workspace_id is not None

    # 2. Save BYOK provider settings
    secret_key = "super_secret_production_api_key_xyz"
    prov_res = await client.post(
        "/api/v1/onboarding/provider-settings",
        json={
            "workspace_id": workspace_id,
            "provider_mode": "cloud",
            "provider_name": "openai",
            "api_key": secret_key,
            "default_llm_model": "gpt-4o",
            "default_embedding_model": "text-embedding-3-large",
            "default_reranker_model": "ms-marco-MiniLM-L-12-v2",
        },
    )
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert prov_data["masked_key"] == "••••••••_xyz"
    assert prov_data["is_verified"] is True
    assert prov_data["default_reranker_model"] == "ms-marco-MiniLM-L-12-v2"

    # 3. Verify in database: raw plaintext is NOT saved; AES-256 payload is saved and decryptable
    stmt = select(ProviderSetting).where(ProviderSetting.workspace_id == uuid.UUID(workspace_id))
    db_setting = (await db_session.execute(stmt)).scalar_one()
    assert db_setting.encrypted_credentials != secret_key
    assert db_setting.default_reranker_model == "ms-marco-MiniLM-L-12-v2"

    vault = get_secret_vault()
    decrypted_key = vault.decrypt_secret(db_setting.encrypted_credentials)
    assert decrypted_key == secret_key

    # 4. Seed enterprise sample dataset
    seed_res = await client.post(
        "/api/v1/onboarding/seed-sample-data",
        json={"workspace_id": workspace_id},
    )
    assert seed_res.status_code == 200
    seed_data = seed_res.json()
    assert seed_data["queued_jobs"] == 4
    assert len(seed_data["document_ids"]) == 4

    # 5. Verify documents exist in database
    docs_stmt = select(Document).where(Document.workspace_id == uuid.UUID(workspace_id))
    docs = (await db_session.execute(docs_stmt)).scalars().all()
    assert len(docs) == 4
    filenames = {d.filename for d in docs}
    assert "sample_financials.xlsx" in filenames
    assert "sample_contract.pdf" in filenames
