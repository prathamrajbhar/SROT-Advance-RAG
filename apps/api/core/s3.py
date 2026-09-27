from typing import Optional
import aioboto3
from botocore.config import Config
from core.config import get_settings

settings = get_settings()

session = aioboto3.Session()


def get_s3_client_kwargs() -> dict:
    region_name = settings.S3_REGION or settings.AWS_DEFAULT_REGION or "us-east-1"
    access_key = settings.S3_ACCESS_KEY or settings.AWS_ACCESS_KEY_ID or "test"
    secret_key = settings.S3_SECRET_KEY or settings.AWS_SECRET_ACCESS_KEY or "test"
    endpoint_url = settings.S3_ENDPOINT_URL or settings.AWS_ENDPOINT_URL

    kwargs = {
        "service_name": "s3",
        "region_name": region_name,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "config": Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
    }
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return kwargs


async def ensure_bucket_exists(bucket_name: Optional[str] = None) -> None:
    target_bucket = bucket_name or settings.S3_BUCKET
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        try:
            await s3.head_bucket(Bucket=target_bucket)
        except Exception:
            try:
                await s3.create_bucket(Bucket=target_bucket)
            except Exception:
                pass


async def upload_file_bytes(
    key: str, data: bytes, content_type: str, bucket_name: Optional[str] = None
) -> str:
    target_bucket = bucket_name or settings.S3_BUCKET
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        await s3.put_object(
            Bucket=target_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    return key


async def download_file_bytes(
    key: str, bucket_name: Optional[str] = None
) -> bytes:
    target_bucket = bucket_name or settings.S3_BUCKET
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        res = await s3.get_object(Bucket=target_bucket, Key=key)
        async with res["Body"] as stream:
            return await stream.read()


async def generate_presigned_url(
    key: str, expires_in: int = 300, bucket_name: Optional[str] = None
) -> str:
    target_bucket = bucket_name or settings.S3_BUCKET
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": target_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    return str(url)


async def delete_s3_object(
    key: str, bucket_name: Optional[str] = None
) -> None:
    target_bucket = bucket_name or settings.S3_BUCKET
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        try:
            await s3.delete_object(Bucket=target_bucket, Key=key)
        except Exception:
            pass


async def delete_s3_prefix(
    prefix: str, bucket_name: Optional[str] = None
) -> None:
    target_bucket = bucket_name or settings.S3_BUCKET
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        paginator = s3.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=target_bucket, Prefix=prefix):
            if "Contents" in page:
                delete_keys = [{"Key": obj["Key"]} for obj in page["Contents"]]
                await s3.delete_objects(
                    Bucket=target_bucket,
                    Delete={"Objects": delete_keys},
                )
