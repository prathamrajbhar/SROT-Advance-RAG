import pytest
from httpx import AsyncClient
from modules.providers.discovery import discover_models_service


@pytest.mark.asyncio
async def test_discover_local_mock_models():
    """Verify local daemon mock endpoint discovers reasoning and embedding models."""
    res = await discover_models_service(
        provider_mode="local",
        base_url="http://mock-ollama:11434",
    )
    assert res.is_live is True
    assert res.provider == "local"
    assert len(res.reasoning_models) > 0
    assert len(res.embedding_models) > 0
    assert any(m.id == "llama3.2:3b" for m in res.reasoning_models)
    assert any(m.id == "nomic-embed-text:latest" for m in res.embedding_models)


@pytest.mark.asyncio
async def test_discover_cloud_mock_models():
    """Verify cloud provider mock returns flagship and embedding models."""
    res = await discover_models_service(
        provider_mode="cloud",
        provider_name="gemini",
        api_key="mock_test_key_123",
    )
    assert res.is_live is True
    assert res.provider == "gemini"
    assert len(res.reasoning_models) > 0
    assert len(res.embedding_models) > 0


@pytest.mark.asyncio
async def test_discover_cloud_missing_key():
    """Verify missing API key returns is_live=False with informative message."""
    res = await discover_models_service(
        provider_mode="cloud",
        provider_name="openai",
        api_key="",
    )
    assert res.is_live is False
    assert res.total_count == 0
    assert "Please provide an API key" in res.message


@pytest.mark.asyncio
async def test_discover_models_api_endpoint(client: AsyncClient):
    """Test the POST /api/v1/onboarding/discover-models endpoint."""
    res = await client.post(
        "/api/v1/onboarding/discover-models",
        json={
            "provider_mode": "local",
            "base_url": "http://test-host:11434",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_live"] is True
    assert len(data["reasoning_models"]) >= 1
    assert data["total_count"] >= 1
