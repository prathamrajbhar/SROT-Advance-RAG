import uuid
from typing import Any, Dict, List, Tuple
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.factory import get_embedder
from core.qdrant import search_vectors
from models.document import Chunk, Document, IngestStatus
from modules.retrieval.constants import DEFAULT_HYBRID_TOP_K, RRF_K_CONSTANT


async def search_bm25_sparse(
    db: AsyncSession, project_id: uuid.UUID, query: str, limit: int = DEFAULT_HYBRID_TOP_K
) -> List[Chunk]:
    stmt = (
        select(Chunk)
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            Document.status == IngestStatus.INDEXED,
            text("chunks.ftsv @@ plainto_tsquery('english', :query_text)"),
        )
        .params(query_text=query)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def search_dense_vector(
    project_id: uuid.UUID, query: str, limit: int = DEFAULT_HYBRID_TOP_K
) -> List[Dict[str, Any]]:
    embedder = get_embedder()
    query_embeddings = await embedder.embed_texts([query])
    if not query_embeddings:
        return []

    points = await search_vectors(str(project_id), query_embeddings[0], limit=limit)
    results: List[Dict[str, Any]] = []
    for p in points:
        payload = p.payload or {}
        results.append({
            "chunk_id": uuid.UUID(payload["chunk_id"]),
            "document_id": uuid.UUID(payload["document_id"]),
            "parent_id": (
                uuid.UUID(payload["parent_id"])
                if payload.get("parent_id") and payload["parent_id"] != "None"
                else None
            ),
            "kind": payload.get("kind", "text"),
            "locator": payload.get("locator"),
            "score": p.score,
        })
    return results


async def hybrid_retrieve(
    db: AsyncSession, project_id: uuid.UUID, query: str, top_k: int = DEFAULT_HYBRID_TOP_K
) -> Tuple[List[Chunk], Dict[str, Any]]:
    sparse_chunks = await search_bm25_sparse(db, project_id, query, limit=top_k)
    dense_results = await search_dense_vector(project_id, query, limit=top_k)

    bm25_ids = [c.id for c in sparse_chunks]
    dense_ids = [d["chunk_id"] for d in dense_results]

    rrf_scores: Dict[uuid.UUID, float] = {}
    for rank, cid in enumerate(bm25_ids):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K_CONSTANT + rank + 1))
    for rank, cid in enumerate(dense_ids):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K_CONSTANT + rank + 1))

    fused_sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

    if not fused_sorted_ids:
        # Fallback to any indexed chunks in the project for small/empty keyword matches
        fallback_stmt = (
            select(Chunk)
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.project_id == project_id, Document.status == IngestStatus.INDEXED)
            .limit(top_k)
        )
        fallback_chunks = list((await db.execute(fallback_stmt)).scalars().all())
        return fallback_chunks, {
            "bm25_ids": [str(i) for i in bm25_ids],
            "dense_ids": [str(i) for i in dense_ids],
            "fused_ids": [str(c.id) for c in fallback_chunks],
        }

    stmt = select(Chunk).where(Chunk.id.in_(fused_sorted_ids))
    fetched_chunks = list((await db.execute(stmt)).scalars().all())
    chunk_map = {c.id: c for c in fetched_chunks}
    ordered_chunks = [chunk_map[cid] for cid in fused_sorted_ids if cid in chunk_map]

    debug_info = {
        "bm25_ids": [str(i) for i in bm25_ids],
        "dense_ids": [str(i) for i in dense_ids],
        "fused_ids": [str(i) for i in fused_sorted_ids],
    }
    return ordered_chunks, debug_info
