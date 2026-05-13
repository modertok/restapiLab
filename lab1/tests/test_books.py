import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.book import books_db

client = TestClient(app)

SAMPLE_BOOK = {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "description": "A novel about the American Dream",
    "status": "available",
    "year": 1925,
}


@pytest.fixture(autouse=True)
def clear_db():
    books_db.clear()
    yield
    books_db.clear()


# ── POST /books/ ──────────────────────────────────────────────────────────────

def test_create_book_returns_201():
    response = client.post("/books/", json=SAMPLE_BOOK)
    assert response.status_code == 201


def test_create_book_returns_correct_data():
    response = client.post("/books/", json=SAMPLE_BOOK)
    data = response.json()
    assert data["title"] == SAMPLE_BOOK["title"]
    assert data["author"] == SAMPLE_BOOK["author"]
    assert data["year"] == SAMPLE_BOOK["year"]
    assert data["status"] == "available"
    assert data["description"] == SAMPLE_BOOK["description"]


def test_create_book_generates_uuid():
    r1 = client.post("/books/", json=SAMPLE_BOOK).json()
    r2 = client.post("/books/", json=SAMPLE_BOOK).json()
    assert "id" in r1
    assert len(r1["id"]) == 36  # UUID format
    assert r1["id"] != r2["id"]


def test_create_book_default_status():
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "status"}
    response = client.post("/books/", json=book)
    assert response.status_code == 201
    assert response.json()["status"] == "available"


def test_create_book_issued_status():
    book = {**SAMPLE_BOOK, "status": "issued"}
    response = client.post("/books/", json=book)
    assert response.status_code == 201
    assert response.json()["status"] == "issued"


def test_create_book_without_description():
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "description"}
    response = client.post("/books/", json=book)
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_book_missing_title_returns_422():
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "title"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_missing_author_returns_422():
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "author"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_missing_year_returns_422():
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "year"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_empty_title_returns_422():
    assert client.post("/books/", json={**SAMPLE_BOOK, "title": ""}).status_code == 422


def test_create_book_empty_author_returns_422():
    assert client.post("/books/", json={**SAMPLE_BOOK, "author": ""}).status_code == 422


def test_create_book_year_too_low_returns_422():
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 999}).status_code == 422


def test_create_book_year_too_high_returns_422():
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 2101}).status_code == 422


def test_create_book_invalid_status_returns_422():
    assert client.post("/books/", json={**SAMPLE_BOOK, "status": "lost"}).status_code == 422


# ── GET /books/ ───────────────────────────────────────────────────────────────

def test_get_all_books_empty_returns_200():
    response = client.get("/books/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_books_returns_all():
    client.post("/books/", json=SAMPLE_BOOK)
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Another Book"})
    response = client.get("/books/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_filter_by_status_available():
    client.post("/books/", json={**SAMPLE_BOOK, "status": "available"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Issued", "status": "issued"})
    data = client.get("/books/?status=available").json()
    assert len(data) == 1
    assert data[0]["status"] == "available"


def test_filter_by_status_issued():
    client.post("/books/", json={**SAMPLE_BOOK, "status": "issued"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Available", "status": "available"})
    data = client.get("/books/?status=issued").json()
    assert len(data) == 1
    assert data[0]["status"] == "issued"


def test_filter_by_author_exact():
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "HP", "author": "Rowling"})
    data = client.get("/books/?author=Tolkien").json()
    assert len(data) == 1
    assert data[0]["author"] == "Tolkien"


def test_filter_by_author_case_insensitive():
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"})
    data = client.get("/books/?author=tolkien").json()
    assert len(data) == 1


def test_filter_by_author_partial():
    client.post("/books/", json={**SAMPLE_BOOK, "author": "John Ronald Reuel Tolkien"})
    data = client.get("/books/?author=tolkien").json()
    assert len(data) == 1


def test_filter_no_match_returns_empty():
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?author=Unknown Author XYZ").json()
    assert data == []


def test_sort_by_title():
    for title in ["Zebra", "Apple", "Mango"]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": title})
    data = client.get("/books/?sort_by=title").json()
    titles = [b["title"] for b in data]
    assert titles == sorted(titles, key=str.lower)


def test_sort_by_year():
    for year in [2005, 1990, 2020]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {year}", "year": year})
    data = client.get("/books/?sort_by=year").json()
    years = [b["year"] for b in data]
    assert years == sorted(years)


def test_sort_by_invalid_field_returns_422():
    assert client.get("/books/?sort_by=invalid").status_code == 422


def test_combined_filter_and_sort():
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Z Book", "author": "Tolkien", "year": 2000, "status": "available"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "A Book", "author": "Tolkien", "year": 1990, "status": "available"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "M Book", "author": "Rowling", "year": 1995, "status": "available"})
    data = client.get("/books/?author=tolkien&sort_by=year").json()
    assert len(data) == 2
    assert data[0]["year"] < data[1]["year"]


# ── GET /books/{id} ───────────────────────────────────────────────────────────

def test_get_book_by_id_returns_200():
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    response = client.get(f"/books/{created['id']}")
    assert response.status_code == 200


def test_get_book_by_id_returns_correct_data():
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    data = client.get(f"/books/{created['id']}").json()
    assert data["id"] == created["id"]
    assert data["title"] == SAMPLE_BOOK["title"]


def test_get_book_by_id_not_found_returns_404():
    response = client.get("/books/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_book_by_id_404_has_detail():
    response = client.get("/books/00000000-0000-0000-0000-000000000000")
    assert "detail" in response.json()


# ── DELETE /books/{id} ────────────────────────────────────────────────────────

def test_delete_existing_book_returns_204():
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    response = client.delete(f"/books/{created['id']}")
    assert response.status_code == 204


def test_delete_removes_book_from_list():
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    client.delete(f"/books/{created['id']}")
    assert client.get(f"/books/{created['id']}").status_code == 404


def test_delete_idempotent_second_call_returns_204():
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    client.delete(f"/books/{created['id']}")
    response = client.delete(f"/books/{created['id']}")
    assert response.status_code == 204


def test_delete_nonexistent_returns_204():
    response = client.delete("/books/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 204


def test_delete_does_not_affect_other_books():
    b1 = client.post("/books/", json=SAMPLE_BOOK).json()
    b2 = client.post("/books/", json={**SAMPLE_BOOK, "title": "Book 2"}).json()
    client.delete(f"/books/{b1['id']}")
    assert client.get(f"/books/{b2['id']}").status_code == 200
