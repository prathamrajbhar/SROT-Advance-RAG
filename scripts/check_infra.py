#!/usr/bin/env python3
"""Infrastructure Service Prober.

Checks whether PostgreSQL, Redis, Qdrant, and S3 Storage are reachable on the host
or configured endpoints without requiring Docker.
"""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
API_DIR = ROOT_DIR / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from core.config import get_settings


def check_tcp_port(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_postgres(db_url: str) -> bool:
    try:
        parsed = urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        return check_tcp_port(host, port)
    except Exception:
        return False


def check_redis(redis_url: str) -> bool:
    try:
        parsed = urlparse(redis_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        return check_tcp_port(host, port)
    except Exception:
        return False


def check_qdrant(qdrant_url: str) -> bool:
    try:
        endpoint = f"{qdrant_url.rstrip('/')}/readyz"
        res = httpx.get(endpoint, timeout=2.0)
        return res.status_code == 200
    except Exception:
        try:
            parsed = urlparse(qdrant_url)
            return check_tcp_port(parsed.hostname or "localhost", parsed.port or 6333)
        except Exception:
            return False


def check_s3(s3_url: str | None) -> bool:
    if not s3_url:
        return True
    try:
        parsed = urlparse(s3_url)
        return check_tcp_port(parsed.hostname or "localhost", parsed.port or 4566)
    except Exception:
        return False


def main() -> int:
    settings = get_settings()

    postgres_ok = check_postgres(settings.DATABASE_URL)
    redis_ok = check_redis(settings.REDIS_URL)
    qdrant_ok = check_qdrant(settings.QDRANT_URL)
    s3_ok = check_s3(settings.S3_ENDPOINT_URL)

    status = {
        "postgres": postgres_ok,
        "redis": redis_ok,
        "qdrant": qdrant_ok,
        "localstack": s3_ok,
    }

    if "--missing" in sys.argv:
        missing = [svc for svc, ok in status.items() if not ok]
        print(" ".join(missing))
        return 0

    if "--json" in sys.argv:
        print(json.dumps(status))
        return 0

    print("  Service Discovery:")
    print(f"    • PostgreSQL : {'✓ Active (Host/Local)' if postgres_ok else '✗ Not running'}")
    print(f"    • Redis      : {'✓ Active (Host/Local)' if redis_ok else '✗ Not running'}")
    print(f"    • Qdrant     : {'✓ Active (Host/Local)' if qdrant_ok else '✗ Not running'}")
    print(f"    • S3 Storage : {'✓ Active (Host/Local)' if s3_ok else '✗ Not running'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
