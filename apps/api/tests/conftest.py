import asyncio
import os
import pytest
from httpx import ASGITransport, AsyncClient
from main import app

os.environ["ENVIRONMENT"] = "testing"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
