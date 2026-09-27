from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProviderTestRequest(BaseModel):
    provider_mode: Literal["cloud", "local", "hybrid"] = "cloud"
    provider_name: Optional[str] = None
    model: str = Field(..., example="gemini-2.0-flash")
    api_key: Optional[str] = Field(None, description="Plaintext API key to verify")
    base_url: Optional[str] = Field(None, description="Host endpoint for local Ollama/vLLM")


class ProviderHealthCheckResponse(BaseModel):
    healthy: bool
    provider_mode: str
    resolved_model: str
    latency_ms: float
    error_message: Optional[str] = None


class WorkspaceSetupRequest(BaseModel):
    tenant_name: str = Field(..., min_length=2, max_length=255)
    tenant_slug: str = Field(..., min_length=2, max_length=255)
    workspace_name: str = Field(..., min_length=2, max_length=255)
    admin_email: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = None


class WorkspaceSetupResponse(BaseModel):
    tenant_id: UUID
    workspace_id: UUID
    user_id: UUID
    tenant_slug: str
    workspace_name: str


class ProviderSettingsSaveRequest(BaseModel):
    workspace_id: UUID
    provider_mode: Literal["cloud", "local", "hybrid"]
    provider_name: Optional[str] = None
    api_key: Optional[str] = Field(None, description="Plaintext key encrypted immediately at rest")
    base_url: Optional[str] = None
    default_llm_model: str = Field(..., example="gemini-2.0-flash")
    default_embedding_model: str = Field(..., example="text-embedding-3-large")
    default_reranker_model: str = Field("ms-marco-MiniLM-L-12-v2", example="ms-marco-MiniLM-L-12-v2")
    reranker_api_key: Optional[str] = Field(None, description="Optional API key for cloud reranker")


class ProviderSettingsResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    provider_mode: str
    default_llm_model: str
    default_embedding_model: str
    default_reranker_model: str
    masked_key: Optional[str] = None
    is_verified: bool
    last_tested_at: Optional[datetime] = None


class SeedSampleDataRequest(BaseModel):
    workspace_id: UUID


class SeedSampleDataResponse(BaseModel):
    queued_jobs: int
    document_ids: List[UUID]
    message: str


class DiscoverModelsRequest(BaseModel):
    provider_mode: Literal["cloud", "local", "hybrid"] = "cloud"
    provider_name: Optional[str] = "gemini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class DiscoveredModelItem(BaseModel):
    id: str
    name: str
    category: Literal["reasoning", "embedding"]
    badge: Optional[str] = None
    context_length: Optional[int] = None
    description: Optional[str] = None


class DiscoverModelsResponse(BaseModel):
    provider: str
    reasoning_models: List[DiscoveredModelItem]
    embedding_models: List[DiscoveredModelItem]
    is_live: bool
    total_count: int
    message: Optional[str] = None


class PipelineDiagnosticRequest(BaseModel):
    provider_mode: Literal["cloud", "local", "hybrid"] = "cloud"
    provider_name: Optional[str] = "gemini"
    llm_model: str = Field(..., example="gemini-2.0-flash")
    embedding_model: str = Field(..., example="text-embedding-004")
    reranker_model: str = Field("ms-marco-MiniLM-L-12-v2", example="ms-marco-MiniLM-L-12-v2")
    api_key: Optional[str] = None
    reranker_api_key: Optional[str] = None
    base_url: Optional[str] = None


class ProbeResult(BaseModel):
    healthy: bool
    latency_ms: float
    model: str
    message: Optional[str] = None
    metadata: Optional[dict] = None


class PipelineDiagnosticResponse(BaseModel):
    healthy: bool
    overall_latency_ms: float
    llm_probe: ProbeResult
    embedding_probe: ProbeResult
    reranker_probe: ProbeResult


class ModelPullRequest(BaseModel):
    engine: Literal["ollama", "vllm", "flashrank"] = "ollama"
    model_name: str = Field(..., example="nomic-embed-text")
    base_url: Optional[str] = "http://localhost:11434"


class ModelPullProgressResponse(BaseModel):
    job_id: str
    model_name: str
    engine: str
    status: Literal["starting", "downloading", "verifying", "ready", "failed"]
    completed_bytes: int = 0
    total_bytes: int = 0
    percentage: float = 0.0
    status_text: Optional[str] = None
    error: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    is_onboarded: bool
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    provider_mode: Optional[str] = None
    default_llm_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    default_reranker_model: Optional[str] = None



