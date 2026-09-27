from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderPingResult:
    """Diagnostic outcome of pinging a model provider."""

    healthy: bool
    latency_ms: float
    resolved_model: str
    error_message: Optional[str] = None


class BaseProviderAdapter(ABC):
    """Abstract contract for dynamic model provider adapters."""

    @abstractmethod
    async def ping(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> ProviderPingResult:
        """Executes a live ping to verify connectivity and authentication."""
        pass
