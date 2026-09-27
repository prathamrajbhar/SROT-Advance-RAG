from typing import Dict, Optional
from modules.providers.anthropic_adapter import AnthropicProviderAdapter
from modules.providers.base import BaseProviderAdapter
from modules.providers.gemini_adapter import GeminiProviderAdapter
from modules.providers.groq_adapter import GroqProviderAdapter
from modules.providers.local_adapter import LocalProviderAdapter
from modules.providers.openai_adapter import OpenAIProviderAdapter


class ProviderRegistry:
    """Factory registry returning the appropriate provider adapter."""

    def __init__(self) -> None:
        self._adapters: Dict[str, BaseProviderAdapter] = {
            "openai": OpenAIProviderAdapter(),
            "gemini": GeminiProviderAdapter(),
            "anthropic": AnthropicProviderAdapter(),
            "groq": GroqProviderAdapter(),
            "local": LocalProviderAdapter(),
            "ollama": LocalProviderAdapter(),
            "vllm": LocalProviderAdapter(),
        }

    def get_adapter(
        self,
        provider_name: Optional[str] = None,
        provider_mode: str = "cloud",
        model: Optional[str] = None,
    ) -> BaseProviderAdapter:
        if provider_mode == "local" or (provider_name and provider_name.lower() in ["local", "ollama", "vllm"]):
            return self._adapters["local"]

        if provider_name:
            normalized_name = provider_name.lower().strip()
            if normalized_name in self._adapters:
                return self._adapters[normalized_name]

        if model:
            lowered_model = model.lower()
            if "gemini" in lowered_model:
                return self._adapters["gemini"]
            if "claude" in lowered_model or "anthropic" in lowered_model:
                return self._adapters["anthropic"]
            if "groq" in lowered_model or "llama" in lowered_model or "mixtral" in lowered_model:
                return self._adapters["groq"]

        # Default fallback to OpenAI-compatible
        return self._adapters["openai"]


provider_registry = ProviderRegistry()
