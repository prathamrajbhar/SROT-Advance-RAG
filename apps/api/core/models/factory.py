"""Model factory returning typed adapters based on environment configuration.

Zero hardcoded fallbacks or dummy API keys: fails fast with descriptive validation errors.
"""
from __future__ import annotations

from core.config import get_settings
from core.models.base import BaseEmbedder, BaseLLMClient, BaseReranker, BaseWhisper
from core.models.embedder import EmbedderAdapter
from core.models.providers.anthropic_provider import AnthropicProvider
from core.models.providers.gemini_provider import GeminiProvider
from core.models.providers.openai_provider import OpenAICompatibleProvider
from core.models.reranker import RerankerAdapter
from core.models.whisper import WhisperAdapter

settings = get_settings()


OPENAI_COMPATIBLE_REGISTRY = {
    "ollama": ("http://localhost:11434/v1", lambda s: "none"),
    "vllm": ("http://localhost:8000/v1", lambda s: s.OPENAI_API_KEY or "none"),
    "openai": ("https://api.openai.com/v1", lambda s: s.OPENAI_API_KEY),
    "groq": ("https://api.groq.com/openai/v1", lambda s: s.GROQ_API_KEY or s.OPENAI_API_KEY),
    "deepseek": ("https://api.deepseek.com/v1", lambda s: s.DEEPSEEK_API_KEY or s.OPENAI_API_KEY),
    "openrouter": ("https://openrouter.ai/api/v1", lambda s: s.OPENROUTER_API_KEY or s.OPENAI_API_KEY),
    "mistral": ("https://api.mistral.ai/v1", lambda s: s.MISTRAL_API_KEY or s.OPENAI_API_KEY),
    "together": ("https://api.together.xyz/v1", lambda s: s.TOGETHER_API_KEY or s.OPENAI_API_KEY),
}


def get_llm_client(custom_settings=None) -> BaseLLMClient:
    active_settings = custom_settings or settings
    provider = active_settings.LLM_PROVIDER.lower()
    model = active_settings.LLM_MODEL

    if provider in OPENAI_COMPATIBLE_REGISTRY:
        default_url, key_resolver = OPENAI_COMPATIBLE_REGISTRY[provider]
        api_key = key_resolver(active_settings)
        if not api_key:
            raise ValueError(f"{provider.upper()}_API_KEY is required when LLM_PROVIDER is '{provider}'")
        
        # Use provider's official base URL for cloud providers unless a non-ollama custom URL is provided
        custom_url = active_settings.LLM_BASE_URL
        if custom_url and provider in ("ollama", "vllm"):
            base_url = custom_url
        elif custom_url and not any(loc in custom_url for loc in ("11434", "localhost:8000")):
            base_url = custom_url
        else:
            base_url = default_url

        return OpenAICompatibleProvider(
            api_key=api_key,
            model=model,
            base_url=base_url,
            provider_name=provider,
        )


    if provider == "custom":
        if not active_settings.LLM_BASE_URL:
            raise ValueError("LLM_BASE_URL is required when LLM_PROVIDER is 'custom'")
        return OpenAICompatibleProvider(
            api_key=active_settings.OPENAI_API_KEY or "none",
            model=model,
            base_url=active_settings.LLM_BASE_URL,
            provider_name="custom",
        )

    if provider == "anthropic":
        if not active_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'")
        return AnthropicProvider(
            api_key=active_settings.ANTHROPIC_API_KEY,
            model=model,
        )

    if provider == "gemini":
        if not active_settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'")
        return GeminiProvider(
            api_key=active_settings.GEMINI_API_KEY,
            model=model,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'")



def get_embedder() -> BaseEmbedder:
    return EmbedderAdapter()


def get_reranker() -> BaseReranker:
    return RerankerAdapter()


def get_whisper() -> BaseWhisper:
    return WhisperAdapter()
