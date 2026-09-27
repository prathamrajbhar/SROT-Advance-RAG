import asyncio
import base64
from typing import Any, Dict, Optional
import uuid
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from celery import Celery
from core.config import get_settings
from core.database import async_session_factory
from modules.ingestion.pipeline import process_document_ingestion

settings = get_settings()

_arq_pool: Optional[ArqRedis] = None


async def get_arq_pool() -> ArqRedis:
    """Get or create the global ARQ async connection pool."""
    global _arq_pool
    if _arq_pool is None:
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        _arq_pool = await create_pool(redis_settings)
    return _arq_pool


async def ingest_document_job(ctx: Dict[str, Any], document_id_str: str, file_b64: str) -> bool:
    """ARQ native async task for document ingestion."""
    doc_id = uuid.UUID(document_id_str)
    file_bytes = base64.b64decode(file_b64.encode("utf-8"))
    async with async_session_factory() as session:
        await process_document_ingestion(session, doc_id, file_bytes)
    return True


async def enqueue_ingestion_job(document_id: uuid.UUID, file_bytes: bytes) -> None:
    """Enqueue background document ingestion job to ARQ queue."""
    file_b64 = base64.b64encode(file_bytes).decode("utf-8")
    pool = await get_arq_pool()
    await pool.enqueue_job("ingest_document_job", str(document_id), file_b64)


class WorkerSettings:
    """ARQ worker configuration."""
    functions = [ingest_document_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 20
    job_timeout = 600


# Celery Fallback & Compatibility Layer
celery_app = Celery(
    "srot_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="ingest_document", bind=True, max_retries=3)
def ingest_document_task(self: Any, document_id_str: str, file_b64: str) -> bool:
    doc_id = uuid.UUID(document_id_str)
    file_bytes = base64.b64decode(file_b64.encode("utf-8"))

    async def _run() -> None:
        async with async_session_factory() as session:
            await process_document_ingestion(session, doc_id, file_bytes)

    try:
        asyncio.run(_run())
        return True
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)

