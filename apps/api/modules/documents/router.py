import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.events import stream_document_events
from modules.documents.schemas import (
    DocumentListResponse,
    MultipartCompleteRequest,
    MultipartCompleteResponse,
    MultipartInitiateRequest,
    MultipartInitiateResponse,
    PresignPartsRequest,
    PresignPartsResponse,
)
from modules.documents.service import (
    complete_upload_service,
    delete_document_service,
    initiate_upload_service,
    list_documents_service,
    presign_parts_service,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/multipart/initiate", response_model=MultipartInitiateResponse)
async def initiate_multipart_upload_endpoint(
    request: MultipartInitiateRequest,
    db: AsyncSession = Depends(get_db),
) -> MultipartInitiateResponse:
    """Initiates an S3 multipart upload and creates an INITIATED document record."""
    try:
        doc_id, upload_id, s3_key, chunk_size, total_parts = await initiate_upload_service(request, db)
        return MultipartInitiateResponse(
            document_id=doc_id,
            upload_id=upload_id,
            s3_key=s3_key,
            chunk_size_bytes=chunk_size,
            total_parts=total_parts,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"S3 initiate failed: {e}")


@router.post("/multipart/presign-parts", response_model=PresignPartsResponse)
async def presign_parts_endpoint(
    request: PresignPartsRequest,
) -> PresignPartsResponse:
    """Generates presigned PUT URLs for parallel part uploads directly to S3."""
    try:
        parts = presign_parts_service(request)
        return PresignPartsResponse(parts=parts)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to presign parts: {e}")


@router.post("/multipart/complete", response_model=MultipartCompleteResponse)
async def complete_multipart_upload_endpoint(
    request: MultipartCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> MultipartCompleteResponse:
    """Completes the S3 multipart upload and dispatches Celery ingestion task."""
    try:
        doc, job = await complete_upload_service(request, db)
        return MultipartCompleteResponse(
            document_id=doc.id,
            status=doc.status,
            s3_location=doc.s3_raw_key,
            processing_job_id=job.id if job else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"S3 complete failed: {e}")


@router.get("", response_model=DocumentListResponse)
async def list_documents_endpoint(
    workspace_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """Lists all cataloged documents and their ingestion states for a workspace."""
    documents = await list_documents_service(workspace_id, db)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deletes a document and all related jobs from the catalog."""
    deleted = await delete_document_service(document_id, db)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found")


@router.get("/{document_id}/progress-stream")
async def document_progress_stream_endpoint(
    document_id: uuid.UUID,
) -> StreamingResponse:
    """Real-time Server-Sent Events (SSE) stream broadcasting ingestion progress from Redis Pub/Sub."""
    return StreamingResponse(
        stream_document_events(str(document_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
