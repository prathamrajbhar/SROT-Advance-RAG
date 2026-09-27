import pytest
from modules.providers import provider_registry
from modules.providers.gemini_adapter import GeminiProviderAdapter
from modules.providers.local_adapter import LocalProviderAdapter
from modules.providers.openai_adapter import OpenAIProviderAdapter


@pytest.mark.asyncio
async def test_provider_registry_resolution():
    assert isinstance(provider_registry.get_adapter("openai"), OpenAIProviderAdapter)
    assert isinstance(provider_registry.get_adapter(provider_mode="local"), LocalProviderAdapter)
    assert isinstance(provider_registry.get_adapter(model="gemini-2.0-flash"), GeminiProviderAdapter)


@pytest.mark.asyncio
async def test_openai_adapter_missing_key():
    adapter = OpenAIProviderAdapter()
    result = await adapter.ping(model="gpt-4o", api_key=None)
    assert not result.healthy
    assert "API key is required" in (result.error_message or "")


@pytest.mark.asyncio
async def test_mock_key_pings_succeed():
    openai_res = await provider_registry.get_adapter("openai").ping(
        model="gpt-4o", api_key="mock_test_key_123"
    )
    assert openai_res.healthy
    assert openai_res.latency_ms > 0

    gemini_res = await provider_registry.get_adapter("gemini").ping(
        model="gemini-2.0-flash", api_key="mock_gemini_key"
    )
    assert gemini_res.healthy

    local_res = await provider_registry.get_adapter(provider_mode="local").ping(
        model="llama3:8b", base_url="http://mock-host:11434"
    )
    assert local_res.healthy
