import logging
from typing import Any, Dict, Optional
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TraceSpan:
    def __init__(
        self,
        name: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.metadata = metadata or {}

    async def __aenter__(self) -> "TraceSpan":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_val:
            self.metadata["error"] = str(exc_val)


def create_span(
    name: str, trace_id: str, metadata: Optional[Dict[str, Any]] = None
) -> TraceSpan:
    return TraceSpan(name=name, trace_id=trace_id, metadata=metadata)


def record_generation(
    trace_id: str,
    name: str,
    model: str,
    prompt: Any,
    output: Any,
    usage: Optional[Dict[str, int]] = None,
    cost_usd: Optional[float] = None,
) -> None:
    logger.debug(
        "Trace generation",
        extra={
            "trace_id": trace_id,
            "span_name": name,
            "model": model,
            "cost_usd": cost_usd,
            "usage": usage,
        },
    )
