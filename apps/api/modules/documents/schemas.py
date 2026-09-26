import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from models.document import IngestStatus


class DocumentUploadItem(BaseModel):
    document_id: Optional[uuid.UUID] = None
    filename: str
    sha256: Optional[str] = None
    status: str
    duplicate: bool = False
    existing_document_id: Optional[uuid.UUID] = None
    note: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    uploads: List[DocumentUploadItem]


class DocumentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    status: IngestStatus
    stats: Optional[Dict[str, Any]] = None
    pii_flags: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_human: Optional[str] = None
    created_at: datetime
    indexed_at: Optional[datetime] = None


class DocumentStatusResponse(BaseModel):
    status: str
    progress_pct: int = 0
    stage_detail: Optional[str] = None


class PresignedUrlResponse(BaseModel):
    url: str
    expires_in: int = 300
