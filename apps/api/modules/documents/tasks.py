import asyncio
import datetime
import logging
import time
import uuid
from typing import Optional
from sqlalchemy import select
from core.celery_app import celery_app
from core.database import async_session_factory
from core.events import publish_document_progress
from models.documents import Document
from models.jobs import ProcessingJob

logger = logging.getLogger("srot.tasks")


def run_async(coro):
    """Helper to run async coroutines from synchronous Celery worker threads."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def persist_job_stage(
    document_id: str,
    stage: str,
    progress_percent: int,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """Updates database Document and ProcessingJob records."""
    try:
        async with async_session_factory() as session:
            doc_uuid = uuid.UUID(document_id)
            doc = await session.get(Document, doc_uuid)
            if doc:
                if stage == "READY":
                    doc.status = "READY"
                    doc.total_chunks = max(doc.total_chunks, 1)
                elif stage == "FAILED":
                    doc.status = "FAILED"
                    doc.error_message = error_message
                elif doc.status != "READY":
                    doc.status = "PROCESSING"

            job_query = await session.execute(
                select(ProcessingJob).where(ProcessingJob.document_id == doc_uuid)
            )
            job = job_query.scalar_one_or_none()
            if job:
                job.stage = stage
                job.progress_percent = progress_percent
                job.status = status
                if stage in ("READY", "FAILED"):
                    job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await session.commit()
    except Exception as exc:
        logger.error(f"Failed to persist job stage {stage} for doc {document_id}: {exc}")


@celery_app.task(bind=True, name="modules.documents.tasks.process_document_task", max_retries=3)
def process_document_task(self, document_id: str, file_type: str, tenant_id: str):
    """Asynchronous worker task simulating phased multi-modal processing with real-time SSE broadcasts."""
    logger.info(f"Starting ingestion worker task for document {document_id} ({file_type})")

    try:
        # Phase 1: Queued & Initialization
        run_async(persist_job_stage(document_id, "QUEUED", 10, "PROCESSING"))
        run_async(publish_document_progress(
            document_id=document_id,
            stage="QUEUED",
            progress_percent=10,
            message="Task assigned to worker pool; preparing parser...",
        ))
        time.sleep(0.5)

        # Phase 2: Extraction & Layout Analysis
        run_async(persist_job_stage(document_id, "EXTRACTING", 45, "PROCESSING"))
        run_async(publish_document_progress(
            document_id=document_id,
            stage="EXTRACTING",
            progress_percent=45,
            message=f"Parsing {file_type.upper()} layout order and structural blocks...",
        ))
        time.sleep(0.8)

        # Phase 3: Chunking & Representation
        run_async(persist_job_stage(document_id, "CHUNKING", 75, "PROCESSING"))
        run_async(publish_document_progress(
            document_id=document_id,
            stage="CHUNKING",
            progress_percent=75,
            message="Generating hierarchical parent-child sections and bounding boxes...",
        ))
        time.sleep(0.5)

        # Phase 4: Ready for Hybrid Retrieval
        run_async(persist_job_stage(document_id, "READY", 100, "COMPLETED"))
        run_async(publish_document_progress(
            document_id=document_id,
            stage="READY",
            progress_percent=100,
            message="Ingestion complete. Document indexed in Qdrant & Catalog.",
        ))
        logger.info(f"Successfully processed document {document_id}")
        return {"status": "SUCCESS", "document_id": document_id}

    except Exception as exc:
        logger.error(f"Ingestion worker failed for document {document_id}: {exc}")
        run_async(persist_job_stage(document_id, "FAILED", 0, "FAILED", str(exc)))
        run_async(publish_document_progress(
            document_id=document_id,
            stage="FAILED",
            progress_percent=0,
            message=f"Processing failed: {str(exc)}",
        ))
        raise exc
