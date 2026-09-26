from core.config import get_settings
from core.models.base import BaseEmbedder, BaseLLMClient, BaseReranker, BaseWhisper
from core.models.embedder import EmbedderAdapter
from core.models.providers.anthropic_provider import AnthropicProvider
from core.models.providers.gemini_provider import GeminiProvider
from core.models.providers.openai_provider import OpenAICompatibleProvider
from core.models.reranker import RerankerAdapter
from core.models.whisper import WhisperAdapter

settings = get_settings()


def get_llm_client() -> BaseLLMClient:
    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL
    if provider == "gemini":
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY or "dummy_gemini_key",
            model=model,
        )
    if provider == "anthropic":
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY or "dummy_anthropic_key",
            model=model,
        )
    if provider == "openai":
        return OpenAICompatibleProvider(
            api_key=settings.OPENAI_API_KEY,
            model=model,
            base_url="https://api.openai.com/v1",
            provider_name="openai",
        )
    if provider == "groq":
        return OpenAICompatibleProvider(
            api_key=settings.GROQ_API_KEY,
            model=model,
            base_url="https://api.groq.com/openai/v1",
            provider_name="groq",
        )
    if provider in ("ollama", "vllm"):
        return OpenAICompatibleProvider(
            api_key="none",
            model=model,
            base_url=settings.LLM_BASE_URL or "http://localhost:11434/v1",
            provider_name=provider,
        )
    # Default fallback
    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY or "dummy_key",
        model=model,
    )


def get_embedder() -> BaseEmbedder:
    return EmbedderAdapter()


def get_reranker() -> BaseReranker:
    return RerankerAdapter()


def get_whisper() -> BaseWhisper:
    return WhisperAdapter()
