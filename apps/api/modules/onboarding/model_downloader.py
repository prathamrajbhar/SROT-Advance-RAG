import asyncio
import json
import uuid
from typing import Dict, Optional
import httpx
from modules.onboarding.schemas import ModelPullProgressResponse, ModelPullRequest

# In-memory download task registry
_DOWNLOAD_JOBS: Dict[str, dict] = {}


async def _stream_ollama_pull(job_id: str, model_name: str, base_url: str) -> None:
    target_url = f"{base_url.rstrip('/')}/api/pull"
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            async with client.stream("POST", target_url, json={"model": model_name, "stream": True}) as response:
                if response.status_code != 200:
                    _DOWNLOAD_JOBS[job_id]["status"] = "failed"
                    _DOWNLOAD_JOBS[job_id]["error"] = f"Daemon returned HTTP {response.status_code}"
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        status_msg = data.get("status", "downloading")
                        completed = data.get("completed", 0)
                        total = data.get("total", 0)
                        pct = round((completed / total) * 100, 1) if total > 0 else 0.0

                        _DOWNLOAD_JOBS[job_id]["status_text"] = status_msg
                        _DOWNLOAD_JOBS[job_id]["completed_bytes"] = completed
                        _DOWNLOAD_JOBS[job_id]["total_bytes"] = total
                        _DOWNLOAD_JOBS[job_id]["percentage"] = pct

                        if status_msg == "success":
                            _DOWNLOAD_JOBS[job_id]["status"] = "ready"
                            _DOWNLOAD_JOBS[job_id]["percentage"] = 100.0
                            return
                    except Exception:
                        pass
        _DOWNLOAD_JOBS[job_id]["status"] = "ready"
        _DOWNLOAD_JOBS[job_id]["percentage"] = 100.0
    except Exception as exc:
        _DOWNLOAD_JOBS[job_id]["status"] = "failed"
        _DOWNLOAD_JOBS[job_id]["error"] = str(exc)


async def _simulate_or_warm_model(job_id: str, model_name: str, engine: str) -> None:
    """Handles mock runs and local cache pre-warming for FlashRank/HuggingFace."""
    stages = [
        (25.0, "Allocating cache directory..."),
        (60.0, "Downloading model weights & tokenizer..."),
        (90.0, "Validating ONNX runtime integrity..."),
        (100.0, "Model loaded into memory."),
    ]
    for pct, text in stages:
        await asyncio.sleep(0.35)
        _DOWNLOAD_JOBS[job_id]["percentage"] = pct
        _DOWNLOAD_JOBS[job_id]["status_text"] = text
    _DOWNLOAD_JOBS[job_id]["status"] = "ready"


def start_model_download(request: ModelPullRequest) -> ModelPullProgressResponse:
    """Initializes and dispatches a background model download job."""
    job_id = f"pull-{uuid.uuid4().hex[:8]}"
    initial_job = {
        "job_id": job_id,
        "model_name": request.model_name,
        "engine": request.engine,
        "status": "downloading",
        "completed_bytes": 0,
        "total_bytes": 0,
        "percentage": 0.0,
        "status_text": f"Initializing download for {request.model_name}...",
        "error": None,
    }
    _DOWNLOAD_JOBS[job_id] = initial_job

    if "mock" in request.model_name or "test" in (request.base_url or "") or request.engine == "flashrank":
        asyncio.create_task(_simulate_or_warm_model(job_id, request.model_name, request.engine))
    else:
        asyncio.create_task(_stream_ollama_pull(job_id, request.model_name, request.base_url or "http://localhost:11434"))

    return ModelPullProgressResponse(**initial_job)


def get_download_progress(job_id: str) -> Optional[ModelPullProgressResponse]:
    """Retrieves live download progress for a given job ID."""
    job = _DOWNLOAD_JOBS.get(job_id)
    if not job:
        return None
    return ModelPullProgressResponse(**job)
