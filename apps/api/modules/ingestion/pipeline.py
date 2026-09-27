"""Document ingestion pipeline: parse → chunk → PII scan → embed → upsert.

Each stage is clearly separated. Failures are logged, the document is marked
FAILED in both Postgres and Redis, then the exception is re-raised so the
task queue (arq/Celery) records the failure correctly.

Idempotency: chunks with a content_hash that already exists for this document
are skipped — re-ingesting an unchanged document is a no-op.
"""
from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from qdrant_client.http import models as qdrant_models
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.models.factory import get_embedder
from core.qdrant import ensure_project_collection, upsert_chunks
from core.redis import get_redis
from models.document import Chunk, Document, IngestStatus
from modules.ingestion.chunker import ParsedElement, chunk_elements
from modules.ingestion.parsers.media import parse_image, parse_media
from modules.ingestion.parsers.pdf_docx import parse_docx, parse_pdf
from modules.ingestion.parsers.spreadsheet import parse_csv, parse_xlsx
from modules.ingestion.parsers.text_md import parse_text_markdown
from modules.ingestion.pii import scan_pii

logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Stage helper ─────────────────────────────────────────────────────────────


async def _set_stage(
    db: AsyncSession,
    redis_cli: Any,
    document_id: uuid.UUID,
    doc_id_str: str,
    stage: str,
    pct: int,
    detail: str,
    trace_id: str,
) -> None:
    await redis_cli.hset(
        f"ingest:job:{doc_id_str}:progress",
        mapping={"stage": stage, "pct": pct, "detail": detail},
    )
    await db.execute(
        update(Document)
        .where(Document.id == document_id)
        .values(status=IngestStatus(stage))
    )
    await db.commit()
    logger.info("ingest stage=%s pct=%d", stage, pct, extra={"trace_id": trace_id})


# ─── MIME routing ─────────────────────────────────────────────────────────────


async def _parse_file(
    file_bytes: bytes, mime: str, filename: str, doc_filename: str, doc_mime: str
) -> list[ParsedElement]:
    if "pdf" in mime or filename.endswith(".pdf"):
        return await parse_pdf(file_bytes)

    if "wordprocessingml" in mime or "docx" in mime or filename.endswith((".docx", ".doc")):
        return parse_docx(file_bytes)

    if "spreadsheet" in mime or "excel" in mime or filename.endswith((".xlsx", ".xls")):
        return parse_xlsx(file_bytes)

    if "csv" in mime or "tsv" in mime or "tab-separated" in mime or filename.endswith((".csv", ".tsv", ".tab")):
        return parse_csv(file_bytes)

    if any(f in mime for f in ("image", "png", "jpeg", "jpg", "webp", "gif", "bmp")) or \
       filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")):
        return await parse_image(file_bytes, doc_filename, doc_mime)

    if any(f in mime for f in ("audio", "video", "mp4", "mp3", "wav", "m4a", "webm", "ogg")) or \
       filename.endswith((".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg", ".mov", ".avi")):
        return await parse_media(file_bytes, doc_filename)

    return parse_text_markdown(file_bytes, doc_filename)


# ─── Pipeline ─────────────────────────────────────────────────────────────────


