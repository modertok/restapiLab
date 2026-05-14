from flask.testing import FlaskClient

SAMPLE_BOOK = {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "description": "A novel about the American Dream",
    "status": "available",
    "year": 1925,
}


# ── POST /books/ ──────────────────────────────────────────────────────────────

def test_create_book_returns_201(client: FlaskClient):
    assert client.post("/books/", json=SAMPLE_BOOK).status_code == 201


def test_create_book_returns_correct_data(client: FlaskClient):
    data = client.post("/books/", json=SAMPLE_BOOK).get_json()
    assert data["title"] == SAMPLE_BOOK["title"]
    assert data["author"] == SAMPLE_BOOK["author"]
    assert data["year"] == SAMPLE_BOOK["year"]
    assert data["status"] == "available"
    assert data["description"] == SAMPLE_BOOK["description"]


def test_create_book_generates_unique_uuid(client: FlaskClient):
    r1 = client.post("/books/", json=SAMPLE_BOOK).get_json()
    r2 = client.post("/books/", json=SAMPLE_BOOK).get_json()
    assert len(r1["id"]) == 36
    assert r1["id"] != r2["id"]


def test_create_book_default_status(client: FlaskClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "status"}
    assert client.post("/books/", json=book).get_json()["status"] == "available"


def test_create_book_issued_status(client: FlaskClient):
    data = client.post("/books/", json={**SAMPLE_BOOK, "status": "issued"}).get_json()
    assert data["status"] == "issued"


def test_create_book_without_description(client: FlaskClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "description"}
    assert client.post("/books/", json=book).get_json()["description"] is None


def test_create_book_missing_title_returns_422(client: FlaskClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "title"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_missing_author_returns_422(client: FlaskClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "author"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_missing_year_returns_422(client: FlaskClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "year"}
    assert client.post("/books/", json=book).status_code == 422


def test_create_book_empty_title_returns_422(client: FlaskClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "title": ""}).status_code == 422


def test_create_book_empty_author_returns_422(client: FlaskClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "author": ""}).status_code == 422


def test_create_book_year_too_low_returns_422(client: FlaskClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 999}).status_code == 422


def test_create_book_year_too_high_returns_422(client: FlaskClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "year": 2101}).status_code == 422


def test_create_book_invalid_status_returns_422(client: FlaskClient):
    assert client.post("/books/", json={**SAMPLE_BOOK, "status": "lost"}).status_code == 422


def test_create_book_422_has_errors_field(client: FlaskClient):
    book = {k: v for k, v in SAMPLE_BOOK.items() if k != "title"}
    data = client.post("/books/", json=book).get_json()
    assert "errors" in data


# ── GET /books/ ───────────────────────────────────────────────────────────────

def test_get_all_books_returns_200(client: FlaskClient):
    assert client.get("/books/").status_code == 200


def test_get_all_books_empty(client: FlaskClient):
    data = client.get("/books/").get_json()
    assert data["items"] == []
    assert data["total"] == 0


def test_get_all_books_response_structure(client: FlaskClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/").get_json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


def test_get_all_books_total_count(client: FlaskClient):
    client.post("/books/", json=SAMPLE_BOOK)
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Book 2"})
    data = client.get("/books/").get_json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


# ── Filtering ─────────────────────────────────────────────────────────────────

def test_filter_by_status_available(client: FlaskClient):
    client.post("/books/", json={**SAMPLE_BOOK, "status": "available"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Issued", "status": "issued"})
    data = client.get("/books/?status=available").get_json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "available"


def test_filter_by_status_issued(client: FlaskClient):
    client.post("/books/", json={**SAMPLE_BOOK, "status": "issued"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Available", "status": "available"})
    data = client.get("/books/?status=issued").get_json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "issued"


def test_filter_by_status_invalid_returns_422(client: FlaskClient):
    assert client.get("/books/?status=unknown").status_code == 422


def test_filter_by_author_exact(client: FlaskClient):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "HP", "author": "Rowling"})
    data = client.get("/books/?author=Tolkien").get_json()
    assert data["total"] == 1
    assert data["items"][0]["author"] == "Tolkien"


def test_filter_by_author_case_insensitive(client: FlaskClient):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "Tolkien"})
    assert client.get("/books/?author=tolkien").get_json()["total"] == 1


def test_filter_by_author_partial_match(client: FlaskClient):
    client.post("/books/", json={**SAMPLE_BOOK, "author": "John Ronald Reuel Tolkien"})
    assert client.get("/books/?author=tolkien").get_json()["total"] == 1


def test_filter_no_match_returns_empty(client: FlaskClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?author=NoSuchAuthorXYZ").get_json()
    assert data["items"] == []
    assert data["total"] == 0


# ── Sorting ───────────────────────────────────────────────────────────────────

def test_sort_by_title(client: FlaskClient):
    for title in ["Zebra", "Apple", "Mango"]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": title})
    items = client.get("/books/?sort_by=title").get_json()["items"]
    titles = [b["title"] for b in items]
    assert titles == sorted(titles, key=str.lower)


def test_sort_by_year(client: FlaskClient):
    for year in [2005, 1990, 2020]:
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {year}", "year": year})
    items = client.get("/books/?sort_by=year").get_json()["items"]
    assert [b["year"] for b in items] == sorted([b["year"] for b in items])


def test_sort_by_invalid_returns_422(client: FlaskClient):
    assert client.get("/books/?sort_by=invalid").status_code == 422


def test_combined_filter_and_sort(client: FlaskClient):
    client.post("/books/", json={**SAMPLE_BOOK, "title": "Z", "author": "Tolkien", "year": 2000})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "A", "author": "Tolkien", "year": 1990})
    client.post("/books/", json={**SAMPLE_BOOK, "title": "M", "author": "Rowling", "year": 1995})
    data = client.get("/books/?author=tolkien&sort_by=year").get_json()
    assert data["total"] == 2
    years = [b["year"] for b in data["items"]]
    assert years == sorted(years)


