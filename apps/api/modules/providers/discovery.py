from typing import Optional
from modules.onboarding.schemas import DiscoverModelsResponse
from modules.providers.discovery_cloud import discover_cloud_models
from modules.providers.discovery_local import discover_local_models


async def discover_models_service(
    provider_mode: str,
    provider_name: Optional[str] = "gemini",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> DiscoverModelsResponse:
    """Entry point dispatching model discovery based on architecture mode."""
    if provider_mode == "local" or (provider_name and provider_name.lower() in ["local", "ollama", "vllm"]):
        host_url = base_url or "http://localhost:11434"
        reasoning, embedding, is_live, msg = await discover_local_models(host_url, api_key)
        return DiscoverModelsResponse(
            provider="local",
            reasoning_models=reasoning,
            embedding_models=embedding,
            is_live=is_live,
            total_count=len(reasoning) + len(embedding),
            message=msg,
        )

    resolved_provider = (provider_name or "gemini").lower()
    if not api_key:
        return DiscoverModelsResponse(
            provider=resolved_provider,
            reasoning_models=[],
            embedding_models=[],
            is_live=False,
            total_count=0,
            message=f"Please provide an API key for {resolved_provider.title()} to discover active models.",
        )

    reasoning, embedding, is_live, msg = await discover_cloud_models(resolved_provider, api_key)
    return DiscoverModelsResponse(
        provider=resolved_provider,
        reasoning_models=reasoning,
        embedding_models=embedding,
        is_live=is_live,
        total_count=len(reasoning) + len(embedding),
        message=msg,
    )
