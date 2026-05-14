"""
Integration tests against the running Prism mock server.
These tests are SKIPPED automatically if Prism is not running.

To run:  docker compose up -d  →  pytest tests/ -v
"""
import pytest
import requests

BASE = "http://localhost:4010"


# ── Auth mock ─────────────────────────────────────────────────────────────────

@pytest.mark.prism
def test_mock_login_returns_200():
    resp = requests.post(f"{BASE}/auth/login",
                         json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200


@pytest.mark.prism
def test_mock_login_response_has_tokens():
    resp = requests.post(f"{BASE}/auth/login",
                         json={"username": "admin", "password": "admin123"})
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # --dynamic mode generates random strings; just confirm field exists
    assert "token_type" in data


@pytest.mark.prism
def test_mock_register_returns_201():
    resp = requests.post(f"{BASE}/auth/register",
                         json={"username": "testuser", "password": "pass123"})
    assert resp.status_code == 201


@pytest.mark.prism
def test_mock_register_response_has_user_fields():
    resp = requests.post(f"{BASE}/auth/register",
                         json={"username": "testuser", "password": "pass123"})
    data = resp.json()
    assert "id" in data
    assert "username" in data
    assert "role" in data
    assert "is_active" in data


@pytest.mark.prism
def test_mock_refresh_returns_200():
    resp = requests.post(f"{BASE}/auth/refresh",
                         json={"refresh_token": "some.refresh.token"})
    assert resp.status_code == 200


@pytest.mark.prism
def test_mock_logout_returns_200():
    resp = requests.post(f"{BASE}/auth/logout",
                         json={"refresh_token": "some.refresh.token"})
    assert resp.status_code == 200


# ── Books mock ────────────────────────────────────────────────────────────────

@pytest.mark.prism
def test_mock_get_books_returns_200():
    resp = requests.get(f"{BASE}/books/",
                        headers={"Authorization": "Bearer fake.access.token"})
    assert resp.status_code == 200


@pytest.mark.prism
def test_mock_get_books_response_structure():
    resp = requests.get(f"{BASE}/books/",
                        headers={"Authorization": "Bearer fake.access.token"})
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


@pytest.mark.prism
def test_mock_get_books_items_is_list():
    resp = requests.get(f"{BASE}/books/",
                        headers={"Authorization": "Bearer fake.access.token"})
    assert isinstance(resp.json()["items"], list)


@pytest.mark.prism
def test_mock_create_book_returns_201():
    resp = requests.post(
        f"{BASE}/books/",
        json={"title": "Kobzar", "author": "Shevchenko", "year": 1840},
        headers={"Authorization": "Bearer fake.access.token"},
    )
    assert resp.status_code == 201


@pytest.mark.prism
def test_mock_create_book_response_has_id():
    resp = requests.post(
        f"{BASE}/books/",
        json={"title": "Kobzar", "author": "Shevchenko", "year": 1840},
        headers={"Authorization": "Bearer fake.access.token"},
    )
    data = resp.json()
    assert "id" in data
    assert "title" in data
    assert "author" in data
    assert "status" in data
    assert "year" in data


@pytest.mark.prism
def test_mock_get_book_by_id_returns_200():
    resp = requests.get(
        f"{BASE}/books/550e8400-e29b-41d4-a716-446655440001",
        headers={"Authorization": "Bearer fake.access.token"},
    )
    assert resp.status_code == 200


@pytest.mark.prism
def test_mock_delete_book_returns_204():
    resp = requests.delete(
        f"{BASE}/books/550e8400-e29b-41d4-a716-446655440001",
        headers={"Authorization": "Bearer fake.access.token"},
    )
    assert resp.status_code == 204


@pytest.mark.prism
def test_mock_get_books_with_limit_param():
    resp = requests.get(
        f"{BASE}/books/?limit=5",
        headers={"Authorization": "Bearer fake.access.token"},
    )
    assert resp.status_code == 200
    # --dynamic mode returns random integers; just check the field is present and is int
    assert isinstance(resp.json()["limit"], int)


@pytest.mark.prism
def test_mock_content_type_is_json():
    resp = requests.get(f"{BASE}/books/",
                        headers={"Authorization": "Bearer fake.access.token"})
    assert "application/json" in resp.headers.get("Content-Type", "")
