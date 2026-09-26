import pytest
from sqlalchemy import text
from core.config import get_settings
from core.database import async_session_factory
from core.s3 import (
    delete_s3_object,
    ensure_bucket_exists,
    get_s3_client_kwargs,
    session,
    upload_file_bytes,
)

settings = get_settings()


@pytest.mark.asyncio
async def test_postgres_connectivity():
    async with async_session_factory() as db_session:
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_s3_bucket_operations():
    kwargs = get_s3_client_kwargs()
    async with session.client(**kwargs) as s3:
        await ensure_bucket_exists(settings.S3_BUCKET)
        test_key = "pytest-connectivity-test.txt"
        test_payload = b"connectivity ok"
        await upload_file_bytes(
            test_key,
            test_payload,
            "text/plain",
            bucket_name=settings.S3_BUCKET,
        )

        response = await s3.get_object(Bucket=settings.S3_BUCKET, Key=test_key)
        data = await response["Body"].read()
        assert data == test_payload

        await delete_s3_object(test_key, bucket_name=settings.S3_BUCKET)


@pytest.mark.asyncio
async def test_gemini_generation():
    if not settings.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not configured")
    from core.models.providers.gemini_provider import GeminiProvider

    model_name = settings.LLM_MODEL if settings.LLM_PROVIDER == "gemini" else "gemini-3.8-flash"
    llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=model_name)
    response = await llm.generate(
        messages=[{"role": "user", "content": "Respond with: PONG"}],
        temperature=0.0,
        max_tokens=256,
    )
    assert response.content is not None
    assert len(response.content.strip()) > 0
    assert "PONG" in response.content.upper()
