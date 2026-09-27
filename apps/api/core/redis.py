import asyncio
from typing import Dict
import redis.asyncio as aioredis
from core.config import get_settings

settings = get_settings()

_redis_clients: Dict[int, aioredis.Redis] = {}


async def get_redis() -> aioredis.Redis:
    try:
        loop = asyncio.get_running_loop()
        loop_id = id(loop)
    except RuntimeError:
        loop_id = 0

    client = _redis_clients.get(loop_id)
    if client is None:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        _redis_clients[loop_id] = client
    return client


async def close_redis() -> None:
    for client in list(_redis_clients.values()):
        try:
            await client.close()
        except Exception:
            pass
    _redis_clients.clear()
