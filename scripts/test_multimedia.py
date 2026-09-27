import asyncio
import hashlib
import uuid
from sqlalchemy import select
from core.database import async_session_factory
from core.models.factory import get_embedder
from core.qdrant import search_vectors
from core.s3 import upload_file_bytes
from models.auth import User
from models.document import Document, Chunk, IngestStatus
from models.project import Project, ProjectMember, ProjectRole
from modules.ingestion.pipeline import process_document_ingestion

# Minimal valid 1x1 PNG binary
PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa74e\xed\x00\x00\x00\x00IEND\xaeB`\x82"

# Minimal valid MP3 / Audio mock bytes
MP3_BYTES = b"ID3\x03\x00\x00\x00\x00\x00#TIT2\x00\x00\x00\x19\x00\x00All-Hands Q3 Keynote Recording\xff\xfb\x90d\x00\x00\x00\x00"

# Minimal valid MP4 / Video mock bytes
MP4_BYTES = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free\x00\x00\x00\x10mdatExecutive Townhall 2026"


async def test_multimedia_pipeline():
    async with async_session_factory() as db:
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one()

        project = Project(
            owner_id=user.id,
            name="Media & Vision Ingestion Verification",
            description="Live validation of Image, Audio and Video ingestion",
        )
        db.add(project)
        await db.flush()

        member = ProjectMember(project_id=project.id, user_id=user.id, role=ProjectRole.OWNER)
        db.add(member)
        await db.commit()

        print(f"=== Testing Multimedia Pipeline for Project: {project.id} ===\n")

        media_files = [
            ("architecture_diagram.png", "image/png", PNG_BYTES),
            ("presentation_slide.jpg", "image/jpeg", PNG_BYTES),
            ("townhall_keynote.mp4", "video/mp4", MP4_BYTES),
            ("podcast_interview.mp3", "audio/mpeg", MP3_BYTES),
        ]

        for fname, mime, content in media_files:
            sha = hashlib.sha256(content + str(uuid.uuid4()).encode()).hexdigest()
            s3_key = f"projects/{project.id}/raw/{fname}"
            await upload_file_bytes(s3_key, content, mime)

            doc_row = Document(
                project_id=project.id,
                uploaded_by=user.id,
                filename=fname,
                mime_type=mime,
                size_bytes=len(content),
                sha256=sha,
                s3_key=s3_key,
                status=IngestStatus.QUEUED,
            )
            db.add(doc_row)
            await db.flush()

            await process_document_ingestion(db, doc_row.id, content)

            updated = (await db.execute(select(Document).where(Document.id == doc_row.id))).scalar_one()
            print(f"  ✓ {fname:<30} | {mime:<12} | Status: {updated.status.value:<7} | Chunks: {updated.stats.get('chunk_count', 0)}")

        # Vector search validation
        embedder = get_embedder()
        queries = [
            "Search for architecture diagram image asset",
            "Find townhall keynote video recording and podcast interview",
        ]

        print("\n--- Semantic Vector Search on Multimedia Content ---")
        for q in queries:
            vec = (await embedder.embed_texts([q]))[0]
            pts = await search_vectors(str(project.id), vec, limit=1)
            hit = pts[0] if pts else None
            score = hit.score if hit else 0.0
            locator = hit.payload.get("locator") if hit else {}
            chunk_id = hit.payload.get("chunk_id") if hit else None

            # Retrieve text from db chunk
            chunk_db = (await db.execute(select(Chunk).where(Chunk.id == uuid.UUID(chunk_id)))).scalar_one_or_none() if chunk_id else None
            chunk_text = chunk_db.content if chunk_db else "N/A"

            print(f'  Query: "{q}"')
            print(f"  -> Hit Score: {score:.4f} | Locator: {locator} | Content: {chunk_text[:70]}...\n")


if __name__ == "__main__":
    asyncio.run(test_multimedia_pipeline())
