from typing import Any, Dict, List
from core.models.factory import get_whisper


async def parse_media(content_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    whisper_client = get_whisper()
    segments = await whisper_client.transcribe(content_bytes, filename)
    elements: List[Dict[str, Any]] = []

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        start_s = float(seg.get("start", 0.0))
        end_s = float(seg.get("end", start_s + 5.0))
        elements.append({
            "kind": "transcript_segment",
            "content": text,
            "locator": {
                "start_s": start_s,
                "end_s": end_s,
            },
        })

    return elements
