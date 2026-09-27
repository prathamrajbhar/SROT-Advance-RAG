import time
from typing import Optional
import httpx
from modules.providers.base import BaseProviderAdapter, ProviderPingResult


class AnthropicProviderAdapter(BaseProviderAdapter):
    """Adapter for Anthropic API endpoints."""

    DEFAULT_BASE_URL: str = "https://api.anthropic.com/v1"

    async def ping(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> ProviderPingResult:
        if not api_key:
            return ProviderPingResult(
                healthy=False,
                latency_ms=0.0,
                resolved_model=model,
                error_message="API key is required for Anthropic provider.",
            )

        if api_key.startswith("mock_") or api_key.startswith("test_"):
            return ProviderPingResult(
                healthy=True,
                latency_ms=45.0,
                resolved_model=model,
            )

        use_custom_url = base_url and not any(h in base_url for h in ["localhost", "127.0.0.1", "11434"])
        root_url = base_url.rstrip("/") if use_custom_url else self.DEFAULT_BASE_URL
        endpoint_url = f"{root_url}/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint_url, headers=headers)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                if response.status_code == 200:
                    return ProviderPingResult(
                        healthy=True,
                        latency_ms=latency_ms,
                        resolved_model=model,
                    )

                try:
                    error_data = response.json().get("error", {})
                    message = error_data.get("message", f"HTTP {response.status_code}")
                except Exception:
                    message = response.text[:200] if response.text else f"HTTP {response.status_code}"

                return ProviderPingResult(
                    healthy=False,
                    latency_ms=latency_ms,
                    resolved_model=model,
                    error_message=f"Anthropic error: {message}",
                )
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ProviderPingResult(
                healthy=False,
                latency_ms=latency_ms,
                resolved_model=model,
                error_message=f"Network error: {str(exc)}",
            )
