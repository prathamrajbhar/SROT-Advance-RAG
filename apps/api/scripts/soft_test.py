import asyncio
import os
import sys
import time
import urllib.request
from typing import Tuple

# Ensure apps/api is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.config import get_settings
from core.database import engine
from core.s3 import get_s3_manager


async def test_postgresql_health() -> Tuple[bool, str, float]:
    """Tests live PostgreSQL connectivity, version probe, and schema availability."""
    start_time = time.perf_counter()
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT current_database(), current_user, version();")
            )
            row = result.fetchone()
            if not row:
                return False, "Failed to fetch PostgreSQL system details", 0.0

            db_name, db_user, version_string = row[0], row[1], row[2]

            table_query = await connection.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
            )
            table_count = table_query.scalar() or 0

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            summary = (
                f"Connected to DB '{db_name}' as user '{db_user}' "
                f"({table_count} tables detected, PG: {version_string.split()[1]})"
            )
            return True, summary, elapsed_ms
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return False, f"PostgreSQL Error: {str(exc)}", elapsed_ms


def test_s3_health() -> Tuple[bool, str, float]:
    """Tests live S3 connectivity and executes a presigned multipart upload roundtrip."""
    start_time = time.perf_counter()
    s3_manager = get_s3_manager()
    test_tenant_id = "diagnostic-tenant"
    test_workspace_id = "diagnostic-workspace"
    test_filename = "soft_test_probe.txt"
    test_payload = b"SROT Enterprise Multimodal RAG Ingestion Pipeline Probe"

    try:
        # 1. Bucket existence verification
        existing_buckets = [b["Name"] for b in s3_manager.client.list_buckets().get("Buckets", [])]
        if s3_manager.bucket not in existing_buckets:
            s3_manager.client.create_bucket(Bucket=s3_manager.bucket)

        # 2. Initiate multipart upload
        upload_id, s3_key = s3_manager.initiate_multipart_upload(
            tenant_id=test_tenant_id,
            workspace_id=test_workspace_id,
            filename=test_filename,
            content_type="text/plain",
        )

        # 3. Generate presigned URL for part 1
        part_urls = s3_manager.generate_presigned_part_urls(s3_key, upload_id, [1])
        upload_target_url = part_urls[0]["presigned_url"]

        # 4. Upload part via direct HTTP PUT
        request = urllib.request.Request(upload_target_url, data=test_payload, method="PUT")
        with urllib.request.urlopen(request) as http_response:
            part_etag = (http_response.headers.get("ETag") or "").strip('"')

        # 5. Complete multipart upload
        s3_manager.complete_multipart_upload(
            s3_key=s3_key,
            upload_id=upload_id,
            parts=[{"part_number": 1, "etag": part_etag}],
        )

        # 6. Read back and verify content integrity
        download_object = s3_manager.client.get_object(Bucket=s3_manager.bucket, Key=s3_key)
        downloaded_content = download_object["Body"].read()
        if downloaded_content != test_payload:
            return False, "S3 downloaded content mismatch", 0.0

        # 7. Clean up test object
        s3_manager.client.delete_object(Bucket=s3_manager.bucket, Key=s3_key)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        summary = (
            f"Bucket '{s3_manager.bucket}' verified. "
            f"Presigned multipart upload + verification roundtrip succeeded."
        )
        return True, summary, elapsed_ms
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return False, f"S3 Error: {str(exc)}", elapsed_ms


async def run_soft_test() -> int:
    settings = get_settings()
    print("=" * 70)
    print("SROT ENTERPRISE INFRASTRUCTURE DIAGNOSTIC SOFT TEST")
    print("=" * 70)
    print(f"DATABASE_URL   : {settings.DATABASE_URL.split('@')[-1]}")
    print(f"S3_ENDPOINT_URL: {settings.S3_ENDPOINT_URL or 'AWS Default'}")
    print(f"S3_BUCKET_NAME : {settings.S3_BUCKET_NAME}")
    print(f"AWS_REGION     : {settings.AWS_REGION}")
    print("-" * 70)

    pg_healthy, pg_msg, pg_ms = await test_postgresql_health()
    pg_status = "PASS" if pg_healthy else "FAIL"
    print(f"[{pg_status}] PostgreSQL ({pg_ms:.1f}ms): {pg_msg}")

    s3_healthy, s3_msg, s3_ms = test_s3_health()
    s3_status = "PASS" if s3_healthy else "FAIL"
    print(f"[{s3_status}] AWS S3 Storage ({s3_ms:.1f}ms): {s3_msg}")
    print("=" * 70)

    if pg_healthy and s3_healthy:
        print("ALL INFRASTRUCTURE SUBSYSTEMS ARE FUNCTIONAL AND OPERATIONAL!")
        return 0
    print("INFRASTRUCTURE VERIFICATION FAILED FOR ONE OR MORE SUBSYSTEMS.")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_soft_test())
    sys.exit(exit_code)
