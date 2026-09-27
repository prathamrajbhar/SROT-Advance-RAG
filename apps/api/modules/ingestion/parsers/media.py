from typing import Any, Dict, List
from core.models.factory import get_whisper
from modules.ingestion.ocr import extract_ocr_text


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


async def parse_image(
    content_bytes: bytes, filename: str, mime_type: str = "image/png"
) -> List[Dict[str, Any]]:
    ocr_text = extract_ocr_text(content_bytes)
    elements: List[Dict[str, Any]] = []

    if ocr_text:
        paragraphs = [p.strip() for p in ocr_text.split("\n\n") if p.strip()]
        for p in paragraphs:
            elements.append({
                "kind": "text",
                "content": p,
                "locator": {"filename": filename, "format": mime_type},
            })
    else:
        elements.append({
            "kind": "image_description",
            "content": f"Image document: {filename} ({len(content_bytes)} bytes, format: {mime_type})",
            "locator": {"filename": filename, "format": mime_type},
        })

    return elements
