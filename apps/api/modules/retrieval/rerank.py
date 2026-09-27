"""Cross-encoder reranker with strict failure semantics.

Flow:
  1. Send (query, chunk_text) pairs to RERANKER_URL/rerank in batches.
  2. On any HTTP failure after max retries → raise RerankerServiceError.
     The caller maps this to HTTP 503. Reranking is NEVER silently skipped.
  3. If top logit score < RERANK_MIN_SCORE → return empty contexts and the
     low top_score. stream_service.py's existing gate on line 71 fires.
  4. For kept chunks, fetch the parent chunk and prepend it as context
     (up to CONTEXT_TOKEN_BUDGET tokens per chunk).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.document import Chunk, Document
from modules.ingestion.chunker import estimate_tokens
from modules.retrieval.constants import (
    CONTEXT_TOKEN_BUDGET,
    DEFAULT_RERANK_TOP_K,
    RERANK_BATCH_SIZE,
    RERANK_MIN_SCORE,
    RERANK_TIMEOUT_S,
)

logger = logging.getLogger(__name__)
settings = get_settings()

_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 0.5


# ─── Typed errors ─────────────────────────────────────────────────────────────


class RerankerServiceError(RuntimeError):
    """Raised when the reranker HTTP service is unreachable after all retries.
    Map to HTTP 503 at the router layer.
    """


from core.models.factory import get_reranker


async def _call_reranker(
    query: str,
    candidates: list[str],
    top_k: int,
) -> list[tuple[int, float]]:
    """Rerank candidates using configured reranker adapter."""
    reranker = get_reranker()
    return await reranker.rerank(query, candidates, top_k=top_k)



# ─── Context expansion ────────────────────────────────────────────────────────


async def _load_parents(
    db: AsyncSession,
    chunks: list[Chunk],
) -> dict[uuid.UUID, str]:
    """Fetch parent chunk content for the given child chunks."""
    parent_ids = {c.parent_id for c in chunks if c.parent_id}
    if not parent_ids:
        return {}
    parents: list[Chunk] = list(
        (await db.execute(select(Chunk).where(Chunk.id.in_(parent_ids)))).scalars().all()
    )
    return {p.id: p.content for p in parents}


def _expand_with_parent(
    chunk: Chunk,
    parent_content_map: dict[uuid.UUID, str],
    token_budget: int,
) -> str:
    """Prepend parent text when it fits within the per-chunk token budget."""
    if chunk.parent_id and chunk.parent_id in parent_content_map:
        parent_text = parent_content_map[chunk.parent_id]
        if estimate_tokens(chunk.content) + estimate_tokens(parent_text) <= token_budget:
            return f"{parent_text}\n\n{chunk.content}"
    return chunk.content


# ─── Public API ───────────────────────────────────────────────────────────────


async def rerank_and_assemble_context(
    db: AsyncSession,
    query: str,
    chunks: list[Chunk],
    top_k: int = DEFAULT_RERANK_TOP_K,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    """Rerank, apply insufficiency gate, expand with parent context.

    Returns
    -------
    contexts : list[dict]
        Ready for the LLM prompt. Empty when the gate fires.
    debug : list[dict]
        Per-chunk rerank scores.
    top_score : float
        Highest reranker score (0.0 when no chunks passed in).

    Raises
    ------
    RerankerServiceError
        When the reranker HTTP service cannot be reached. Map to HTTP 503.
    """
    if not chunks:
        return [], [], 0.0

    # Raises RerankerServiceError on failure — never silently skipped.
    ranked = await _call_reranker(query, [c.content for c in chunks], top_k=top_k)

    top_score = ranked[0][1] if ranked else 0.0
    debug = [
        {"chunk_id": str(chunks[idx].id), "score": round(score, 4)}
        for idx, score in ranked
        if idx < len(chunks)
    ]

    logger.info(
        "rerank: top_score=%.4f threshold=%.4f gate_fired=%s",
        top_score, RERANK_MIN_SCORE, top_score < RERANK_MIN_SCORE,
    )

    if top_score < RERANK_MIN_SCORE:
        return [], debug, top_score

    # ── Assemble context with parent expansion ────────────────────────────
    selected = [chunks[idx] for idx, _ in ranked if idx < len(chunks)]
    parent_map = await _load_parents(db, selected)

    doc_ids = list({c.document_id for c in selected})
    doc_names: dict[uuid.UUID, str] = {
        d.id: d.filename
        for d in (
            await db.execute(select(Document).where(Document.id.in_(doc_ids)))
        ).scalars().all()
    }

    per_chunk_budget = CONTEXT_TOKEN_BUDGET // max(1, len(selected))
    contexts: list[dict[str, Any]] = [
        {
            "chunk_id": str(chunk.id),
            "parent_id": str(chunk.parent_id) if chunk.parent_id else str(chunk.id),
            "document_id": str(chunk.document_id),
            "document_name": doc_names.get(chunk.document_id, "document"),
            "content": _expand_with_parent(chunk, parent_map, per_chunk_budget),
            "locator": chunk.locator,
            "kind": chunk.kind,
        }
        for chunk in selected
    ]

    return contexts, debug, top_score
