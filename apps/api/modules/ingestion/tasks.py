import asyncio
import base64
import uuid
from celery import Celery
from core.config import get_settings
from core.database import async_session_factory
from modules.ingestion.pipeline import process_document_ingestion

settings = get_settings()

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
def ingest_document_task(self, document_id_str: str, file_b64: str) -> bool:
    doc_id = uuid.UUID(document_id_str)
    file_bytes = base64.b64decode(file_b64.encode("utf-8"))

    async def _run() -> None:
        async with async_session_factory() as session:
            await process_document_ingestion(session, doc_id, file_bytes)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run())
        return True
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
    finally:
        loop.close()
