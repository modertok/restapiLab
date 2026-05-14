from fastapi.testclient import TestClient

SAMPLE_BOOK = {
    "title": "Kobzar", "author": "Taras Shevchenko",
    "description": "Poetry collection", "status": "available", "year": 1840,
}


# ── Authentication required ───────────────────────────────────────────────────

def test_get_books_without_token_returns_401(client: TestClient):
    assert client.get("/books/").status_code == 401


def test_get_book_by_id_without_token_returns_401(client: TestClient, admin_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.get(f"/books/{book['id']}").status_code == 401


def test_create_book_without_token_returns_401(client: TestClient):
    assert client.post("/books/", json=SAMPLE_BOOK).status_code == 401


def test_delete_book_without_token_returns_401(client: TestClient, admin_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.delete(f"/books/{book['id']}").status_code == 401


def test_invalid_token_returns_401(client: TestClient):
    headers = {"Authorization": "Bearer not.a.valid.token"}
    assert client.get("/books/", headers=headers).status_code == 401


# ── Authorization: admin vs user ──────────────────────────────────────────────

def test_admin_can_create_book(client: TestClient, admin_headers):
    assert client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).status_code == 201


def test_user_cannot_create_book_returns_403(client: TestClient, user_headers):
    assert client.post("/books/", json=SAMPLE_BOOK, headers=user_headers).status_code == 403


def test_admin_can_delete_book(client: TestClient, admin_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.delete(f"/books/{book['id']}", headers=admin_headers).status_code == 204


def test_user_cannot_delete_book_returns_403(client: TestClient, admin_headers, user_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.delete(f"/books/{book['id']}", headers=user_headers).status_code == 403


def test_admin_can_read_books(client: TestClient, admin_headers):
    assert client.get("/books/", headers=admin_headers).status_code == 200


def test_user_can_read_books(client: TestClient, user_headers):
    assert client.get("/books/", headers=user_headers).status_code == 200


def test_user_can_read_book_by_id(client: TestClient, admin_headers, user_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.get(f"/books/{book['id']}", headers=user_headers).status_code == 200


# ── POST /books/ — admin ──────────────────────────────────────────────────────

def test_create_book_returns_correct_data(client: TestClient, admin_headers):
    data = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert data["title"] == SAMPLE_BOOK["title"]
    assert data["author"] == SAMPLE_BOOK["author"]
    assert "id" in data


def test_create_book_generates_unique_ids(client: TestClient, admin_headers):
    r1 = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    r2 = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert r1["id"] != r2["id"]


def test_create_book_missing_title_returns_422(client: TestClient, admin_headers):
    assert client.post("/books/", json={k: v for k, v in SAMPLE_BOOK.items() if k != "title"}, headers=admin_headers).status_code == 422


def test_create_book_invalid_year_returns_422(client: TestClient, admin_headers):
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 999}, headers=admin_headers).status_code == 422


def test_create_book_invalid_status_returns_422(client: TestClient, admin_headers):
    assert client.post("/books/", json={**SAMPLE_BOOK, "status": "lost"}, headers=admin_headers).status_code == 422


# ── GET /books/ ───────────────────────────────────────────────────────────────

def test_get_books_returns_paginated_structure(client: TestClient, user_headers):
    data = client.get("/books/", headers=user_headers).json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0


def test_get_books_total_count(client: TestClient, admin_headers, user_headers):
    client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers)
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Book 2"}, headers=admin_headers)
    assert client.get("/books/", headers=user_headers).json()["total"] == 2


def test_filter_by_status(client: TestClient, admin_headers, user_headers):
    client.post("/books/", json={**SAMPLE_BOOK, "status": "available"}, headers=admin_headers)
    client.post("/books/", json={**SAMPLE_BOOK, "title": "B2", "status": "issued"}, headers=admin_headers)
    data = client.get("/books/?status=available", headers=user_headers).json()
    assert data["total"] == 1


def test_filter_by_author_case_insensitive(client: TestClient, admin_headers, user_headers):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"}, headers=admin_headers)
    client.post("/books/", json={**SAMPLE_BOOK, "title": "B2", "author": "Rowling"}, headers=admin_headers)
    assert client.get("/books/?author=tolkien", headers=user_headers).json()["total"] == 1


def test_sort_by_year(client: TestClient, admin_headers, user_headers):
    for year in [2005, 1990, 2020]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {year}", "year": year}, headers=admin_headers)
    items = client.get("/books/?sort_by=year", headers=user_headers).json()["items"]
    assert [b["year"] for b in items] == sorted([b["year"] for b in items])


def test_pagination(client: TestClient, admin_headers, user_headers):
    for i in range(5):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i}"}, headers=admin_headers)
    data = client.get("/books/?limit=3&offset=0", headers=user_headers).json()
    assert len(data["items"]) == 3
    assert data["total"] == 5


def test_pagination_invalid_limit_returns_422(client: TestClient, user_headers):
    assert client.get("/books/?limit=0", headers=user_headers).status_code == 422


# ── GET /books/{id} ───────────────────────────────────────────────────────────

def test_get_book_by_id_returns_200(client: TestClient, admin_headers, user_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.get(f"/books/{book['id']}", headers=user_headers).status_code == 200


def test_get_book_not_found_returns_404(client: TestClient, user_headers):
    assert client.get("/books/00000000-0000-0000-0000-000000000000", headers=user_headers).status_code == 404


# ── DELETE /books/{id} ────────────────────────────────────────────────────────

def test_delete_book_returns_204(client: TestClient, admin_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    assert client.delete(f"/books/{book['id']}", headers=admin_headers).status_code == 204


def test_delete_removes_book(client: TestClient, admin_headers, user_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    client.delete(f"/books/{book['id']}", headers=admin_headers)
    assert client.get(f"/books/{book['id']}", headers=user_headers).status_code == 404


def test_delete_idempotent(client: TestClient, admin_headers):
    book = client.post("/books/", json=SAMPLE_BOOK, headers=admin_headers).json()
    client.delete(f"/books/{book['id']}", headers=admin_headers)
    assert client.delete(f"/books/{book['id']}", headers=admin_headers).status_code == 204


def test_delete_nonexistent_returns_204(client: TestClient, admin_headers):
    assert client.delete("/books/00000000-0000-0000-0000-000000000000", headers=admin_headers).status_code == 204
