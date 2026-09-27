"""Media (audio/video) and image parsers returning typed ParsedElement objects.

Audio/video → Whisper transcription → ``transcript_segment`` elements.
Image       → OCR text             → ``paragraph`` elements.
             (no OCR text)         → ``image_description`` placeholder.
"""
from __future__ import annotations

import logging
from typing import List

from core.models.factory import get_whisper
from modules.ingestion.chunker import ParsedElement
from modules.ingestion.ocr import extract_ocr_text

logger = logging.getLogger(__name__)


async def parse_media(content_bytes: bytes, filename: str) -> List[ParsedElement]:
    """Transcribe audio/video via Whisper; emit one element per segment."""
    whisper_client = get_whisper()
    segments = await whisper_client.transcribe(content_bytes, filename)
    elements: List[ParsedElement] = []

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        start_s = float(seg.get("start", 0.0))
        end_s = float(seg.get("end", start_s + 5.0))
        elements.append(ParsedElement(
            kind="transcript_segment",
            content=text,
            locator={"start_s": start_s, "end_s": end_s},
        ))

    logger.debug(
        "parse_media: '%s' → %d transcript_segment elements", filename, len(elements)
    )
    return elements


async def parse_image(
    content_bytes: bytes,
    filename: str,
    mime_type: str = "image/png",
) -> List[ParsedElement]:
    """OCR an image; fall back to a descriptive placeholder if no text found."""
    ocr_text = extract_ocr_text(content_bytes)
    elements: List[ParsedElement] = []

    if ocr_text:
        paragraphs = [p.strip() for p in ocr_text.split("\n\n") if p.strip()]
        for para in paragraphs:
            elements.append(ParsedElement(
                kind="paragraph",
                content=para,
                locator={"filename": filename, "format": mime_type},
            ))
    else:
        elements.append(ParsedElement(
            kind="image_description",
            content=(
                f"Image document: {filename} "
                f"({len(content_bytes)} bytes, format: {mime_type})"
            ),
            locator={"filename": filename, "format": mime_type},
        ))

    logger.debug(
        "parse_image: '%s' → %d elements (ocr=%s)",
        filename,
        len(elements),
        bool(ocr_text),
    )
    return elements
