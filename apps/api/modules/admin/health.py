import time
from typing import Any, Dict
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from core.config import get_settings
from core.database import async_session_factory
from core.models.factory import get_embedder, get_llm_client, get_reranker, get_whisper
from core.qdrant import get_qdrant
from core.redis import get_redis
from core.s3 import get_s3_client_kwargs, session

router = APIRouter(tags=["Admin & Health"])
settings = get_settings()


async def run_diagnostics() -> Dict[str, Any]:
    """Runs a full diagnostic probe across all database, vector, cache, and AI model subsystems."""
    checks: Dict[str, Any] = {}
    is_healthy = True
    start_total = time.perf_counter()

    # 1. PostgreSQL Database
    t0 = time.perf_counter()
    try:
        async with async_session_factory() as session_db:
            await session_db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        checks["postgres"] = {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        checks["postgres"] = {"status": "unhealthy", "error": str(exc)}
        is_healthy = False

    # 2. Redis Cache & Broker
    t0 = time.perf_counter()
    try:
        r = await get_redis()
        pong = await r.ping()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        if pong:
            checks["redis"] = {"status": "healthy", "latency_ms": latency_ms}
        else:
            checks["redis"] = {"status": "unhealthy", "error": "Ping failed"}
            is_healthy = False
    except Exception as exc:
        checks["redis"] = {"status": "unhealthy", "error": str(exc)}
        is_healthy = False

    # 3. Qdrant Vector Engine
    t0 = time.perf_counter()
    try:
        q = get_qdrant()
        collections = await q.get_collections()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        collection_names = [c.name for c in collections.collections] if hasattr(collections, "collections") else []
        checks["qdrant"] = {
            "status": "healthy",
            "latency_ms": latency_ms,
            "collections_count": len(collection_names),
        }
    except Exception as exc:
        checks["qdrant"] = {"status": "unhealthy", "error": str(exc)}
        is_healthy = False

    # 4. S3 / Object Storage
    t0 = time.perf_counter()
    try:
        kwargs = get_s3_client_kwargs()
        async with session.client(**kwargs) as s3:
            await s3.list_buckets()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        checks["storage_s3"] = {"status": "healthy", "latency_ms": latency_ms, "bucket": settings.S3_BUCKET}
    except Exception as exc:
        checks["storage_s3"] = {"status": "degraded", "error": str(exc)}

    # 5. Embedding Model (Local FastEmbed / Ollama)
    t0 = time.perf_counter()
    try:
        embedder = get_embedder()
        sample_embed = await embedder.embed_texts(["health_probe"])
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        dim = len(sample_embed[0]) if sample_embed else embedder.dimension
        checks["embedding_model"] = {
            "status": "healthy",
            "provider": embedder.provider,
            "model": embedder.model,
            "dimension": dim,
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        checks["embedding_model"] = {
            "status": "unhealthy",
            "provider": settings.EMBEDDING_PROVIDER,
            "model": settings.EMBEDDING_MODEL,
            "error": str(exc),
        }
        is_healthy = False

    # 6. Reranker Model (Cross-Encoder / FastEmbed)
    t0 = time.perf_counter()
    try:
        reranker = get_reranker()
        sample_rerank = await reranker.rerank("health_query", ["health_candidate_1", "health_candidate_2"])
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        checks["reranker_model"] = {
            "status": "healthy",
            "provider": reranker.provider,
            "model": reranker.model,
            "latency_ms": latency_ms,
            "results_scored": len(sample_rerank),
        }
    except Exception as exc:
        checks["reranker_model"] = {
            "status": "degraded",
            "provider": settings.RERANKER_PROVIDER,
            "model": settings.RERANKER_MODEL,
            "error": str(exc),
        }

    # 7. LLM Provider Configuration
    try:
        llm = get_llm_client()
        checks["llm_provider"] = {
            "status": "configured",
            "provider": getattr(llm, "provider_name", settings.LLM_PROVIDER),
            "model": getattr(llm, "model", settings.LLM_MODEL),
        }
    except Exception as exc:
        checks["llm_provider"] = {
            "status": "misconfigured",
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "error": str(exc),
        }
        is_healthy = False

    # 8. Whisper Audio Transcription
    try:
        whisper = get_whisper()
        checks["whisper_audio"] = {
            "status": "configured",
            "endpoint": getattr(whisper, "whisper_url", settings.WHISPER_URL),
        }
    except Exception as exc:
        checks["whisper_audio"] = {"status": "unconfigured", "error": str(exc)}

    total_latency_ms = round((time.perf_counter() - start_total) * 1000, 2)

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "total_latency_ms": total_latency_ms,
        "environment": settings.ENVIRONMENT,
        "services": checks,
    }


@router.get("/health")
async def health_check(response: Response) -> Dict[str, Any]:
    """Comprehensive system & model health check endpoint."""
    result = await run_diagnostics()
    if result["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/ready")
async def readiness_check(response: Response) -> Dict[str, Any]:
    """Kubernetes / Docker readiness probe."""
    return await health_check(response)
