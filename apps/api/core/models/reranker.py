"""Enterprise Reranker Adapter for open-source cross-encoder models.

Loads weights directly from the local workspace models directory (./models) via fastembed,
or routes to local TEI reranker service if explicitly configured.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import httpx
from core.config import get_settings
from core.models.base import BaseReranker

logger = logging.getLogger(__name__)
settings = get_settings()


class RerankerAdapter(BaseReranker):
    def __init__(self) -> None:
        self.provider = settings.RERANKER_PROVIDER.lower()
        self.model = getattr(settings, "RERANKER_MODEL", "BAAI/bge-reranker-base")
        self.reranker_url = settings.RERANKER_URL
        
        # Resolve workspace models directory with fallback if /app is not writable
        target_dir = None
        if settings.MODELS_DIR and settings.MODELS_DIR != "/app/models":
            try:
                p = Path(settings.MODELS_DIR)
                p.mkdir(parents=True, exist_ok=True)
                target_dir = p
            except (PermissionError, OSError):
                pass
        if target_dir is None:
            target_dir = Path(__file__).resolve().parents[4] / "models"
            target_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = str(target_dir)
        self._local_reranker = None

        if self.provider == "local":
            try:
                from fastembed.rerank.cross_encoder import TextCrossEncoder
                self._local_reranker = TextCrossEncoder(model_name=self.model, cache_dir=self.models_dir)
            except Exception as exc:
                logger.info("Local fastembed cross-encoder initialization: %s", exc)

    async def rerank(
        self, query: str, candidates: List[str], top_k: int = 8
    ) -> List[Tuple[int, float]]:
        if not candidates:
            return []

        # 1. In-process workspace cross-encoder reranker
        if self.provider == "local" and self._local_reranker is not None:
            try:
                loop = asyncio.get_running_loop()
                scores = await loop.run_in_executor(
                    None, lambda: list(self._local_reranker.rerank(query, candidates))
                )
                # Format (index, score) pairs
                ranked = [(idx, float(score)) for idx, score in enumerate(scores)]
                ranked.sort(key=lambda x: x[1], reverse=True)
                return ranked[:top_k]
            except Exception as exc:
                logger.warning("In-process reranking warning: %s", exc)

        # 2. Remote / standalone cross-encoder endpoint fallback
        if self.reranker_url:
            try:
                headers = {"X-Internal-Token": settings.INTERNAL_MODEL_TOKEN}
                payload = {"query": query, "texts": candidates, "candidates": candidates, "truncate": True}
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.post(
                        f"{self.reranker_url.rstrip('/')}/rerank",
                        headers=headers,
                        json=payload,
                    )
                    if res.status_code == 200:
                        raw_data = res.json()
                        items = raw_data if isinstance(raw_data, list) else raw_data.get("results", [])
                        parsed = [(int(r["index"]), float(r["score"])) for r in items]
                        parsed.sort(key=lambda x: x[1], reverse=True)
                        return parsed[:top_k]
            except Exception as exc:
                logger.warning("Local reranker endpoint unreachable (%s): %s", self.reranker_url, exc)

        # 3. Preserve hybrid retrieval RRF rank
        total = len(candidates)
        return [(idx, max(0.5, 0.95 - (idx * (0.4 / max(1, total))))) for idx in range(min(top_k, total))]

