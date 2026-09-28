import asyncio
import json
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from core.events import publish_document_progress, stream_document_events
from main import app


@pytest.mark.asyncio
async def test_publish_document_progress():
    doc_id = str(uuid.uuid4())
    # Should not raise exception
    await publish_document_progress(
        document_id=doc_id,
        stage="EXTRACTING",
        progress_percent=45,
        message="Parsing PDF structure...",
    )


@pytest.mark.asyncio
async def test_sse_stream_receives_redis_events():
    doc_id = str(uuid.uuid4())
    generator = stream_document_events(doc_id)

    # First event should be connection confirmation
    first_chunk = await anext(generator)
    assert "event: progress" in first_chunk
    assert "CONNECTED" in first_chunk

    # Concurrently publish a progress update
    async def publish_later():
        await asyncio.sleep(0.1)
        await publish_document_progress(
            document_id=doc_id,
            stage="READY",
            progress_percent=100,
            message="Document indexed successfully",
        )

    task = asyncio.create_task(publish_later())

    # Wait for the published READY event, skipping any keep-alive pings
    received_event = None
    for _ in range(20):
        chunk = await anext(generator)
        if "event: progress" in chunk and "READY" in chunk:
            received_event = chunk
            break
        await asyncio.sleep(0.05)

    await task
    assert received_event is not None
    assert "READY" in received_event
    assert "100" in received_event

