import base64
import hashlib
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from core.qdrant import delete_document_points
from core.redis import get_redis
from core.s3 import delete_s3_object, generate_presigned_url, upload_file_bytes
from models.document import Document, IngestStatus
from models.project import ProjectRole
from modules.documents.schemas import DocumentUploadItem
from modules.ingestion.tasks import ingest_document_task
from modules.projects.service import verify_project_access


async def upload_documents(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID, files: List[UploadFile]
) -> List[DocumentUploadItem]:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.EDITOR)
    upload_results: List[DocumentUploadItem] = []

    for file in files:
        content = await file.read()
        sha256_hash = hashlib.sha256(content).hexdigest()
        filename = file.filename or "unnamed_file"
        mime_type = file.content_type or "application/octet-stream"

        # Check existing deduplication
        stmt = select(Document).where(
            Document.project_id == project_id,
            Document.sha256 == sha256_hash,
            Document.status == IngestStatus.INDEXED,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            upload_results.append(
                DocumentUploadItem(
                    document_id=existing.id,
                    filename=filename,
                    sha256=sha256_hash,
                    status="indexed",
                    duplicate=True,
                    existing_document_id=existing.id,
                    note="Identical content already indexed",
                )
            )
            continue

        doc_id = uuid.uuid4()
        s3_key = f"projects/{project_id}/docs/{sha256_hash}/v1"
        await upload_file_bytes(s3_key, content, mime_type)

        doc = Document(
            id=doc_id,
            project_id=project_id,
            uploaded_by=user_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(content),
            sha256=sha256_hash,
            s3_key=s3_key,
            status=IngestStatus.QUEUED,
        )
        db.add(doc)
        await db.commit()

        # Enqueue background ingestion
        file_b64 = base64.b64encode(content).decode("utf-8")
        try:
            ingest_document_task.delay(str(doc_id), file_b64)
        except Exception:
            # If celery broker is offline, run inline async fallback
            from modules.ingestion.pipeline import process_document_ingestion
            import asyncio
            asyncio.create_task(process_document_ingestion(db, doc_id, content))

        upload_results.append(
            DocumentUploadItem(
                document_id=doc_id,
                filename=filename,
                sha256=sha256_hash,
                status="queued",
                duplicate=False,
            )
        )

    return upload_results


async def list_documents(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    status_filter: Optional[str] = None,
    query_str: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Document], int]:
    await verify_project_access(db, project_id, user_id)
    offset = (page - 1) * page_size

    stmt = select(Document).where(Document.project_id == project_id)
    if status_filter:
        stmt = stmt.where(Document.status == IngestStatus(status_filter))
    if query_str:
        stmt = stmt.where(Document.filename.ilike(f"%{query_str}%"))

    count_stmt = select(func.count(Document.id)).where(Document.project_id == project_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
    docs = (await db.execute(stmt)).scalars().all()
    return list(docs), total


async def get_document_status(
    db: AsyncSession, project_id: uuid.UUID, doc_id: uuid.UUID, user_id: uuid.UUID
) -> Dict[str, Any]:
    await verify_project_access(db, project_id, user_id)
    redis_cli = await get_redis()
    progress = await redis_cli.hgetall(f"ingest:job:{doc_id}:progress")
    if progress:
        return {
            "status": progress.get("stage", "queued"),
            "progress_pct": int(progress.get("pct", 0)),
            "stage_detail": progress.get("detail", ""),
        }

    stmt = select(Document).where(Document.id == doc_id, Document.project_id == project_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pct = 100 if doc.status == IngestStatus.INDEXED else (0 if doc.status == IngestStatus.FAILED else 50)
    return {"status": doc.status.value, "progress_pct": pct, "stage_detail": doc.error_human or doc.status.value}


async def get_document_content_url(
    db: AsyncSession, project_id: uuid.UUID, doc_id: uuid.UUID, user_id: uuid.UUID
) -> str:
    await verify_project_access(db, project_id, user_id)
    stmt = select(Document).where(Document.id == doc_id, Document.project_id == project_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return await generate_presigned_url(doc.s3_key, expires_in=300)


async def delete_document(
    db: AsyncSession, project_id: uuid.UUID, doc_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await verify_project_access(db, project_id, user_id, min_role=ProjectRole.EDITOR)
    stmt = select(Document).where(Document.id == doc_id, Document.project_id == project_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        return

    await delete_s3_object(doc.s3_key)
    await delete_document_points(str(project_id), str(doc_id))
    await db.execute(delete(Document).where(Document.id == doc_id))
    await db.commit()
