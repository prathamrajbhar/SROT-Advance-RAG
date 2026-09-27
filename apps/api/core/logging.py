import logging
import os
import sys
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ConsoleFormatter(logging.Formatter):
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    LEVEL_COLORS = {
        "DEBUG": GRAY,
        "INFO": CYAN,
        "WARNING": YELLOW,
        "ERROR": RED,
        "CRITICAL": f"{BOLD}{RED}",
    }

    METHOD_COLORS = {
        "GET": BLUE,
        "POST": GREEN,
        "PUT": YELLOW,
        "PATCH": YELLOW,
        "DELETE": RED,
        "OPTIONS": GRAY,
        "HEAD": GRAY,
    }

    def _status_color(self, status_code: int) -> str:
        if status_code < 300:
            return self.GREEN
        if status_code < 400:
            return self.CYAN
        if status_code < 500:
            return self.YELLOW
        return self.RED

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%H:%M:%S")
        level_color = self.LEVEL_COLORS.get(record.levelname, self.RESET)
        level_badge = f"{level_color}{record.levelname:<5}{self.RESET}"

        # HTTP request lines get method, path, status, latency
        if hasattr(record, "status_code") and hasattr(record, "path"):
            method = getattr(record, "method", "")
            method_color = self.METHOD_COLORS.get(method, self.BOLD)
            status_code = getattr(record, "status_code", 200)
            status_color = self._status_color(status_code)
            latency_ms = getattr(record, "latency_ms", 0.0)
            trace_id = getattr(record, "trace_id", "")

            method_part = f"{method_color}{method}{self.RESET} " if method else ""
            path_part = f"{record.path}"
            status_part = f"{status_color}{status_code}{self.RESET}"
            latency_part = f"{self.GRAY}{latency_ms:.1f}ms{self.RESET}"
            trace_part = f" {self.DIM}[trace:{trace_id[:8]}]{self.RESET}" if trace_id else ""

            log_line = (
                f"{self.GRAY}{timestamp}{self.RESET} "
                f"{level_badge} "
                f"{self.GRAY}[{record.name}]{self.RESET} "
                f"{method_part}{path_part} -> {status_part} {latency_part}{trace_part}"
            )
        else:
            message = record.getMessage()
            trace_id = getattr(record, "trace_id", None)
            trace_part = f" {self.DIM}[trace:{trace_id[:8]}]{self.RESET}" if trace_id else ""

            log_line = (
                f"{self.GRAY}{timestamp}{self.RESET} "
                f"{level_badge} "
                f"{self.GRAY}[{record.name}]{self.RESET} "
                f"{message}{trace_part}"
            )

        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ConsoleFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

    for noisy in [
        "uvicorn.access",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
        "httpx",
        "httpcore",
    ]:
        noisy_logger = logging.getLogger(noisy)
        noisy_logger.setLevel(logging.WARNING)
        noisy_logger.propagate = False


logger = logging.getLogger("srot.http")

QUIET_PATHS = frozenset(
    {"/health", "/ready", "/api/v1/health", "/api/v1/ready", "/docs", "/openapi.json"}
)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex[:16]
        request.state.trace_id = trace_id
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Process-Time-Ms"] = str(latency_ms)

            # keep probe traffic out of the log
            if request.url.path not in QUIET_PATHS:
                extra = {
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                }
                logger.info(
                    f"{request.method} {request.url.path} -> {response.status_code} ({latency_ms}ms)",
                    extra=extra,
                )
            return response
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled request error on {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latency_ms": latency_ms,
                },
            )
            raise
