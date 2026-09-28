import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MultipartInitiateRequest(BaseModel):
    workspace_id: uuid.UUID
    filename: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: int = Field(..., gt=0)
    content_type: Optional[str] = "application/octet-stream"


class MultipartInitiateResponse(BaseModel):
    document_id: uuid.UUID
    upload_id: str
    s3_key: str
    chunk_size_bytes: int
    total_parts: int


class PresignPartsRequest(BaseModel):
    document_id: uuid.UUID
    upload_id: str
    s3_key: str
    part_numbers: List[int] = Field(..., min_items=1)


class PresignedPartItem(BaseModel):
    part_number: int
    presigned_url: str


class PresignPartsResponse(BaseModel):
    parts: List[PresignedPartItem]


class CompletedPartItem(BaseModel):
    part_number: int
    etag: str


class MultipartCompleteRequest(BaseModel):
    document_id: uuid.UUID
    upload_id: str
    s3_key: str
    parts: List[CompletedPartItem]


class MultipartCompleteResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    s3_location: Optional[str] = None
    processing_job_id: Optional[uuid.UUID] = None


class DocumentItemResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    chunk_count: int
    created_at: datetime
    job_stage: Optional[str] = None
    job_progress: Optional[int] = None
    job_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentItemResponse]
    total: int
