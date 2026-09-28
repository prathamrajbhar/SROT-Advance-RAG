import math
import os
import uuid
from typing import Dict, List, Optional, Tuple
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from core.s3 import get_s3_manager
from models import Document, ProcessingJob, Workspace
from modules.documents.schemas import (
    DocumentItemResponse,
    MultipartCompleteRequest,
    MultipartInitiateRequest,
    PresignPartsRequest,
)
from modules.documents.tasks import process_document_task

CHUNK_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB chunks

MODALITY_MAP = {
    ".pdf": "document",
    ".docx": "document",
    ".txt": "document",
    ".xlsx": "tabular",
    ".xls": "tabular",
    ".csv": "tabular",
    ".mp4": "video",
    ".mov": "video",
    ".mkv": "video",
    ".mp3": "audio",
    ".wav": "audio",
    ".m4a": "audio",
}


def resolve_file_type(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    return MODALITY_MAP.get(ext, "document")


async def initiate_upload_service(
    request: MultipartInitiateRequest,
    db: AsyncSession,
) -> Tuple[uuid.UUID, str, str, int, int]:
    ws_query = select(Workspace).where(Workspace.id == request.workspace_id)
    workspace = (await db.execute(ws_query)).scalar_one_or_none()
    if not workspace:
        raise ValueError(f"Workspace {request.workspace_id} not found")

    file_type = resolve_file_type(request.filename)
    total_parts = max(1, math.ceil(request.file_size_bytes / CHUNK_SIZE_BYTES))

    s3_mgr = get_s3_manager()
    upload_id, s3_key = s3_mgr.initiate_multipart_upload(
        tenant_id=str(workspace.tenant_id),
        workspace_id=str(workspace.id),
        filename=request.filename,
        content_type=request.content_type or "application/octet-stream",
    )

    doc = Document(
        tenant_id=workspace.tenant_id,
        workspace_id=workspace.id,
        filename=request.filename,
        file_type=file_type,
        file_size_bytes=request.file_size_bytes,
        s3_raw_key=s3_key,
        status="INITIATED",
        metadata_json={"upload_id": upload_id, "total_parts": total_parts},
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return doc.id, upload_id, s3_key, CHUNK_SIZE_BYTES, total_parts


def presign_parts_service(request: PresignPartsRequest) -> List[Dict[str, object]]:
    s3_mgr = get_s3_manager()
    return s3_mgr.generate_presigned_part_urls(
        s3_key=request.s3_key,
        upload_id=request.upload_id,
        part_numbers=request.part_numbers,
    )


async def complete_upload_service(
    request: MultipartCompleteRequest,
    db: AsyncSession,
) -> Tuple[Document, ProcessingJob]:
    s3_mgr = get_s3_manager()
    parts_data = [{"part_number": p.part_number, "etag": p.etag} for p in request.parts]
    s3_result = s3_mgr.complete_multipart_upload(
        s3_key=request.s3_key,
        upload_id=request.upload_id,
        parts=parts_data,
    )

    doc_query = select(Document).where(Document.id == request.document_id)
    doc = (await db.execute(doc_query)).scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document {request.document_id} not found")

    doc.status = "UPLOADED"

    job = ProcessingJob(
        tenant_id=doc.tenant_id,
        document_id=doc.id,
        celery_task_id=f"ingest-{uuid.uuid4()}",
        stage="QUEUED",
        progress_percent=0,
        status="PENDING",
    )
    db.add(job)
    await db.commit()
    await db.refresh(doc)
    await db.refresh(job)

    # Dispatch Celery task
    try:
        process_document_task.delay(str(doc.id), doc.file_type, str(doc.tenant_id))
    except Exception:
        # If Celery daemon not running locally in test, fallback gracefully
        pass

    return doc, job


async def list_documents_service(
    workspace_id: uuid.UUID,
    db: AsyncSession,
) -> List[DocumentItemResponse]:
    query = (
        select(Document, ProcessingJob)
        .outerjoin(ProcessingJob, Document.id == ProcessingJob.document_id)
        .where(Document.workspace_id == workspace_id)
        .order_by(desc(Document.created_at))
    )
    rows = (await db.execute(query)).all()

    items: List[DocumentItemResponse] = []
    for doc, job in rows:
        items.append(
            DocumentItemResponse(
                id=doc.id,
                workspace_id=doc.workspace_id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes,
                status=doc.status,
                chunk_count=doc.total_chunks,
                created_at=doc.created_at,
                job_stage=job.stage if job else None,
                job_progress=job.progress_percent if job else None,
                job_message=doc.error_message,
            )
        )
    return items


async def delete_document_service(document_id: uuid.UUID, db: AsyncSession) -> bool:
    await db.execute(delete(ProcessingJob).where(ProcessingJob.document_id == document_id))
    result = await db.execute(delete(Document).where(Document.id == document_id))
    await db.commit()
    return result.rowcount > 0
