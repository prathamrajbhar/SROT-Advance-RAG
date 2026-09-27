import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.auth import User
from modules.auth.deps import get_current_user
from modules.documents.schemas import (
    DocumentItemResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    PresignedUrlResponse,
)
from modules.documents.service import (
    delete_document,
    get_document_chunks,
    get_document_content_url,
    get_document_status,
    list_documents,
    upload_documents,
)

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_files(
    project_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    uploads = await upload_documents(db, project_id, user.id, files)
    return DocumentUploadResponse(uploads=uploads)


@router.get("", response_model=Dict[str, Any])
async def list_project_documents(
    project_id: uuid.UUID,
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    docs, total = await list_documents(
        db, project_id, user.id, status_filter=status, query_str=q, page=page, page_size=page_size
    )
    return {
        "items": [DocumentItemResponse.model_validate(d) for d in docs],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_status_endpoint(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    status_data = await get_document_status(db, project_id, doc_id, user.id)
    return DocumentStatusResponse.model_validate(status_data)


@router.get("/{doc_id}/content", response_model=PresignedUrlResponse)
async def get_content_url_endpoint(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PresignedUrlResponse:
    url = await get_document_content_url(db, project_id, doc_id, user.id)
    return PresignedUrlResponse(url=url, expires_in=300)


@router.get("/{doc_id}/chunks", response_model=Dict[str, Any])
async def get_document_chunks_endpoint(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    return await get_document_chunks(db, project_id, doc_id, user.id)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await delete_document(db, project_id, doc_id, user.id)
