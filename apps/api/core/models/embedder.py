"""Enterprise-grade Embedder Adapter using local workspace open-source models.

Supported Providers:
- Local Workspace (fastembed ONNX in ./models)
- Ollama (e.g. nomic-embed-text, bge-m3)
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import httpx
from core.config import get_settings
from core.models.base import BaseEmbedder

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbedderAdapter(BaseEmbedder):
    def __init__(self) -> None:
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.model = getattr(settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self.embedder_url = settings.EMBEDDER_URL or "http://localhost:11434"
        
        # Resolve workspace models directory
        workspace_models = Path(settings.MODELS_DIR) if settings.MODELS_DIR else Path(__file__).resolve().parent.parent.parent.parent.parent / "models"
        self.models_dir = str(workspace_models)
        self._local_model = None
        self._dimension: Optional[int] = None

        if self.provider == "local":
            try:
                from fastembed import TextEmbedding
                self._local_model = TextEmbedding(model_name=self.model, cache_dir=self.models_dir)
            except Exception as exc:
                logger.warning("Could not initialize local fastembed model (%s): %s", self.model, exc)

    @property
    def dimension(self) -> int:
        if self._dimension:
            return self._dimension
        if self._local_model and hasattr(self._local_model, "embedding_dim"):
            return self._local_model.embedding_dim
        if "large" in self.model:
            return 1024
        if "small" in self.model:
            return 384
        return 768

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == "local":
            if self._local_model is None:
                from fastembed import TextEmbedding
                self._local_model = TextEmbedding(model_name=self.model, cache_dir=self.models_dir)
            
            # Execute embedding in threadpool for non-blocking async execution
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None, lambda: [arr.tolist() for arr in self._local_model.embed(texts)]
            )
            if results:
                self._dimension = len(results[0])
            return results

        if self.provider == "ollama":
            url = f"{self.embedder_url.rstrip('/')}/api/embed"
            batch_size = 64
            all_embeddings: List[List[float]] = []
            async with httpx.AsyncClient(timeout=120.0) as client:
                for idx in range(0, len(texts), batch_size):
                    batch = texts[idx : idx + batch_size]
                    body = {"model": self.model, "input": batch}
                    res = await client.post(url, json=body)
                    res.raise_for_status()
                    data = res.json()
                    embeddings: List[List[float]] = data.get("embeddings", [])
                    if not embeddings:
                        raise RuntimeError(f"Ollama returned empty embeddings for model '{self.model}'")
                    all_embeddings.extend(embeddings)
            if all_embeddings:
                self._dimension = len(all_embeddings[0])
            return all_embeddings

        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: '{self.provider}'")

