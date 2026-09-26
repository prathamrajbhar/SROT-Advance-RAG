from typing import List, Tuple
import httpx
from core.config import get_settings
from core.models.base import BaseReranker

settings = get_settings()


class RerankerAdapter(BaseReranker):
    def __init__(self):
        self.provider = settings.RERANKER_PROVIDER
        self.reranker_url = settings.RERANKER_URL

    async def rerank(
        self, query: str, candidates: List[str], top_k: int = 8
    ) -> List[Tuple[int, float]]:
        if not candidates:
            return []

        if self.provider == "local":
            try:
                headers = {"X-Internal-Token": settings.INTERNAL_MODEL_TOKEN}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        f"{self.reranker_url}/rerank",
                        headers=headers,
                        json={"query": query, "candidates": candidates, "top_k": top_k},
                    )
                    if res.status_code == 200:
                        results = res.json().get("results", [])
                        return [(r["index"], float(r["score"])) for r in results]
            except Exception:
                pass

        # Robust keyword & token overlap score for dev/testing
        query_terms = set(query.lower().split())
        scored: List[Tuple[int, float]] = []
        for i, text in enumerate(candidates):
            text_lower = text.lower()
            overlap = sum(1 for term in query_terms if term in text_lower)
            score = min(1.0, 0.4 + (overlap / max(1, len(query_terms))) * 0.55)
            scored.append((i, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
