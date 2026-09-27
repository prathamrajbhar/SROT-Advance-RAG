#!/usr/bin/env python3
"""Workspace Model Provisioning & Downloader.

Downloads and pre-caches open-source embedding and reranker model weights directly
into the workspace './models' directory, and syncs local LLMs if configured.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from core.config import get_settings


def pull_ollama_model(base_url: str, model_name: str) -> bool:
    endpoint = f"{base_url.rstrip('/')}/api/pull"
    print(f"  ⬇  Downloading / verifying Ollama LLM '{model_name}' from {endpoint}...")
    try:
        with httpx.Client(timeout=600.0) as client:
            with client.stream("POST", endpoint, json={"name": model_name, "stream": True}) as response:
                if response.status_code != 200:
                    print(f"  ✖ Failed to pull '{model_name}': HTTP {response.status_code}")
                    return False
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                        status = payload.get("status", "")
                        completed = payload.get("completed", 0)
                        total = payload.get("total", 0)
                        if total > 0:
                            pct = (completed / total) * 100
                            print(f"\r     [{status}] {pct:.1f}%", end="", flush=True)
                        else:
                            print(f"\r     [{status}]", end="", flush=True)
                    except json.JSONDecodeError:
                        pass
        print(f"\n  ✓ Ollama model '{model_name}' ready in workspace.\n")
        return True
    except httpx.ConnectError:
        print(f"\n  ⚠ Could not connect to Ollama at {base_url}. Ensure Ollama is running if using Ollama LLM.")
        return False
    except Exception as exc:
        print(f"\n  ✖ Error pulling model '{model_name}': {exc}")
        return False


def provision_fastembed_models(models_dir: Path, embed_model_name: str, reranker_model_name: str) -> bool:
    success = True
    print(f"\n[1/3] Downloading Workspace Embedding Model ('{embed_model_name}')...")
    try:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name=embed_model_name, cache_dir=str(models_dir))
        # Warmup probe
        _ = list(model.embed(["probe"]))
        print(f"  ✓ Embedding model '{embed_model_name}' cached in {models_dir}")
    except Exception as exc:
        print(f"  ✖ Failed to download embedding model '{embed_model_name}': {exc}")
        success = False

    print(f"\n[2/3] Downloading Workspace Cross-Encoder Reranker ('{reranker_model_name}')...")
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        reranker = TextCrossEncoder(model_name=reranker_model_name, cache_dir=str(models_dir))
        # Warmup probe
        _ = list(reranker.rerank("q", ["c1"]))
        print(f"  ✓ Reranker model '{reranker_model_name}' cached in {models_dir}")
    except Exception as exc:
        print(f"  ✖ Failed to download reranker model '{reranker_model_name}': {exc}")
        success = False

    return success


def main() -> int:
    settings = get_settings()
    print("====================================================")
    print("  SROT Workspace Open-Source Model Provisioning")
    print("====================================================")

    models_dir = Path(settings.MODELS_DIR) if settings.MODELS_DIR else ROOT_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Target directory: {models_dir}")

    embed_name = getattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    rerank_name = getattr(settings, "RERANKER_MODEL", "BAAI/bge-reranker-base")

    success = provision_fastembed_models(models_dir, embed_name, rerank_name)

    # 3. Local LLM Model (if configured for Ollama)
    if settings.LLM_PROVIDER.lower() == "ollama":
        llm_model = settings.LLM_MODEL
        llm_url = (settings.LLM_BASE_URL or "http://localhost:11434/v1").replace("/v1", "")
        print(f"\n[3/3] Provisioning Local LLM Model ({llm_model}):")
        if not pull_ollama_model(llm_url, llm_model):
            pass  # Non-fatal if user intends to run cloud provider
    else:
        print(f"\n[3/3] LLM provider configured as '{settings.LLM_PROVIDER}' ({settings.LLM_MODEL}) — Skipping local LLM pull.")

    print("\n====================================================")
    if success:
        print("  ✓ All workspace models verified and ready for local inference.")
    else:
        print("  ⚠ Some models could not be cached. Check logs above.")
    print("====================================================")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
