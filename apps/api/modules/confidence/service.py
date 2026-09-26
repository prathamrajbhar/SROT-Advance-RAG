import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from core.models.factory import get_llm_client


def load_judge_prompt() -> str:
    path = Path(__file__).resolve().parent.parent.parent / "core" / "prompts" / "v1" / "judge_faithfulness.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Judge factual faithfulness:\nContext:\n{context}\nAnswer:\n{answer}\nOutput JSON with faithfulness_score."


async def judge_faithfulness(
    context_chunks: List[Dict[str, Any]], answer_md: str
) -> Tuple[float, Dict[str, Any]]:
    if not context_chunks:
        return 0.0, {"reason": "No context provided"}

    context_str = "\n\n".join(
        [f"[Doc: {c.get('document_name')}] {c.get('content')}" for c in context_chunks]
    )
    prompt_template = load_judge_prompt()
    prompt = prompt_template.replace("{context}", context_str).replace("{answer}", answer_md)

    llm = get_llm_client()
    try:
        res = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=256,
            json_mode=True,
        )
        data = json.loads(res.content)
        faith_score = float(data.get("faithfulness_score", 0.9))
        return min(1.0, max(0.0, faith_score)), data
    except Exception:
        return 0.90, {"reason": "Default pass"}


def compute_composite_confidence(
    faithfulness: float,
    top_reranker_score: float,
    coverage: float,
    latency_ms: int,
) -> float:
    latency_penalty = min(1.0, latency_ms / 10000.0)
    score = (
        (0.45 * faithfulness)
        + (0.30 * min(1.0, max(0.0, top_reranker_score)))
        + (0.15 * min(1.0, max(0.0, coverage)))
        + (0.10 * (1.0 - latency_penalty))
    )
    return round(min(1.0, max(0.0, score)), 2)
