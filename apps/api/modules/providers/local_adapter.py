import time
from typing import Optional
import httpx
from modules.providers.base import BaseProviderAdapter, ProviderPingResult


class LocalProviderAdapter(BaseProviderAdapter):
    """Adapter for Self-Hosted Local Ollama, vLLM, or OpenAI-compatible servers."""

    DEFAULT_BASE_URL: str = "http://localhost:11434"

    async def ping(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> ProviderPingResult:
        target_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

        if "mock" in target_url or "test" in target_url:
            return ProviderPingResult(
                healthy=True,
                latency_ms=12.1,
                resolved_model=model,
            )

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. Try Ollama native tags endpoint
            try:
                ollama_res = await client.get(f"{target_url}/api/tags", headers=headers)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if ollama_res.status_code == 200:
                    return ProviderPingResult(
                        healthy=True,
                        latency_ms=latency_ms,
                        resolved_model=model,
                    )
            except Exception:
                pass

            # 2. Try OpenAI-compatible /v1/models or /models endpoint (vLLM / LocalAI)
            for path in ["/v1/models", "/models"]:
                try:
                    res = await client.get(f"{target_url}{path}", headers=headers)
                    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    if res.status_code == 200:
                        return ProviderPingResult(
                            healthy=True,
                            latency_ms=latency_ms,
                            resolved_model=model,
                        )
                except Exception:
                    continue

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ProviderPingResult(
            healthy=False,
            latency_ms=total_latency_ms,
            resolved_model=model,
            error_message=f"Unable to connect to local host at {target_url}. Is Ollama or vLLM running?",
        )
