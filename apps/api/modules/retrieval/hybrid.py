"""Hybrid retrieval: parallel Qdrant dense search + Postgres BM25, fused with RRF.

Dense path:   project_id filter is applied inside Qdrant's query_filter so
              filtering happens at the index layer — not post-retrieval.

BM25 path:    ts_rank_cd provides a proper rank score for each matching chunk
              rather than a boolean hit set, enabling true rank-based fusion.

Embedding:    EMBEDDING_QUERY_PREFIX is prepended to the query text (e.g.
              "query: " for BGE/E5 models). Set to "" in config for plain models.

RRF fusion:   score(d) = Σ 1 / (k + rank_i(d)) with k = RRF_K from config.

Debug:        every call returns bm25_ids, dense_ids, fused_ids, and per-source
              rank maps so callers can inspect the full fusion decision.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.models.factory import get_embedder
from core.qdrant import search_vectors
from models.document import Chunk
from modules.retrieval.constants import DEFAULT_HYBRID_TOP_K, RRF_K_CONSTANT

logger = logging.getLogger(__name__)
settings = get_settings()


# ─── BM25 ─────────────────────────────────────────────────────────────────────

_BM25_SQL = text(
    """
    SELECT
        c.id,
        ts_rank_cd(c.ftsv, q.query) AS bm_rank
    FROM chunks c
    JOIN documents d ON c.document_id = d.id,
         plainto_tsquery('english', :query_text) AS q(query)
    WHERE d.project_id = :project_id
      AND d.status     = 'indexed'
      AND c.ftsv       @@ q.query
    ORDER BY bm_rank DESC
    LIMIT :limit
    """
)


async def _bm25_search(
    db: AsyncSession,
    project_id: uuid.UUID,
    query: str,
    limit: int,
) -> list[uuid.UUID]:
    """Return chunk IDs ranked by Postgres ts_rank_cd (best first)."""
    rows = (
        await db.execute(
            _BM25_SQL,
            {
                "query_text": query,
                "project_id": str(project_id),
                "limit": limit,
            },
        )
    ).fetchall()
    return [uuid.UUID(str(row[0])) for row in rows]


# ─── Dense ────────────────────────────────────────────────────────────────────


async def _dense_search(
    project_id: uuid.UUID,
    query: str,
    limit: int,
) -> list[uuid.UUID]:
    """Embed query, search Qdrant with project_id filter at the index layer."""
    embedder = get_embedder()
    prefix = settings.EMBEDDING_QUERY_PREFIX
    query_text = f"{prefix}{query}" if prefix else query

    embeddings = await embedder.embed_texts([query_text])
    if not embeddings:
        raise RuntimeError("Embedder returned no vectors for the query.")

    points = await search_vectors(str(project_id), embeddings[0], limit=limit)

    ids: list[uuid.UUID] = []
    for point in points:
        raw_id = (point.payload or {}).get("chunk_id")
        if raw_id:
            ids.append(uuid.UUID(str(raw_id)))
    return ids


# ─── RRF fusion ───────────────────────────────────────────────────────────────


def _rrf_fuse(
    ranked_lists: list[list[uuid.UUID]],
    k: int,
    top_n: int,
) -> list[uuid.UUID]:
    """Reciprocal Rank Fusion: score(d) = Σ 1 / (k + rank_i(d)), rank 1-based."""
    scores: dict[uuid.UUID, float] = {}
    for ranked in ranked_lists:
        for rank_zero, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank_zero + 1)
    return sorted(scores, key=lambda d: scores[d], reverse=True)[:top_n]


# ─── Public API ───────────────────────────────────────────────────────────────


async def hybrid_retrieve(
    db: AsyncSession,
    project_id: uuid.UUID,
    query: str,
    top_k: int = DEFAULT_HYBRID_TOP_K,
) -> tuple[list[Chunk], dict[str, Any]]:
    """Run BM25 + dense in parallel, fuse with RRF, return ordered Chunks.

    Returns
    -------
    chunks : list[Chunk]
        Fused and ordered by RRF score, length ≤ top_k.
    debug : dict
        bm25_ids, dense_ids, fused_ids, bm25_ranks, dense_ranks for inspection.
    """
    bm25_ids, dense_ids = await asyncio.gather(
        _bm25_search(db, project_id, query, limit=top_k),
        _dense_search(project_id, query, limit=top_k),
    )

    logger.info(
        "hybrid_retrieve: bm25=%d dense=%d project=%s",
        len(bm25_ids), len(dense_ids), project_id,
    )

    fused_ids = _rrf_fuse([bm25_ids, dense_ids], k=RRF_K_CONSTANT, top_n=top_k)

    debug: dict[str, Any] = {
        "bm25_ids": [str(i) for i in bm25_ids],
        "dense_ids": [str(i) for i in dense_ids],
        "fused_ids": [str(i) for i in fused_ids],
        "bm25_ranks": {str(cid): rank for rank, cid in enumerate(bm25_ids)},
        "dense_ranks": {str(cid): rank for rank, cid in enumerate(dense_ids)},
    }

    if not fused_ids:
        logger.info("hybrid_retrieve: no results for project=%s", project_id)
        return [], debug

    fetched: list[Chunk] = list(
        (await db.execute(select(Chunk).where(Chunk.id.in_(fused_ids)))).scalars().all()
    )
    chunk_map: dict[uuid.UUID, Chunk] = {c.id: c for c in fetched}
    ordered = [chunk_map[cid] for cid in fused_ids if cid in chunk_map]

    return ordered, debug
