from fastapi.testclient import TestClient

SAMPLE_BOOK = {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "description": "A novel about the American Dream",
    "status": "available",
    "year": 1925,
}


# ── POST /books/ ──────────────────────────────────────────────────────────────

def test_create_book_returns_201(client: TestClient):
    assert client.post("/books/", json=SAMPLE_BOOK).status_code == 201


def test_create_book_returns_correct_data(client: TestClient):
    data = client.post("/books/", json=SAMPLE_BOOK).json()
    assert data["title"] == SAMPLE_BOOK["title"]
    assert data["author"] == SAMPLE_BOOK["author"]
    assert data["year"] == SAMPLE_BOOK["year"]
    assert data["status"] == "available"
    assert data["description"] == SAMPLE_BOOK["description"]


def test_create_book_generates_unique_uuid(client: TestClient):
    r1 = client.post("/books/", json=SAMPLE_BOOK).json()
    r2 = client.post("/books/", json=SAMPLE_BOOK).json()
    assert len(r1["id"]) == 36
    assert r1["id"] != r2["id"]


def test_create_book_default_status(client: TestClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "status"}
    assert client.post("/books/", json=book).json()["status"] == "available"


def test_create_book_issued_status(client: TestClient):
    data = client.post("/books/", json={**SAMPLE_BOOK, "status": "issued"}).json()
    assert data["status"] == "issued"


def test_create_book_without_description(client: TestClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "description"}
    assert client.post("/books/", json=book).json()["description"] is None


def test_create_book_missing_title_returns_422(client: TestClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "title"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_missing_author_returns_422(client: TestClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "author"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_missing_year_returns_422(client: TestClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "year"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_empty_title_returns_422(client: TestClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "title": ""}).status_code == 422


def test_create_book_empty_author_returns_422(client: TestClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "author": ""}).status_code == 422


def test_create_book_year_too_low_returns_422(client: TestClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 999}).status_code == 422


def test_create_book_year_too_high_returns_422(client: TestClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 2101}).status_code == 422


def test_create_book_invalid_status_returns_422(client: TestClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "status": "lost"}).status_code == 422


# ── GET /books/ ───────────────────────────────────────────────────────────────

def test_get_all_books_returns_200(client: TestClient):
    assert client.get("/books/").status_code == 200


def test_get_all_books_empty_list(client: TestClient):
    data = client.get("/books/").json()
    assert data["items"] == []
    assert data["total"] == 0


def test_get_all_books_returns_correct_structure(client: TestClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/").json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


def test_get_all_books_total_count(client: TestClient):
    client.post("/books/", json=SAMPLE_BOOK)
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Book 2"})
    data = client.get("/books/").json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# ── Filtering ─────────────────────────────────────────────────────────────────

def test_filter_by_status_available(client: TestClient):
    client.post("/books/", json={**SAMPLE_BOOK, "status": "available"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Issued", "status": "issued"})
    data = client.get("/books/?status=available").json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "available"


def test_filter_by_status_issued(client: TestClient):
    client.post("/books/", json={**SAMPLE_BOOK, "status": "issued"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Available", "status": "available"})
    data = client.get("/books/?status=issued").json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "issued"


def test_filter_by_author_exact(client: TestClient):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "HP", "author": "Rowling"})
    data = client.get("/books/?author=Tolkien").json()
    assert data["total"] == 1
    assert data["items"][0]["author"] == "Tolkien"


def test_filter_by_author_case_insensitive(client: TestClient):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"})
    data = client.get("/books/?author=tolkien").json()
    assert data["total"] == 1


def test_filter_by_author_partial_match(client: TestClient):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "John Ronald Reuel Tolkien"})
    data = client.get("/books/?author=tolkien").json()
    assert data["total"] == 1


def test_filter_no_match_returns_empty(client: TestClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?author=NoSuchAuthorXYZ").json()
    assert data["items"] == []
    assert data["total"] == 0


# ── Sorting ───────────────────────────────────────────────────────────────────

def test_sort_by_title(client: TestClient):
    for title in ["Zebra", "Apple", "Mango"]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": title})
    items = client.get("/books/?sort_by=title").json()["items"]
    titles = [b["title"] for b in items]
    assert titles == sorted(titles, key=str.lower)


def test_sort_by_year(client: TestClient):
    for year in [2005, 1990, 2020]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {year}", "year": year})
    items = client.get("/books/?sort_by=year").json()["items"]
    years = [b["year"] for b in items]
    assert years == sorted(years)


def test_sort_by_invalid_field_returns_422(client: TestClient):
    assert client.get("/books/?sort_by=invalid").status_code == 422


def test_combined_filter_and_sort(client: TestClient):
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Z", "author": "Tolkien", "year": 2000})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "A", "author": "Tolkien", "year": 1990})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "M", "author": "Rowling", "year": 1995})
    data = client.get("/books/?author=tolkien&sort_by=year").json()
    assert data["total"] == 2
    years = [b["year"] for b in data["items"]]
    assert years == sorted(years)


# ── Pagination ────────────────────────────────────────────────────────────────

def test_pagination_default_limit_and_offset(client: TestClient):
    for i in range(12):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i}"})
    data = client.get("/books/").json()
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["total"] == 12
    assert len(data["items"]) == 10


def test_pagination_custom_limit(client: TestClient):
    for i in range(5):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i}"})
    data = client.get("/books/?limit=3").json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["limit"] == 3


