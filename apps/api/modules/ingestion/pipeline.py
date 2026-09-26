import datetime
import uuid
from typing import Any, Dict, List
from qdrant_client.http import models as rest_models
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.factory import get_embedder
from core.qdrant import ensure_project_collection, upsert_chunks
from core.redis import get_redis
from models.document import Chunk, Document, IngestStatus
from modules.ingestion.chunker import chunk_elements
from modules.ingestion.parsers.media import parse_media
from modules.ingestion.parsers.pdf_docx import parse_docx, parse_pdf
from modules.ingestion.parsers.spreadsheet import parse_csv, parse_xlsx
from modules.ingestion.parsers.text_md import parse_text_markdown
from modules.ingestion.pii import scan_pii


async def process_document_ingestion(
    db: AsyncSession, document_id: uuid.UUID, file_bytes: bytes
) -> None:
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not doc:
        return

    redis_cli = await get_redis()
    doc_id_str = str(document_id)

    async def update_stage(stage: str, pct: int, detail: str) -> None:
        await redis_cli.hset(f"ingest:job:{doc_id_str}:progress", mapping={"stage": stage, "pct": pct, "detail": detail})
        await db.execute(update(Document).where(Document.id == document_id).values(status=IngestStatus(stage)))
        await db.commit()

    try:
        # 1. Parsing
        await update_stage("parsing", 15, f"Parsing {doc.filename}")
        mime = doc.mime_type.lower()
        filename = doc.filename.lower()

        if "pdf" in mime or filename.endswith(".pdf"):
            elements = parse_pdf(file_bytes)
        elif "wordprocessingml" in mime or "docx" in mime or filename.endswith((".docx", ".doc")):
            elements = parse_docx(file_bytes)
        elif "spreadsheet" in mime or "excel" in mime or filename.endswith((".xlsx", ".xls")):
            elements = parse_xlsx(file_bytes)
        elif "csv" in mime or filename.endswith(".csv"):
            elements = parse_csv(file_bytes)
        elif (
            any(audio_fmt in mime for audio_fmt in ["audio", "video", "mp4", "mp3", "wav", "m4a"])
            or filename.endswith((".mp3", ".mp4", ".wav", ".m4a"))
        ):
            elements = await parse_media(file_bytes, doc.filename)
        else:
            elements = parse_text_markdown(file_bytes, doc.filename)

        if not elements:
            raise ValueError("No extractable content found in file")

        # 2. Chunking & PII
        await update_stage("chunking", 40, "Creating parent-child chunks")
        chunks_data = chunk_elements(elements)
        full_text = " ".join([c["content"] for c in chunks_data])
        pii_flags, _ = scan_pii(full_text)

        # 3. Embedding
        await update_stage("embedding", 65, f"Embedding {len(chunks_data)} chunks")
        embedder = get_embedder()
        texts_to_embed = [c["content"] for c in chunks_data]
        embeddings = await embedder.embed_texts(texts_to_embed)

        # 4. Indexing (Postgres + Qdrant)
        await update_stage("indexing", 85, "Upserting vectors and search indices")
        await ensure_project_collection(str(doc.project_id), vector_dim=embedder.dimension)

        qdrant_points: List[rest_models.PointStruct] = []
        db_chunks: List[Chunk] = []

        for i, c_data in enumerate(chunks_data):
            embedding_id = uuid.uuid4()
            chunk_row = Chunk(
                id=c_data["id"],
                document_id=doc.id,
                project_id=doc.project_id,
                chunk_index=c_data["chunk_index"],
                parent_id=c_data["parent_id"],
                kind=c_data["kind"],
                token_count=c_data["token_count"],
                content=c_data["content"],
                locator=c_data["locator"],
                content_hash=c_data["content_hash"],
                embedding_id=embedding_id,
            )
            db_chunks.append(chunk_row)

            vector = embeddings[i] if i < len(embeddings) else [0.0] * embedder.dimension
            qdrant_points.append(
                rest_models.PointStruct(
                    id=str(embedding_id),
                    vector=vector,
                    payload={
                        "project_id": str(doc.project_id),
                        "document_id": str(doc.id),
                        "chunk_id": str(c_data["id"]),
                        "parent_id": str(c_data["parent_id"]) if c_data.get("parent_id") else None,
                        "kind": c_data["kind"],
                        "locator": c_data["locator"],
                        "content_hash": c_data["content_hash"],
                    },
                )
            )

        db.add_all(db_chunks)
        await db.flush()
        await upsert_chunks(str(doc.project_id), qdrant_points)

        # 5. Indexed
        now = datetime.datetime.now(datetime.timezone.utc)
        stats = {
            "chunk_count": len(chunks_data),
            "token_count": sum(c["token_count"] for c in chunks_data),
        }
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=IngestStatus.INDEXED,
                indexed_at=now,
                stats=stats,
                pii_flags=pii_flags,
                error_code=None,
                error_human=None,
            )
        )
        await db.commit()
        await redis_cli.hset(f"ingest:job:{doc_id_str}:progress", mapping={"stage": "indexed", "pct": 100, "detail": "Indexing complete"})

    except Exception as e:
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                status=IngestStatus.FAILED,
                error_code="PARSE_FAILED",
                error_human=str(e),
            )
        )
        await db.commit()
        await redis_cli.hset(f"ingest:job:{doc_id_str}:progress", mapping={"stage": "failed", "pct": 0, "detail": str(e)})
