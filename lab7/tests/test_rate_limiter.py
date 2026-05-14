"""
Rate limiter tests — Sliding Window via Redis (mocked with fakeredis).

Required cases per the task:
  1. User has NOT reached the limit → 200
  2. User HAS reached the limit     → 429
Both for authenticated AND anonymous users.
"""
import asyncio
import time
import jwt
import pytest
from fastapi.testclient import TestClient


# ── Helper ────────────────────────────────────────────────────────────────────

async def _fill_rate_key(redis, key: str, count: int) -> None:
    """Pre-populate a Redis sorted-set key with `count` entries inside the window."""
    now = int(time.time())
    entries = {f"entry:{i}": float(now - i) for i in range(count)}
    await redis.zadd(key, entries)


# ── Anonymous user (identified by client IP = "testclient" in TestClient) ─────

def test_anonymous_under_limit_returns_not_429(client: TestClient):
    """Anonymous user — first request must NOT be rate-limited (Redis empty)."""
    resp = client.post("/auth/login", json={"username": "nobody", "password": "nobody"})
    # May be 401 (wrong credentials) but never 429 on the first request
    assert resp.status_code != 429


def test_anonymous_reaches_limit_returns_429(client: TestClient, fake_redis):
    """Anonymous user — 2 entries already in Redis → next request returns 429."""
    asyncio.run(_fill_rate_key(fake_redis, "rate_limit:testclient", 2))
    resp = client.post("/auth/login", json={"username": "nobody", "password": "nobody"})
    assert resp.status_code == 429


def test_anonymous_under_limit_one_entry_not_429(client: TestClient, fake_redis):
    """Anonymous user — only 1 entry (below limit of 2) → request goes through."""
    asyncio.run(_fill_rate_key(fake_redis, "rate_limit:testclient", 1))
    resp = client.post("/auth/login", json={"username": "nobody", "password": "nobody"})
    assert resp.status_code != 429


def test_anonymous_429_response_has_detail(client: TestClient, fake_redis):
    """429 response must contain a detail message."""
    asyncio.run(_fill_rate_key(fake_redis, "rate_limit:testclient", 2))
    resp = client.post("/auth/login", json={"username": "nobody", "password": "nobody"})
    assert resp.status_code == 429
    assert "detail" in resp.json()


def test_anonymous_429_response_has_retry_after_header(client: TestClient, fake_redis):
    """429 response must carry Retry-After header."""
    asyncio.run(_fill_rate_key(fake_redis, "rate_limit:testclient", 2))
    resp = client.post("/auth/login", json={"username": "nobody", "password": "nobody"})
    assert resp.status_code == 429
    assert "retry-after" in {h.lower() for h in resp.headers}


# ── Authenticated user (identified by user_id from JWT) ───────────────────────

def test_authenticated_under_limit_returns_200(client: TestClient, admin_headers):
    """Authenticated user — first request must return 200 (Redis empty)."""
    resp = client.get("/books/", headers=admin_headers)
    assert resp.status_code == 200


def test_authenticated_reaches_limit_returns_429(
    client: TestClient, admin_tokens, fake_redis
):
    """Authenticated user — 10 entries already in Redis → next request returns 429."""
    payload = jwt.decode(
        admin_tokens["access_token"], options={"verify_signature": False}
    )
    user_id = payload["sub"]

    asyncio.run(_fill_rate_key(fake_redis, f"rate_limit:{user_id}", 10))

    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    resp = client.get("/books/", headers=headers)
    assert resp.status_code == 429


def test_authenticated_under_limit_nine_entries_not_429(
    client: TestClient, admin_tokens, fake_redis
):
    """Authenticated user — 9 entries (below limit of 10) → request passes."""
    payload = jwt.decode(
        admin_tokens["access_token"], options={"verify_signature": False}
    )
    user_id = payload["sub"]

    asyncio.run(_fill_rate_key(fake_redis, f"rate_limit:{user_id}", 9))

    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    resp = client.get("/books/", headers=headers)
    assert resp.status_code == 200


def test_authenticated_429_response_has_detail(
    client: TestClient, admin_tokens, fake_redis
):
    """429 response for authenticated user must contain detail message."""
    payload = jwt.decode(
        admin_tokens["access_token"], options={"verify_signature": False}
    )
    user_id = payload["sub"]
    asyncio.run(_fill_rate_key(fake_redis, f"rate_limit:{user_id}", 10))

    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    resp = client.get("/books/", headers=headers)
    assert resp.status_code == 429
    assert "detail" in resp.json()


# ── Isolation between identities ──────────────────────────────────────────────

def test_different_users_do_not_share_counters(
    client: TestClient, admin_tokens, user_tokens, fake_redis
):
    """Each user has an independent rate-limit counter."""
    admin_id = jwt.decode(
        admin_tokens["access_token"], options={"verify_signature": False}
    )["sub"]

    # Fill admin's bucket to the limit
    asyncio.run(_fill_rate_key(fake_redis, f"rate_limit:{admin_id}", 10))

    # Admin is blocked
    admin_h = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    assert client.get("/books/", headers=admin_h).status_code == 429

    # User is NOT blocked (separate counter)
    user_h = {"Authorization": f"Bearer {user_tokens['access_token']}"}
    assert client.get("/books/", headers=user_h).status_code == 200


# ── Counter increments on each allowed request ────────────────────────────────

def test_counter_increments_after_each_request(
    client: TestClient, admin_headers, admin_tokens, fake_redis
):
    """Each successful request adds exactly one entry to the Redis sorted set."""
    payload = jwt.decode(
        admin_tokens["access_token"], options={"verify_signature": False}
    )
    user_id = payload["sub"]
    key = f"rate_limit:{user_id}"

    async def _count():
        return await fake_redis.zcard(key)

    initial = asyncio.run(_count())
    client.get("/books/", headers=admin_headers)
    assert asyncio.run(_count()) == initial + 1


# ── Limit values sanity check ─────────────────────────────────────────────────

def test_anonymous_limit_is_2(client: TestClient, fake_redis):
    """Exactly 2 requests allowed for anonymous; 3rd is blocked."""
    for i in range(2):
        resp = client.post("/auth/login", json={"username": "x", "password": "x"})
        assert resp.status_code != 429
    assert client.post("/auth/login", json={"username": "x", "password": "x"}).status_code == 429


def test_authenticated_limit_is_10(client: TestClient, admin_tokens, fake_redis):
    """Exactly 10 requests allowed for authenticated users; 11th is blocked."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    for i in range(10):
        resp = client.get("/books/", headers=headers)
        assert resp.status_code == 200
    assert client.get("/books/", headers=headers).status_code == 429
