import os
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("ENVIRONMENT", "test")


import models  # noqa: F401 - Ensure all models are registered on Base.metadata
from core.config import get_settings  # noqa: E402
from core.database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

settings = get_settings()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Isolated transactional session per test against PostgreSQL."""
    connect_args = {}
    if "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL:
        connect_args["ssl"] = False

    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        connect_args=connect_args,
    )

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        yield session

        await session.close()
        await transaction.rollback()

    await engine.dispose()



@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
