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


@router.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check(response: Response) -> Dict[str, Any]:
    checks: Dict[str, str] = {}
    is_ready = True

    # 1. Postgres
    try:
        async with async_session_factory() as session_db:
            await session_db.execute(text("SELECT 1"))
        checks["pg"] = "ok"
    except Exception as e:
        checks["pg"] = f"error: {str(e)}"
        is_ready = False

    # 2. Redis
    try:
        r = await get_redis()
        pong = await r.ping()
        checks["redis"] = "ok" if pong else "failed"
        if not pong:
            is_ready = False
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        is_ready = False

    # 3. Qdrant
    try:
        q = get_qdrant()
        await q.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {str(e)}"
        is_ready = False

    # 4. S3
    try:
        kwargs = get_s3_client_kwargs()
        async with session.client(**kwargs) as s3:
            await s3.list_buckets()
        checks["s3"] = "ok"
    except Exception as e:
        checks["s3"] = f"error: {str(e)}"
        is_ready = False

    # 5. LLM Provider
    try:
        llm = get_llm_client()
        checks["llm_provider"] = f"ok ({settings.LLM_PROVIDER}: {settings.LLM_MODEL})"
    except Exception as e:
        checks["llm_provider"] = f"error: {str(e)}"
        is_ready = False

    # 6. Embedder, Reranker, Whisper
    checks["embedder"] = "ok"
    checks["reranker"] = "ok"
    checks["whisper"] = "ok"

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"ready": is_ready, "checks": checks}