def test_pagination_offset(client: TestClient):
    for i in range(5):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i}"})
    data = client.get("/books/?offset=3").json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["offset"] == 3


def test_pagination_limit_and_offset(client: TestClient):
    for i in range(10):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i:02d}"})
    data = client.get("/books/?sort_by=title&limit=3&offset=3").json()
    assert len(data["items"]) == 3
    assert data["total"] == 10
    assert data["items"][0]["title"] == "Book 03"


def test_pagination_offset_exceeds_total(client: TestClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?offset=100").json()
    assert data["items"] == []
    assert data["total"] == 1


def test_pagination_limit_exceeds_total(client: TestClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?limit=50").json()
    assert len(data["items"]) == 1
    assert data["total"] == 1


def test_pagination_invalid_limit_returns_422(client: TestClient):
    assert client.get("/books/?limit=0").status_code == 422


def test_pagination_invalid_offset_returns_422(client: TestClient):
    assert client.get("/books/?offset=-1").status_code == 422


def test_pagination_limit_max_100(client: TestClient):
    assert client.get("/books/?limit=101").status_code == 422


# ── GET /books/{id} ───────────────────────────────────────────────────────────

def test_get_book_by_id_returns_200(client: TestClient):
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    assert client.get(f"/books/{created['id']}").status_code == 200


def test_get_book_by_id_returns_correct_data(client: TestClient):
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    data = client.get(f"/books/{created['id']}").json()
    assert data["id"] == created["id"]
    assert data["title"] == SAMPLE_BOOK["title"]


def test_get_book_by_id_not_found_returns_404(client: TestClient):
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


def test_get_book_by_id_404_has_detail(client: TestClient):
    resp = client.get("/books/00000000-0000-0000-0000-000000000000")
    assert "detail" in resp.json()


# ── DELETE /books/{id} ────────────────────────────────────────────────────────

def test_delete_existing_book_returns_204(client: TestClient):
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    assert client.delete(f"/books/{created['id']}").status_code == 204


def test_delete_removes_book(client: TestClient):
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    client.delete(f"/books/{created['id']}")
    assert client.get(f"/books/{created['id']}").status_code == 404


def test_delete_idempotent_second_call_returns_204(client: TestClient):
    created = client.post("/books/", json=SAMPLE_BOOK).json()
    client.delete(f"/books/{created['id']}")
    assert client.delete(f"/books/{created['id']}").status_code == 204


def test_delete_nonexistent_returns_204(client: TestClient):
    assert client.delete("/books/00000000-0000-0000-0000-000000000000").status_code == 204


def test_delete_does_not_affect_other_books(client: TestClient):
    b1 = client.post("/books/", json=SAMPLE_BOOK).json()
    b2 = client.post("/books/", json={**SAMPLE_BOOK, "title": "Book 2"}).json()
    client.delete(f"/books/{b1['id']}")
    assert client.get(f"/books/{b2['id']}").status_code == 200
