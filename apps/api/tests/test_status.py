import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_onboarding_status_empty_db(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/onboarding/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_onboarded" in data


@pytest.mark.asyncio
async def test_onboarding_status_after_flow(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        setup_payload = {
            "tenant_name": "Acme Status Test",
            "tenant_slug": "acme-status-test",
            "workspace_name": "Status Workspace",
            "admin_email": "admin@acmestatus.io",
        }
        res_setup = await client.post("/api/v1/onboarding/workspace", json=setup_payload)
        assert res_setup.status_code == 200
        workspace_id = res_setup.json()["workspace_id"]

        save_payload = {
            "workspace_id": workspace_id,
            "provider_mode": "cloud",
            "provider_name": "gemini",
            "api_key": "mock-test-key-status",
            "default_llm_model": "gemini-2.0-flash",
            "default_embedding_model": "text-embedding-004",
            "default_reranker_model": "ms-marco-MiniLM-L-12-v2",
        }
        res_save = await client.post("/api/v1/onboarding/provider-settings", json=save_payload)
        assert res_save.status_code == 200

        res_status = await client.get("/api/v1/onboarding/status")
        assert res_status.status_code == 200
        data = res_status.json()
        assert data["is_onboarded"] is True
        assert data["workspace_name"] == "Status Workspace"
        assert data["provider_mode"] == "cloud"
        assert data["default_llm_model"] == "gemini-2.0-flash"
        assert data["default_embedding_model"] == "text-embedding-004"
        assert data["default_reranker_model"] == "ms-marco-MiniLM-L-12-v2"
