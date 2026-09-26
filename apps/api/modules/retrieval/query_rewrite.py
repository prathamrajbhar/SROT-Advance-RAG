import json
from pathlib import Path
from typing import List
from core.models.factory import get_llm_client
from core.redis import get_redis


def load_query_rewrite_prompt() -> str:
    path = Path(__file__).resolve().parent.parent.parent / "core" / "prompts" / "v1" / "query_rewrite.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Rewrite the follow-up question given conversation history:\nHistory:\n{history}\nQuestion:\n{question}"


async def get_conversation_history_from_redis(conversation_id: str) -> List[dict]:
    redis_cli = await get_redis()
    raw_history = await redis_cli.lrange(f"conv:{conversation_id}:last_turns", 0, 5)
    history = []
    for item in raw_history:
        try:
            history.append(json.loads(item))
        except Exception:
            pass
    return history


async def rewrite_query_if_needed(conversation_id: str, new_question: str) -> str:
    history = await get_conversation_history_from_redis(conversation_id)
    if not history:
        return new_question

    formatted_history = "\n".join(
        [f"{turn.get('role', 'user').upper()}: {turn.get('content', '')}" for turn in history]
    )

    prompt_template = load_query_rewrite_prompt()
    prompt = prompt_template.format(history=formatted_history, question=new_question)

    llm = get_llm_client()
    try:
        response = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=256,
        )
        rewritten = response.content.strip().strip('"')
        return rewritten if rewritten else new_question
    except Exception:
        return new_question
