import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from models.project import ProjectRole


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    role: Optional[str] = "owner"
    document_count: int = 0
    updated_at: datetime


class ProjectDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    document_count: int = 0
    indexed_count: int = 0
    failed_count: int = 0
    total_chunks: int = 0
    last_indexed_at: Optional[datetime] = None


class MemberAddRequest(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.VIEWER


class MemberRoleUpdateRequest(BaseModel):
    role: ProjectRole


class MemberUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: Optional[str] = None


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: MemberUserResponse
    role: str
    joined_at: datetime
