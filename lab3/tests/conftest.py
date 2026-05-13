import asyncio
import os

# Patch the database engine BEFORE importing main so the lifespan uses SQLite
import database
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_TEST_DB = "test_library.db"
_test_engine = create_async_engine(f"sqlite+aiosqlite:///{_TEST_DB}")
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)

database.engine = _test_engine

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from main import app
from database import get_db, Base
from models.book import Book


async def _override_get_db():
    async with _TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session", autouse=True)
def client():
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    with TestClient(app) as c:
        yield c
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


@pytest.fixture(autouse=True)
def clean_db(client):
    yield
    asyncio.run(_wipe())


async def _wipe():
    async with _TestSession() as session:
        await session.execute(delete(Book))
        await session.commit()
