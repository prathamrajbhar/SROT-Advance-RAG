import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, Any
import redis.asyncio as aioredis
from core.config import get_settings

logger = logging.getLogger("srot.events")


def get_document_channel(document_id: str) -> str:
    return f"channel:document:{document_id}:progress"


async def publish_document_progress(
    document_id: str,
    stage: str,
    progress_percent: int,
    message: str = "",
    metadata: Dict[str, Any] = None,
) -> None:
    """Publishes a real-time progress event to Redis Pub/Sub for SSE streaming."""
    settings = get_settings()
    channel = get_document_channel(document_id)
    payload = {
        "document_id": str(document_id),
        "stage": stage,
        "progress_percent": max(0, min(100, progress_percent)),
        "message": message,
        "metadata": metadata or {},
        "timestamp": time.time(),
    }
    encoded = json.dumps(payload)

    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.publish(channel, encoded)
        logger.debug(f"Published progress to {channel}: {stage} ({progress_percent}%)")
    except Exception as e:
        logger.warning(f"Failed to publish progress to Redis: {e}")
    finally:
        await client.aclose()


async def stream_document_events(document_id: str) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE formatted event lines from Redis Pub/Sub."""
    settings = get_settings()
    channel_name = get_document_channel(document_id)
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()

    try:
        await pubsub.subscribe(channel_name)
        # Yield initial connection confirmation
        initial_event = json.dumps({
            "document_id": str(document_id),
            "stage": "CONNECTED",
            "progress_percent": 0,
            "message": "Connected to real-time ingestion stream",
            "timestamp": time.time(),
        })
        yield f"event: progress\ndata: {initial_event}\n\n"

        while True:
            try:
                # Poll with 15s timeout to allow sending SSE heartbeats
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if msg and msg.get("type") == "message":
                    data_str = msg["data"]
                    yield f"event: progress\ndata: {data_str}\n\n"
                    # If document processing is complete or failed, close the stream gracefully
                    parsed = json.loads(data_str)
                    if parsed.get("stage") in ["READY", "FAILED", "COMPLETED"]:
                        break
                else:
                    # SSE keep-alive heartbeat comment
                    yield ": ping\n\n"
            except asyncio.CancelledError:
                break
    except Exception as e:
        logger.error(f"Error in SSE stream for {document_id}: {e}")
        error_event = json.dumps({"document_id": str(document_id), "stage": "ERROR", "message": str(e)})
        yield f"event: error\ndata: {error_event}\n\n"
    finally:
        await pubsub.unsubscribe(channel_name)
        await client.aclose()
