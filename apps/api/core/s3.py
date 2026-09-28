import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
import boto3
from botocore.config import Config
from core.config import get_settings

logger = logging.getLogger("srot.s3")


class S3StorageManager:
    """Manages AWS S3 Direct-to-Storage presigned multipart lifecycle."""

    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.S3_BUCKET_NAME
        self.expiry = settings.S3_PRESIGNED_EXPIRY_SECONDS

        boto_config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
        )

        client_kwargs: Dict[str, Any] = {
            "service_name": "s3",
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "config": boto_config,
        }
        if settings.S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

        self.client = boto3.client(**client_kwargs)

    def generate_s3_key(self, tenant_id: str, workspace_id: str, filename: str) -> str:
        safe_filename = filename.replace(" ", "_")
        unique_prefix = uuid.uuid4().hex[:12]
        return f"{tenant_id}/{workspace_id}/raw/{unique_prefix}_{safe_filename}"

    def initiate_multipart_upload(
        self,
        tenant_id: str,
        workspace_id: str,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> Tuple[str, str]:
        s3_key = self.generate_s3_key(tenant_id, workspace_id, filename)
        logger.info(f"Initiating S3 multipart upload for key: {s3_key}")
        response = self.client.create_multipart_upload(
            Bucket=self.bucket,
            Key=s3_key,
            ContentType=content_type,
        )
        upload_id = response["UploadId"]
        return upload_id, s3_key

    def generate_presigned_part_url(
        self,
        s3_key: str,
        upload_id: str,
        part_number: int,
    ) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket": self.bucket,
                "Key": s3_key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=self.expiry,
        )

    def generate_presigned_part_urls(
        self,
        s3_key: str,
        upload_id: str,
        part_numbers: List[int],
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for part_num in part_numbers:
            url = self.generate_presigned_part_url(s3_key, upload_id, part_num)
            results.append({"part_number": part_num, "presigned_url": url})
        return results

    def complete_multipart_upload(
        self,
        s3_key: str,
        upload_id: str,
        parts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        sorted_parts = sorted(
            [{"PartNumber": int(p["part_number"]), "ETag": p["etag"].strip('"')} for p in parts],
            key=lambda x: x["PartNumber"],
        )
        logger.info(f"Completing S3 multipart upload for key: {s3_key} with {len(sorted_parts)} parts")
        return self.client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": sorted_parts},
        )

    def abort_multipart_upload(self, s3_key: str, upload_id: str) -> None:
        logger.warning(f"Aborting S3 multipart upload for key: {s3_key}")
        try:
            self.client.abort_multipart_upload(
                Bucket=self.bucket,
                Key=s3_key,
                UploadId=upload_id,
            )
        except Exception as e:
            logger.error(f"Failed to abort multipart upload {upload_id}: {e}")

    def ensure_bucket_cors(self) -> bool:
        """Enforces browser CORS configuration on the S3 bucket for multipart uploads."""
        cors_rules = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": ["ETag", "x-amz-request-id", "x-amz-id-2"],
                    "MaxAgeSeconds": 3600,
                }
            ]
        }
        try:
            self.client.put_bucket_cors(Bucket=self.bucket, CORSConfiguration=cors_rules)
            logger.info(f"Configured S3 CORS policy on bucket '{self.bucket}'")
            return True
        except Exception as exc:
            logger.warning(f"Could not configure S3 CORS on bucket '{self.bucket}': {exc}")
            return False


@lru_cache()
def get_s3_manager() -> S3StorageManager:
    return S3StorageManager()
