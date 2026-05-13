import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "library")

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(MONGO_URL)


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def get_database() -> AsyncIOMotorDatabase:
    return _client[MONGO_DB_NAME]
