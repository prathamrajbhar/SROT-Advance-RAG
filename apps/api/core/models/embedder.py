import hashlib
import math
from typing import List
import httpx
from core.config import get_settings
from core.models.base import BaseEmbedder

settings = get_settings()


class EmbedderAdapter(BaseEmbedder):
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.embedder_url = settings.EMBEDDER_URL
        self._dimension = 1024 if self.provider == "local" else 1536

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == "local":
            try:
                headers = {"X-Internal-Token": settings.INTERNAL_MODEL_TOKEN}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        f"{self.embedder_url}/embed",
                        headers=headers,
                        json={"texts": texts},
                    )
                    if res.status_code == 200:
                        return res.json().get("embeddings", [])
            except Exception:
                pass
            # Fallback deterministic pseudo-embedding generation for testing/dev
            return [self._generate_pseudo_vector(t, self.dimension) for t in texts]

        if self.provider == "openai" and settings.OPENAI_API_KEY:
            url = "https://api.openai.com/v1/embeddings"
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            body = {"model": "text-embedding-3-small", "input": texts}
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=body)
                res.raise_for_status()
                data = res.json()
                return [item["embedding"] for item in data.get("data", [])]

        # Default fallback
        return [self._generate_pseudo_vector(t, self.dimension) for t in texts]

    def _generate_pseudo_vector(self, text: str, dim: int) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(dim):
            byte_val = h[i % len(h)]
            val = (byte_val / 255.0) * 2.0 - 1.0 + math.sin(i + len(text))
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
