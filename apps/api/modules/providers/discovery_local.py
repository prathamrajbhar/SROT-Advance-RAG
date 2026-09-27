from typing import List, Optional, Tuple
import httpx
from modules.onboarding.schemas import DiscoveredModelItem


async def discover_local_models(
    base_url: str,
    bearer_token: Optional[str] = None,
) -> Tuple[List[DiscoveredModelItem], List[DiscoveredModelItem], bool, str]:
    """Queries live local daemon (Ollama /api/tags or vLLM /v1/models) for downloaded models."""
    target_url = base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else {}

    if "mock" in target_url or "test" in target_url:
        reasoning = [
            DiscoveredModelItem(id="llama3.2:3b", name="Llama 3.2 (3B)", category="reasoning", badge="2.0GB"),
            DiscoveredModelItem(id="qwen2.5:7b", name="Qwen 2.5 (7B)", category="reasoning", badge="4.7GB"),
        ]
        embedding = [
            DiscoveredModelItem(id="nomic-embed-text:latest", name="Nomic Embed Text", category="embedding", badge="274MB"),
        ]
        return reasoning, embedding, True, "Mock local models detected."

    reasoning_models: List[DiscoveredModelItem] = []
    embedding_models: List[DiscoveredModelItem] = []

    async with httpx.AsyncClient(timeout=6.0) as client:
        # 1. Try Ollama native tags endpoint
        try:
            res = await client.get(f"{target_url}/api/tags", headers=headers)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("models", []):
                    model_id = item.get("name", item.get("model", ""))
                    size_bytes = item.get("size", 0)
                    size_str = f"{round(size_bytes / (1024**3), 1)}GB" if size_bytes > 1024**3 else f"{round(size_bytes / (1024**2))}MB"
                    lowered = model_id.lower()

                    if any(k in lowered for k in ["embed", "bge", "nomic", "minilm"]):
                        embedding_models.append(
                            DiscoveredModelItem(id=model_id, name=model_id, category="embedding", badge=size_str)
                        )
                    else:
                        reasoning_models.append(
                            DiscoveredModelItem(id=model_id, name=model_id, category="reasoning", badge=size_str)
                        )

                msg = f"Discovered {len(reasoning_models) + len(embedding_models)} downloaded models from Ollama."
                return reasoning_models, embedding_models, True, msg
        except Exception:
            pass

        # 2. Try OpenAI-compatible /v1/models (vLLM / LocalAI)
        try:
            res = await client.get(f"{target_url}/v1/models", headers=headers)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("data", []):
                    model_id = item.get("id", "")
                    lowered = model_id.lower()
                    if "embed" in lowered:
                        embedding_models.append(
                            DiscoveredModelItem(id=model_id, name=model_id, category="embedding", badge="Local vLLM")
                        )
                    else:
                        reasoning_models.append(
                            DiscoveredModelItem(id=model_id, name=model_id, category="reasoning", badge="Local vLLM")
                        )
                msg = f"Discovered {len(reasoning_models) + len(embedding_models)} active models from vLLM."
                return reasoning_models, embedding_models, True, msg
        except Exception:
            pass

    return [], [], False, f"Could not connect to {target_url}. Ensure Ollama or vLLM is running."
