import asyncio
import pytest
from httpx import AsyncClient
from modules.onboarding.diagnostics import run_pipeline_diagnostics
from modules.onboarding.model_downloader import get_download_progress, start_model_download
from modules.onboarding.schemas import ModelPullRequest, PipelineDiagnosticRequest


@pytest.mark.asyncio
async def test_tri_engine_pipeline_probe():
    req = PipelineDiagnosticRequest(
        provider_mode="cloud",
        provider_name="gemini",
        llm_model="gemini-2.0-flash",
        embedding_model="text-embedding-004",
        reranker_model="ms-marco-MiniLM-L-12-v2",
        api_key="mock_valid_key",
    )
    res = await run_pipeline_diagnostics(req)
    assert res.healthy is True
    assert res.llm_probe.healthy is True
    assert res.embedding_probe.healthy is True
    assert res.embedding_probe.metadata.get("dimensions") == 768
    assert res.reranker_probe.healthy is True
    assert res.overall_latency_ms > 0


@pytest.mark.asyncio
async def test_tri_engine_cohere_missing_key():
    req = PipelineDiagnosticRequest(
        provider_mode="cloud",
        provider_name="groq",
        llm_model="llama-3.3-70b-versatile",
        embedding_model="nomic-embed-text",
        reranker_model="rerank-v4-fast",
        api_key="mock_groq_key",
        reranker_api_key=None,
    )
    res = await run_pipeline_diagnostics(req)
    assert res.reranker_probe.healthy is False
    assert "Cohere API key is required" in (res.reranker_probe.message or "")
    assert res.healthy is False


@pytest.mark.asyncio
async def test_model_download_lifecycle():
    req = ModelPullRequest(
        engine="flashrank",
        model_name="ms-marco-TinyBERT-L-2-v2",
    )
    start_res = start_model_download(req)
    assert start_res.job_id.startswith("pull-")
    assert start_res.status == "downloading"

    # Wait for mock download stages to complete
    await asyncio.sleep(1.6)
    final_status = get_download_progress(start_res.job_id)
    assert final_status is not None
    assert final_status.status == "ready"
    assert final_status.percentage == 100.0


@pytest.mark.asyncio
async def test_pipeline_diagnostic_api_route(client: AsyncClient):
    res = await client.post(
        "/api/v1/onboarding/test-pipeline",
        json={
            "provider_mode": "cloud",
            "provider_name": "gemini",
            "llm_model": "gemini-2.0-flash",
            "embedding_model": "text-embedding-004",
            "reranker_model": "none",
            "api_key": "mock_valid_key",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["healthy"] is True
    assert data["reranker_probe"]["model"] == "none"
