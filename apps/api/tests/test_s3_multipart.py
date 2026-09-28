import uuid
import pytest
from botocore.stub import Stubber
from httpx import ASGITransport, AsyncClient
from core.s3 import get_s3_manager
from main import app


@pytest.fixture
def stubbed_s3():
    manager = get_s3_manager()
    with Stubber(manager.client) as stubber:
        yield stubber


@pytest.mark.asyncio
async def test_s3_multipart_full_lifecycle(db_session, stubbed_s3):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Setup workspace first
        setup_res = await client.post(
            "/api/v1/onboarding/workspace",
            json={
                "tenant_name": "S3 Enterprise Corp",
                "tenant_slug": f"s3-corp-{uuid.uuid4().hex[:6]}",
                "workspace_name": "S3 Test Workspace",
                "admin_email": "admin@s3corp.io",
            },
        )
        assert setup_res.status_code == 200
        workspace_id = setup_res.json()["workspace_id"]

        # Stub S3 create_multipart_upload
        upload_id = "test-upload-id-9988"
        stubbed_s3.add_response(
            "create_multipart_upload",
            {"Bucket": "srot-enterprise-multimodal", "Key": "placeholder", "UploadId": upload_id},
        )

        # 2. Initiate multipart upload for a 25MB PDF (should calculate 3 parts of 10MB)
        file_size = 25 * 1024 * 1024
        init_res = await client.post(
            "/api/v1/documents/multipart/initiate",
            json={
                "workspace_id": workspace_id,
                "filename": "quarterly_earnings_2026.pdf",
                "file_size_bytes": file_size,
                "content_type": "application/pdf",
            },
        )
        assert init_res.status_code == 200
        init_data = init_res.json()
        assert init_data["upload_id"] == upload_id
        assert init_data["total_parts"] == 3
        assert init_data["chunk_size_bytes"] == 10 * 1024 * 1024
        document_id = init_data["document_id"]
        s3_key = init_data["s3_key"]

        # 3. Presign URLs for all 3 parts
        presign_res = await client.post(
            "/api/v1/documents/multipart/presign-parts",
            json={
                "document_id": document_id,
                "upload_id": upload_id,
                "s3_key": s3_key,
                "part_numbers": [1, 2, 3],
            },
        )
        assert presign_res.status_code == 200
        presign_data = presign_res.json()
        assert len(presign_data["parts"]) == 3
        for item in presign_data["parts"]:
            assert "X-Amz-Signature" in item["presigned_url"]
            assert f"partNumber={item['part_number']}" in item["presigned_url"]

        # Stub S3 complete_multipart_upload
        bucket_name = get_s3_manager().bucket
        stubbed_s3.add_response(
            "complete_multipart_upload",
            {
                "Location": f"https://s3.amazonaws.com/{bucket_name}/{s3_key}",
                "Bucket": bucket_name,
                "Key": s3_key,
                "ETag": '"final-merged-etag"',
            },
            expected_params={
                "Bucket": bucket_name,
                "Key": s3_key,
                "UploadId": upload_id,
                "MultipartUpload": {
                    "Parts": [
                        {"PartNumber": 1, "ETag": "etag-part-1"},
                        {"PartNumber": 2, "ETag": "etag-part-2"},
                        {"PartNumber": 3, "ETag": "etag-part-3"},
                    ]
                },
            },
        )

        # 4. Complete upload
        comp_res = await client.post(
            "/api/v1/documents/multipart/complete",
            json={
                "document_id": document_id,
                "upload_id": upload_id,
                "s3_key": s3_key,
                "parts": [
                    {"part_number": 3, "etag": "etag-part-3"},
                    {"part_number": 1, "etag": "etag-part-1"},
                    {"part_number": 2, "etag": "etag-part-2"},
                ],
            },
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["status"] == "UPLOADED"
        assert comp_data["processing_job_id"] is not None

        # 5. List documents in workspace
        list_res = await client.get(f"/api/v1/documents?workspace_id={workspace_id}")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] == 1
        assert list_data["documents"][0]["filename"] == "quarterly_earnings_2026.pdf"
        assert list_data["documents"][0]["file_type"] == "document"
        assert list_data["documents"][0]["status"] in ("UPLOADED", "PROCESSING", "READY")

        # 6. Delete document
        del_res = await client.delete(f"/api/v1/documents/{document_id}")
        assert del_res.status_code == 204

        # Verify list is empty
        list_after = await client.get(f"/api/v1/documents?workspace_id={workspace_id}")
        assert list_after.json()["total"] == 0
