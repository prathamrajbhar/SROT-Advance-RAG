"""Enterprise Whisper ASR Adapter for audio/video transcription via local microservice."""
from __future__ import annotations

import logging
from typing import Any, Dict, List
import httpx
from core.config import get_settings
from core.models.base import BaseWhisper

logger = logging.getLogger(__name__)
settings = get_settings()


class WhisperAdapter(BaseWhisper):
    def __init__(self) -> None:
        self.whisper_url = settings.WHISPER_URL

    async def transcribe(
        self, audio_bytes: bytes, filename: str
    ) -> List[Dict[str, Any]]:
        headers = {"X-Internal-Token": settings.INTERNAL_MODEL_TOKEN}
        files = {"file": (filename, audio_bytes, "audio/mpeg")}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(
                    f"{self.whisper_url.rstrip('/')}/transcribe",
                    headers=headers,
                    files=files,
                )
                res.raise_for_status()
                return res.json().get("segments", [])
        except Exception as exc:
            logger.error("Whisper transcription failed for %s: %s", filename, exc)
            raise RuntimeError(f"Whisper ASR service at {self.whisper_url} failed: {exc}")
