"""Follow-up query rewriting via the configured LLM.

If conversation history exists in Redis, the user's follow-up question is
rewritten into a standalone search query so retrieval has full context.

Guarantees:
* Deterministic: temperature=0, max_tokens=120.
* One-sentence output validated non-empty.
* On ANY failure (LLM error, empty output, network): log a WARNING and
  return the original raw query.  **Never blocks the request.**
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

from core.config import get_settings
from core.models.factory import get_llm_client
from core.redis import get_redis

logger = logging.getLogger(__name__)
settings = get_settings()

_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "core"
    / "prompts"
    / "v1"
    / "query_rewrite.txt"
)

_INLINE_PROMPT = (
    "Given the conversation history below, rewrite the follow-up question into a "
    "single standalone search query. Output only the query.\n\n"
    "History ({n_turns} turns):\n{history}\n\n"
    "Follow-up Question:\n{question}\n\n"
    "Rewritten Search Query:"
)


def _load_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        logger.warning("query_rewrite: prompt file not found at %s, using inline default", _PROMPT_PATH)
        return _INLINE_PROMPT


_PROMPT_TEMPLATE: str = _load_prompt()


async def _fetch_history(conversation_id: str) -> List[dict]:
    """Fetch last N turns from Redis key ``conv:{id}:last_turns``."""
    n_turns = settings.QUERY_REWRITE_LAST_N_TURNS
    redis_cli = await get_redis()
    # Each turn is 2 entries (user + assistant); fetch 2×N from the tail.
    raw_items = await redis_cli.lrange(
        f"conv:{conversation_id}:last_turns", -(n_turns * 2), -1
    )
    history: List[dict] = []
    for item in raw_items:
        try:
            history.append(json.loads(item))
        except (json.JSONDecodeError, TypeError):
            continue
    return history


def _format_history(turns: List[dict]) -> str:
    lines: List[str] = []
    for turn in turns:
        role = turn.get("role", "user").upper()
        content = turn.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _is_valid_rewrite(text: str) -> bool:
    """Accept non-empty single-sentence responses (strip trailing punctuation noise)."""
    cleaned = text.strip().strip('"').strip("'").strip()
    return bool(cleaned) and len(cleaned.split()) >= 2  # at least 2 words


async def rewrite_query_if_needed(
    conversation_id: str,
    new_question: str,
) -> str:
    """Return a standalone search query.

    If history is empty or any step fails, returns *new_question* unchanged.
    Never raises.
    """
    try:
        history = await _fetch_history(conversation_id)
    except Exception as exc:
        logger.warning(
            "query_rewrite: failed to fetch history for conv=%s: %s",
            conversation_id,
            exc,
            extra={"conversation_id": conversation_id},
        )
        return new_question

    if not history:
        return new_question

    formatted = _format_history(history)
    n_turns = settings.QUERY_REWRITE_LAST_N_TURNS
    prompt = _PROMPT_TEMPLATE.format(
        history=formatted,
        question=new_question,
        n_turns=n_turns,
    )

    try:
        llm = get_llm_client()
        response = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=120,
        )
        rewritten = response.content.strip().strip('"').strip("'").strip()

        if not _is_valid_rewrite(rewritten):
            logger.warning(
                "query_rewrite: LLM returned invalid output %r for conv=%s — using original",
                rewritten[:80],
                conversation_id,
                extra={"conversation_id": conversation_id},
            )
            return new_question

        logger.info(
            "query_rewrite: '%s' → '%s' (conv=%s)",
            new_question[:60],
            rewritten[:60],
            conversation_id,
        )
        return rewritten

    except Exception as exc:
        logger.warning(
            "query_rewrite: LLM call failed for conv=%s: %s — using original query",
            conversation_id,
            exc,
            extra={"conversation_id": conversation_id},
        )
        return new_question
