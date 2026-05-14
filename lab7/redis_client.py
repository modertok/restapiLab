import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_client: aioredis.Redis | None = None


async def connect_redis() -> None:
    global _client
    _client = aioredis.from_url(REDIS_URL, decode_responses=True)


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def get_redis_client() -> aioredis.Redis:
    return _client
