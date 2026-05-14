import asyncio
import os

import database
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_TEST_DB = "test_library.db"
_test_engine = create_async_engine(f"sqlite+aiosqlite:///{_TEST_DB}")
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)
database.engine = _test_engine  # patch before importing main

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from main import app
from database import get_db, Base
from models.book import Book
from models.user import User
from services import auth_service


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
    auth_service.clear_refresh_tokens()


async def _wipe():
    async with _TestSession() as session:
        await session.execute(delete(Book))
        await session.execute(delete(User))
        await session.commit()


# ── Auth helper fixtures ──────────────────────────────────────────────────────

ADMIN = {"username": "admin_test", "password": "admin123", "role": "admin"}
USER = {"username": "user_test", "password": "user123", "role": "user"}
SAMPLE_BOOK = {
    "title": "Kobzar", "author": "Taras Shevchenko",
    "description": "Poetry", "status": "available", "year": 1840,
}


def _register_and_login(client, creds: dict) -> dict:
    client.post("/auth/register", json=creds)
    resp = client.post("/auth/login", json={"username": creds["username"], "password": creds["password"]})
    return resp.json()


@pytest.fixture
def admin_tokens(client):
    return _register_and_login(client, ADMIN)


@pytest.fixture
def user_tokens(client):
    return _register_and_login(client, USER)


@pytest.fixture
def admin_headers(admin_tokens):
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


@pytest.fixture
def user_headers(user_tokens):
    return {"Authorization": f"Bearer {user_tokens['access_token']}"}
