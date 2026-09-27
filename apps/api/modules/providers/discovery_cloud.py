from typing import List, Tuple
import httpx
from modules.onboarding.schemas import DiscoveredModelItem

RECOMMENDED_PAIRED_EMBEDDINGS: List[DiscoveredModelItem] = [
    DiscoveredModelItem(id="nomic-embed-text", name="Ollama: Nomic Embed Text (8K)", category="embedding", badge="Zero Egress"),
    DiscoveredModelItem(id="bge-m3", name="Ollama: BAAI BGE-M3", category="embedding", badge="Local Vector"),
    DiscoveredModelItem(id="bge-small-en-v1.5", name="FastEmbed: BGE Small EN", category="embedding", badge="Embedded"),
    DiscoveredModelItem(id="text-embedding-004", name="Google: Text Embedding 004", category="embedding", badge="Cloud BYOK"),
    DiscoveredModelItem(id="text-embedding-3-large", name="OpenAI: Text Embedding 3 Large", category="embedding", badge="Cloud BYOK"),
]


async def _discover_gemini(client: httpx.AsyncClient, api_key: str) -> Tuple[List[DiscoveredModelItem], List[DiscoveredModelItem], bool, str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    res = await client.get(url)
    if res.status_code != 200:
        return [], [], False, f"Gemini API returned status {res.status_code}"
    data = res.json()
    reasoning, embedding = [], []
    for m in data.get("models", []):
        m_id = m.get("name", "").replace("models/", "")
        display = m.get("displayName", m_id)
        methods = m.get("supportedGenerationMethods", [])
        input_tokens = m.get("inputTokenLimit")
        badge = f"{round(input_tokens / 1000)}K" if input_tokens else None
        if "embedContent" in methods and "generateContent" not in methods:
            embedding.append(DiscoveredModelItem(id=m_id, name=display, category="embedding", badge=badge))
        elif "generateContent" in methods:
            reasoning.append(DiscoveredModelItem(id=m_id, name=display, category="reasoning", badge=badge))
    return reasoning, embedding, True, f"Discovered {len(reasoning)} Gemini models."


async def _discover_openai(client: httpx.AsyncClient, api_key: str) -> Tuple[List[DiscoveredModelItem], List[DiscoveredModelItem], bool, str]:
    url = "https://api.openai.com/v1/models"
    res = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
    if res.status_code != 200:
        return [], [], False, f"OpenAI API returned status {res.status_code}"
    data = res.json()
    reasoning, embedding = [], []
    for m in data.get("data", []):
        m_id = m.get("id", "")
        if "embedding" in m_id:
            embedding.append(DiscoveredModelItem(id=m_id, name=m_id, category="embedding"))
        elif any(m_id.startswith(p) for p in ["gpt-4", "o1", "o3", "o4", "chatgpt"]):
            reasoning.append(DiscoveredModelItem(id=m_id, name=m_id, category="reasoning"))
    return reasoning, embedding, True, f"Discovered {len(reasoning)} OpenAI models."


async def _discover_groq(client: httpx.AsyncClient, api_key: str) -> Tuple[List[DiscoveredModelItem], List[DiscoveredModelItem], bool, str]:
    url = "https://api.groq.com/openai/v1/models"
    res = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
    if res.status_code != 200:
        return [], [], False, f"Groq API returned status {res.status_code}"
    data = res.json()
    reasoning = []
    for m in data.get("data", []):
        m_id = m.get("id", "")
        lowered = m_id.lower()
        if any(bad in lowered for bad in ["whisper", "guard", "safeguard", "orpheus"]):
            continue
        badge = f"{m.get('context_window', 0) // 1024}K" if m.get("context_window") else "LPU"
        reasoning.append(DiscoveredModelItem(id=m_id, name=m_id, category="reasoning", badge=badge))
    return reasoning, RECOMMENDED_PAIRED_EMBEDDINGS, True, f"Discovered {len(reasoning)} Groq models. Paired with 5 vector embedding options."


async def _discover_anthropic(client: httpx.AsyncClient, api_key: str) -> Tuple[List[DiscoveredModelItem], List[DiscoveredModelItem], bool, str]:
    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    res = await client.get(url, headers=headers)
    if res.status_code != 200:
        return [], [], False, f"Anthropic API returned status {res.status_code}"
    data = res.json()
    reasoning = [
        DiscoveredModelItem(id=m.get("id", ""), name=m.get("display_name", m.get("id", "")), category="reasoning")
        for m in data.get("data", [])
    ]
    return reasoning, RECOMMENDED_PAIRED_EMBEDDINGS, True, f"Discovered {len(reasoning)} Anthropic models. Paired with 5 vector embedding options."


async def discover_cloud_models(
    provider_name: str,
    api_key: str,
) -> Tuple[List[DiscoveredModelItem], List[DiscoveredModelItem], bool, str]:
    """Queries live cloud model APIs using the user's provided API key."""
    if api_key.startswith("mock_") or api_key.startswith("test_"):
        reasoning = [
            DiscoveredModelItem(id=f"{provider_name}-flagship", name=f"{provider_name.title()} Flagship", category="reasoning", badge="Live"),
            DiscoveredModelItem(id=f"{provider_name}-fast", name=f"{provider_name.title()} Fast", category="reasoning", badge="Sub-200ms"),
        ]
        return reasoning, RECOMMENDED_PAIRED_EMBEDDINGS, True, f"Mock live models for {provider_name}."

    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            if provider_name == "gemini":
                return await _discover_gemini(client, api_key)
            if provider_name == "openai":
                return await _discover_openai(client, api_key)
            if provider_name == "groq":
                return await _discover_groq(client, api_key)
            if provider_name == "anthropic":
                return await _discover_anthropic(client, api_key)
        except Exception as e:
            return [], [], False, f"{provider_name.title()} API error: {str(e)}"

    return [], [], False, f"Failed to retrieve models from {provider_name}."
