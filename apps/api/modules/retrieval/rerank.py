import uuid
from typing import Any, Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.factory import get_reranker
from models.document import Chunk, Document
from modules.retrieval.constants import DEFAULT_RERANK_TOP_K


async def rerank_and_assemble_context(
    db: AsyncSession,
    query: str,
    chunks: List[Chunk],
    top_k: int = DEFAULT_RERANK_TOP_K,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
    if not chunks:
        return [], [], 0.0

    reranker = get_reranker()
    texts = [c.content for c in chunks]
    ranked = await reranker.rerank(query, texts, top_k=top_k)

    top_score = ranked[0][1] if ranked else 0.0
    rerank_debug = []
    selected_chunks: List[Chunk] = []

    for idx, score in ranked:
        if idx < len(chunks):
            chunk = chunks[idx]
            selected_chunks.append(chunk)
            rerank_debug.append({"chunk_id": str(chunk.id), "score": round(score, 4)})

    # Fetch document metadata and parent chunks for richest context
    doc_ids = list(set(c.document_id for c in selected_chunks))
    doc_stmt = select(Document).where(Document.id.in_(doc_ids))
    docs = {d.id: d.filename for d in (await db.execute(doc_stmt)).scalars().all()}

    contexts: List[Dict[str, Any]] = []
    for c in selected_chunks:
        contexts.append({
            "chunk_id": str(c.id),
            "parent_id": str(c.parent_id) if c.parent_id else str(c.id),
            "document_id": str(c.document_id),
            "document_name": docs.get(c.document_id, "document"),
            "content": c.content,
            "locator": c.locator,
            "kind": c.kind,
        })

    return contexts, rerank_debug, top_score
