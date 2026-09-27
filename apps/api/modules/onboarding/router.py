from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models import Workspace
from modules.onboarding.diagnostics import run_pipeline_diagnostics
from modules.onboarding.model_downloader import get_download_progress, start_model_download
from modules.onboarding.schemas import (
    DiscoverModelsRequest,
    DiscoverModelsResponse,
    ModelPullProgressResponse,
    ModelPullRequest,
    OnboardingStatusResponse,
    PipelineDiagnosticRequest,
    PipelineDiagnosticResponse,
    ProviderHealthCheckResponse,
    ProviderSettingsResponse,
    ProviderSettingsSaveRequest,
    ProviderTestRequest,
    SeedSampleDataRequest,
    SeedSampleDataResponse,
    WorkspaceSetupRequest,
    WorkspaceSetupResponse,
)
from modules.onboarding.service import (
    check_onboarding_status,
    provision_workspace,
    save_encrypted_provider_settings,
    seed_sample_documents,
)
from modules.providers import provider_registry
from modules.providers.discovery import discover_models_service

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    db: AsyncSession = Depends(get_db),
) -> OnboardingStatusResponse:
    """Checks whether the system has completed onboarding and returns active workspace info."""
    status_data = await check_onboarding_status(db)
    return OnboardingStatusResponse(**status_data)


@router.post("/test-pipeline", response_model=PipelineDiagnosticResponse)
async def test_pipeline_endpoint(request: PipelineDiagnosticRequest) -> PipelineDiagnosticResponse:
    """Executes live end-to-end diagnostics across LLM, Embeddings, and Reranker."""
    return await run_pipeline_diagnostics(request)


@router.post("/models/pull", response_model=ModelPullProgressResponse)
async def pull_model_endpoint(request: ModelPullRequest) -> ModelPullProgressResponse:
    """Dispatches in-platform download for local Ollama or FlashRank ONNX models."""
    return start_model_download(request)


@router.get("/models/pull-status/{job_id}", response_model=ModelPullProgressResponse)
async def get_pull_status_endpoint(job_id: str) -> ModelPullProgressResponse:
    """Polls real-time download percentage and transfer progress."""
    job = get_download_progress(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")
    return job


@router.post("/discover-models", response_model=DiscoverModelsResponse)
async def discover_models_endpoint(
    request: DiscoverModelsRequest,
) -> DiscoverModelsResponse:
    """Discovers available models dynamically from live cloud APIs or local host daemons."""
    return await discover_models_service(
        provider_mode=request.provider_mode,
        provider_name=request.provider_name,
        api_key=request.api_key,
        base_url=request.base_url,
    )



@router.post("/test-provider", response_model=ProviderHealthCheckResponse)
async def test_provider_connection(
    request: ProviderTestRequest,
) -> ProviderHealthCheckResponse:
    """Executes a live ping to verify provider connection and measure latency."""
    adapter = provider_registry.get_adapter(
        provider_name=request.provider_name,
        provider_mode=request.provider_mode,
        model=request.model,
    )
    result = await adapter.ping(
        model=request.model,
        api_key=request.api_key,
        base_url=request.base_url,
    )
    return ProviderHealthCheckResponse(
        healthy=result.healthy,
        provider_mode=request.provider_mode,
        resolved_model=result.resolved_model,
        latency_ms=result.latency_ms,
        error_message=result.error_message,
    )


@router.post("/workspace", response_model=WorkspaceSetupResponse)
async def setup_workspace(
    request: WorkspaceSetupRequest,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceSetupResponse:
    """Provisions a new tenant, initial workspace, and admin user."""
    tenant, workspace, user = await provision_workspace(request, db)
    return WorkspaceSetupResponse(
        tenant_id=tenant.id,
        workspace_id=workspace.id,
        user_id=user.id,
        tenant_slug=tenant.slug,
        workspace_name=workspace.name,
    )


@router.post("/provider-settings", response_model=ProviderSettingsResponse)
async def save_provider_settings(
    request: ProviderSettingsSaveRequest,
    db: AsyncSession = Depends(get_db),
) -> ProviderSettingsResponse:
    """Encrypts BYOK credentials with AES-256-GCM and persists them to PostgreSQL."""
    ws_query = select(Workspace).where(Workspace.id == request.workspace_id)
    workspace = (await db.execute(ws_query)).scalar_one_or_none()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {request.workspace_id} not found.",
        )

    setting, masked_key = await save_encrypted_provider_settings(workspace, request, db)
    return ProviderSettingsResponse(
        id=setting.id,
        workspace_id=setting.workspace_id,
        provider_mode=setting.provider_mode,
        default_llm_model=setting.default_llm_model,
        default_embedding_model=setting.default_embedding_model,
        default_reranker_model=setting.default_reranker_model,
        masked_key=masked_key,
        is_verified=setting.is_verified,
        last_tested_at=setting.last_tested_at,
    )


@router.post("/seed-sample-data", response_model=SeedSampleDataResponse)
async def seed_sample_dataset(
    request: SeedSampleDataRequest,
    db: AsyncSession = Depends(get_db),
) -> SeedSampleDataResponse:
    """Preloads verified multimodal sample files and registers indexing jobs."""
    ws_query = select(Workspace).where(Workspace.id == request.workspace_id)
    workspace = (await db.execute(ws_query)).scalar_one_or_none()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {request.workspace_id} not found.",
        )

    created_ids = await seed_sample_documents(workspace, db)
    return SeedSampleDataResponse(
        queued_jobs=len(created_ids),
        document_ids=created_ids,
        message="Enterprise sample dataset successfully preloaded and queued for indexing.",
    )