async def process_document_ingestion(
    db: AsyncSession,
    document_id: uuid.UUID,
    file_bytes: bytes,
) -> None:
    """Ingest a document: parse → chunk → PII scan → embed → index.

    On failure: marks the document FAILED, pushes the error to Redis,
    logs it, then re-raises so the task queue records the failure.
    """
    trace_id = uuid.uuid4().hex[:16]
    doc_id_str = str(document_id)

    doc = (
        await db.execute(select(Document).where(Document.id == document_id))
    ).scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document {document_id} not found — cannot ingest.")

    redis_cli = await get_redis()

    try:
        # ── 1. Parse ──────────────────────────────────────────────────────
        await _set_stage(db, redis_cli, document_id, doc_id_str, "parsing", 15, f"Parsing {doc.filename}", trace_id)

        elements = await _parse_file(
            file_bytes,
            mime=doc.mime_type.lower(),
            filename=doc.filename.lower(),
            doc_filename=doc.filename,
            doc_mime=doc.mime_type,
        )
        if not elements:
            raise ValueError(f"No extractable content found in '{doc.filename}'.")

        logger.info(
            "ingest: parsed %d elements from '%s'",
            len(elements), doc.filename,
            extra={"trace_id": trace_id},
        )

        # ── 2. Chunk + PII ────────────────────────────────────────────────
        await _set_stage(db, redis_cli, document_id, doc_id_str, "chunking", 40, "Chunking", trace_id)

        chunks_data = chunk_elements(elements)
        if not chunks_data:
            raise ValueError("Chunker produced zero chunks — cannot index an empty document.")

        pii_flags, _ = scan_pii(" ".join(c["content"] for c in chunks_data))

        # ── 3. Embed ──────────────────────────────────────────────────────
        await _set_stage(db, redis_cli, document_id, doc_id_str, "embedding", 65, f"Embedding {len(chunks_data)} chunks", trace_id)

        embedder = get_embedder()
        embeddings = await embedder.embed_texts([c["content"] for c in chunks_data])

        if len(embeddings) != len(chunks_data):
            raise RuntimeError(
                f"Embedder returned {len(embeddings)} vectors for {len(chunks_data)} chunks. "
                "This is a bug in the embedding service."
            )

        # ── 4. Idempotent upsert ──────────────────────────────────────────
        await _set_stage(db, redis_cli, document_id, doc_id_str, "indexing", 85, "Indexing", trace_id)

        await ensure_project_collection(str(doc.project_id), vector_dim=embedder.dimension)

        existing_hashes: set[str] = set(
            (await db.execute(
                select(Chunk.content_hash).where(Chunk.document_id == document_id)
            )).scalars().all()
        )

        new_chunks: list[Chunk] = []
        new_points: list[qdrant_models.PointStruct] = []

        for i, c in enumerate(chunks_data):
            if c["content_hash"] in existing_hashes:
                continue

            embedding_id = uuid.uuid4()
            new_chunks.append(Chunk(
                id=c["id"],
                document_id=doc.id,
                project_id=doc.project_id,
                chunk_index=c["chunk_index"],
                parent_id=c["parent_id"],
                kind=c["kind"],
                token_count=c["token_count"],
                content=c["content"],
                locator=c["locator"],
                content_hash=c["content_hash"],
                embedding_id=embedding_id,
            ))
            new_points.append(qdrant_models.PointStruct(
                id=str(embedding_id),
                vector=embeddings[i],
                payload={
                    "project_id": str(doc.project_id),
                    "document_id": str(doc.id),
                    "chunk_id": str(c["id"]),
                    "parent_id": str(c["parent_id"]) if c["parent_id"] else None,
                    "kind": c["kind"],
                    "locator": c["locator"],
                    "content_hash": c["content_hash"],
                },
            ))

        if new_chunks:
            db.add_all(new_chunks)
            await db.flush()
            await upsert_chunks(str(doc.project_id), new_points)

        skipped = len(chunks_data) - len(new_chunks)
        logger.info(
            "ingest: indexed %d new chunks, skipped %d duplicates",
            len(new_chunks), skipped,
            extra={"trace_id": trace_id},
        )

        # ── 5. Mark indexed ───────────────────────────────────────────────
        now = datetime.datetime.now(datetime.timezone.utc)
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=IngestStatus.INDEXED,
                indexed_at=now,
                stats={
                    "chunk_count": len(chunks_data),
                    "token_count": sum(c["token_count"] for c in chunks_data),
                    "skipped_duplicates": skipped,
                },
                pii_flags=pii_flags,
                error_code=None,
                error_human=None,
            )
        )
        await db.commit()
        await redis_cli.hset(
            f"ingest:job:{doc_id_str}:progress",
            mapping={"stage": "indexed", "pct": 100, "detail": "Complete"},
        )

    except Exception as exc:
        logger.error(
            "ingest FAILED for document %s: %s",
            doc_id_str, exc,
            exc_info=True,
            extra={"trace_id": trace_id},
        )
        try:
            await db.rollback()
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(
                    status=IngestStatus.FAILED,
                    error_code="INGEST_FAILED",
                    error_human=str(exc),
                )
            )
            await db.commit()
            await redis_cli.hset(
                f"ingest:job:{doc_id_str}:progress",
                mapping={"stage": "failed", "pct": 0, "detail": str(exc)},
            )
        except Exception as cleanup_exc:
            logger.error(
                "ingest: cleanup after failure also failed: %s",
                cleanup_exc,
                extra={"trace_id": trace_id},
            )
        raise
