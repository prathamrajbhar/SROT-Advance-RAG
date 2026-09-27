import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db

router = APIRouter(tags=["Health"])
settings = get_settings()


async def run_diagnostics(db: AsyncSession) -> Dict[str, Any]:
    """Probe the database and report per-dependency status with latency."""
    checks: Dict[str, Any] = {}
    is_healthy = True
    start_total = time.perf_counter()

    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    except Exception as exc:
        checks["postgres"] = {"status": "unhealthy", "error": str(exc)}
        is_healthy = False

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "total_latency_ms": round((time.perf_counter() - start_total) * 1000, 2),
        "environment": settings.ENVIRONMENT,
        "services": checks,
    }


@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Liveness and dependency health check endpoint."""
    result = await run_diagnostics(db)
    if result["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/ready")
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Kubernetes / Docker readiness probe."""
    result = await run_diagnostics(db)
    if result["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