# ── Pagination ────────────────────────────────────────────────────────────────

def test_pagination_default_limit_and_offset(client: FlaskClient):
    for i in range(12):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i:02d}"})
    data = client.get("/books/").get_json()
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["total"] == 12
    assert len(data["items"]) == 10


def test_pagination_custom_limit(client: FlaskClient):
    for i in range(5):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i}"})
    data = client.get("/books/?limit=3").get_json()
    assert len(data["items"]) == 3
    assert data["total"] == 5


def test_pagination_offset(client: FlaskClient):
    for i in range(5):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i:02d}"})
    data = client.get("/books/?sort_by=title&offset=3").get_json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


def test_pagination_limit_and_offset(client: FlaskClient):
    for i in range(10):
        client.post("/books/", json={**SAMPLE_BOOK, "title": f"Book {i:02d}"})
    data = client.get("/books/?sort_by=title&limit=3&offset=3").get_json()
    assert len(data["items"]) == 3
    assert data["total"] == 10
    assert data["items"][0]["title"] == "Book 03"


def test_pagination_offset_exceeds_total(client: FlaskClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?offset=100").get_json()
    assert data["items"] == []
    assert data["total"] == 1


def test_pagination_limit_exceeds_total(client: FlaskClient):
    client.post("/books/", json=SAMPLE_BOOK)
    data = client.get("/books/?limit=50").get_json()
    assert len(data["items"]) == 1
    assert data["total"] == 1


def test_pagination_invalid_limit_returns_422(client: FlaskClient):
    assert client.get("/books/?limit=0").status_code == 422


def test_pagination_invalid_offset_returns_422(client: FlaskClient):
    assert client.get("/books/?offset=-1").status_code == 422


def test_pagination_limit_max_100_returns_422(client: FlaskClient):
    assert client.get("/books/?limit=101").status_code == 422


# ── GET /books/<id> ───────────────────────────────────────────────────────────

def test_get_book_by_id_returns_200(client: FlaskClient):
    created = client.post("/books/", json=SAMPLE_BOOK).get_json()
    assert client.get(f"/books/{created['id']}").status_code == 200


def test_get_book_by_id_returns_correct_data(client: FlaskClient):
    created = client.post("/books/", json=SAMPLE_BOOK).get_json()
    data = client.get(f"/books/{created['id']}").get_json()
    assert data["id"] == created["id"]
    assert data["title"] == SAMPLE_BOOK["title"]


def test_get_book_not_found_returns_404(client: FlaskClient):
    assert client.get("/books/00000000-0000-0000-0000-000000000000").status_code == 404


def test_get_book_404_has_detail(client: FlaskClient):
    data = client.get("/books/00000000-0000-0000-0000-000000000000").get_json()
    assert "detail" in data


# ── DELETE /books/<id> ────────────────────────────────────────────────────────

def test_delete_existing_book_returns_204(client: FlaskClient):
    created = client.post("/books/", json=SAMPLE_BOOK).get_json()
    assert client.delete(f"/books/{created['id']}").status_code == 204


def test_delete_removes_book(client: FlaskClient):
    created = client.post("/books/", json=SAMPLE_BOOK).get_json()
    client.delete(f"/books/{created['id']}")
    assert client.get(f"/books/{created['id']}").status_code == 404


def test_delete_idempotent_second_call_returns_204(client: FlaskClient):
    created = client.post("/books/", json=SAMPLE_BOOK).get_json()
    client.delete(f"/books/{created['id']}")
    assert client.delete(f"/books/{created['id']}").status_code == 204


def test_delete_nonexistent_returns_204(client: FlaskClient):
    assert client.delete("/books/00000000-0000-0000-0000-000000000000").status_code == 204


def test_delete_does_not_affect_other_books(client: FlaskClient):
    b1 = client.post("/books/", json=SAMPLE_BOOK).get_json()
    b2 = client.post("/books/", json={**SAMPLE_BOOK, "title": "Book 2"}).get_json()
    client.delete(f"/books/{b1['id']}")
    assert client.get(f"/books/{b2['id']}").status_code == 200


# ── Swagger / OpenAPI ─────────────────────────────────────────────────────────

def test_swagger_ui_accessible(client: FlaskClient):
    assert client.get("/docs").status_code == 200


def test_openapi_spec_accessible(client: FlaskClient):
    assert client.get("/apispec.json").status_code == 200


def test_openapi_spec_has_correct_info(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    assert spec["info"]["title"] == "Library API"
    assert spec["info"]["version"] == "5.0.0"


def test_openapi_spec_has_books_paths(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    paths = spec.get("paths", {})
    assert "/books/" in paths
    assert "/books/{book_id}" in paths


def test_openapi_spec_has_definitions(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    defs = spec.get("definitions", {})
    assert "Book" in defs
    assert "BookCreate" in defs
    assert "BookListResponse" in defs


def test_openapi_spec_book_definition_has_required_fields(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    book_props = spec["definitions"]["Book"]["properties"]
    for field in ("id", "title", "author", "status", "year"):
        assert field in book_props


def test_openapi_spec_get_books_has_parameters(client: FlaskClient):
    spec = client.get("/apispec.json").get_json()
    get_op = spec["paths"]["/books/"]["get"]
    param_names = [p["name"] for p in get_op.get("parameters", [])]
    assert "status" in param_names
    assert "author" in param_names
    assert "sort_by" in param_names
    assert "limit" in param_names
    assert "offset" in param_names
