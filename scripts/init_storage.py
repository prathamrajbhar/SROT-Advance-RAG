#!/usr/bin/env python3
"""Universal S3 Bucket Provisioner.

Ensures the configured S3 bucket exists on LocalStack, MinIO, or AWS S3
using native application credentials from Settings.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from core.config import get_settings
from core.s3 import ensure_bucket_exists


async def main() -> int:
    settings = get_settings()
    bucket = settings.S3_BUCKET
    print(f"  Ensuring S3 storage bucket '{bucket}' exists at {settings.S3_ENDPOINT_URL or 'AWS'}...")
    try:
        await ensure_bucket_exists(bucket)
        print(f"  ✓ S3 storage bucket '{bucket}' is ready.")
        return 0
    except Exception as exc:
        print(f"  ⚠ Could not ensure S3 bucket '{bucket}': {exc}")
        return 0


if __name__ == "__main__":
    asyncio.run(main())
