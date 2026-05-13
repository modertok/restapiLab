import asyncio
import os

# ── Patch the database engine BEFORE importing main ──────────────────────────
# Tests use SQLite (no Docker required); engine is replaced at module level so
# the lifespan's `database.engine.begin()` automatically uses the test engine.
import database
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_TEST_DB = "test_library.db"
_test_engine = create_async_engine(f"sqlite+aiosqlite:///{_TEST_DB}")
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)

database.engine = _test_engine  # lifespan will use this engine

# ── Now it's safe to import the app ──────────────────────────────────────────
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
    """Session-scoped TestClient. Lifespan creates SQLite tables on startup."""
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    with TestClient(app) as c:
        yield c
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


@pytest.fixture(autouse=True)
def clean_db(client):
    """Wipe all books after every test to keep tests independent."""
    yield
    asyncio.run(_wipe())


async def _wipe():
    async with _TestSession() as session:
        await session.execute(delete(Book))
        await session.commit()
