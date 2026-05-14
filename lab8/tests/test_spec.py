"""
OpenAPI spec structure validation — runs without any external service.
"""
import pytest


# ── Basic structure ───────────────────────────────────────────────────────────

def test_spec_loads_successfully(spec):
    assert spec is not None


def test_spec_openapi_version(spec):
    assert spec["openapi"].startswith("3.")


def test_spec_has_info(spec):
    assert "title" in spec["info"]
    assert "version" in spec["info"]
    assert spec["info"]["title"] == "Library API"


def test_spec_has_servers(spec):
    assert "servers" in spec
    assert len(spec["servers"]) >= 1


def test_spec_has_tags(spec):
    tag_names = {t["name"] for t in spec.get("tags", [])}
    assert "auth" in tag_names
    assert "books" in tag_names


# ── Security ──────────────────────────────────────────────────────────────────

def test_spec_has_bearer_security_scheme(spec):
    schemes = spec["components"]["securitySchemes"]
    assert "BearerAuth" in schemes
    assert schemes["BearerAuth"]["scheme"] == "bearer"


def test_spec_default_security_is_bearer(spec):
    security = spec.get("security", [])
    assert any("BearerAuth" in s for s in security)


def test_auth_endpoints_have_no_security(spec):
    """Auth endpoints must be accessible without a token."""
    for path in ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"]:
        for method in spec["paths"].get(path, {}).values():
            if isinstance(method, dict):
                # security: [] means public
                assert method.get("security") == [], \
                    f"{path} should be public (security: [])"


def test_book_endpoints_require_auth(spec):
    """Book endpoints must inherit global BearerAuth."""
    for path in ["/books/", "/books/{book_id}"]:
        for method_name, method in spec["paths"].get(path, {}).items():
            if isinstance(method, dict):
                # Should NOT override with empty [] (meaning not public)
                assert method.get("security") != [], \
                    f"{path} {method_name} should not be public"


# ── Auth paths ────────────────────────────────────────────────────────────────

def test_spec_has_register_endpoint(spec):
    assert "/auth/register" in spec["paths"]
    assert "post" in spec["paths"]["/auth/register"]


def test_register_has_201_and_409_and_422(spec):
    responses = spec["paths"]["/auth/register"]["post"]["responses"]
    assert "201" in responses
    assert "409" in responses
    assert "422" in responses


def test_spec_has_login_endpoint(spec):
    assert "/auth/login" in spec["paths"]
    assert "post" in spec["paths"]["/auth/login"]


def test_login_has_200_and_401_and_429(spec):
    responses = spec["paths"]["/auth/login"]["post"]["responses"]
    assert "200" in responses
    assert "401" in responses
    assert "429" in responses


def test_spec_has_refresh_endpoint(spec):
    assert "/auth/refresh" in spec["paths"]
    assert "post" in spec["paths"]["/auth/refresh"]


def test_refresh_has_200_and_401(spec):
    responses = spec["paths"]["/auth/refresh"]["post"]["responses"]
    assert "200" in responses
    assert "401" in responses


def test_spec_has_logout_endpoint(spec):
    assert "/auth/logout" in spec["paths"]
    assert "post" in spec["paths"]["/auth/logout"]


def test_logout_has_200(spec):
    responses = spec["paths"]["/auth/logout"]["post"]["responses"]
    assert "200" in responses


# ── Books paths ───────────────────────────────────────────────────────────────

def test_spec_has_books_list_endpoint(spec):
    assert "/books/" in spec["paths"]
    assert "get" in spec["paths"]["/books/"]
    assert "post" in spec["paths"]["/books/"]


def test_get_books_has_200_401_429(spec):
    responses = spec["paths"]["/books/"]["get"]["responses"]
    assert "200" in responses
    assert "401" in responses
    assert "429" in responses


def test_post_books_has_201_401_403_429(spec):
    responses = spec["paths"]["/books/"]["post"]["responses"]
    assert "201" in responses
    assert "401" in responses
    assert "403" in responses
    assert "429" in responses


def test_spec_has_book_detail_endpoint(spec):
    assert "/books/{book_id}" in spec["paths"]
    assert "get" in spec["paths"]["/books/{book_id}"]
    assert "delete" in spec["paths"]["/books/{book_id}"]


def test_get_book_has_200_401_404(spec):
    responses = spec["paths"]["/books/{book_id}"]["get"]["responses"]
    assert "200" in responses
    assert "401" in responses
    assert "404" in responses


def test_delete_book_has_204_401_403(spec):
    responses = spec["paths"]["/books/{book_id}"]["delete"]["responses"]
    assert "204" in responses
    assert "401" in responses
    assert "403" in responses


# ── Query parameters ──────────────────────────────────────────────────────────

def test_get_books_has_pagination_params(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    assert "limit" in params
    assert "offset" in params
    assert params["limit"]["schema"]["default"] == 10
    assert params["offset"]["schema"]["default"] == 0


def test_get_books_has_filter_params(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    assert "status" in params
    assert "author" in params
    assert "sort_by" in params


def test_status_param_has_enum(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    status_enum = params["status"]["schema"]["enum"]
    assert "available" in status_enum
    assert "issued" in status_enum


def test_sort_by_param_has_correct_enum(spec):
    params = {p["name"]: p for p in spec["paths"]["/books/"]["get"]["parameters"]}
    sort_enum = params["sort_by"]["schema"]["enum"]
    assert "title" in sort_enum
    assert "year" in sort_enum


# ── Schemas ───────────────────────────────────────────────────────────────────

def test_spec_has_all_schemas(spec):
    schemas = spec["components"]["schemas"]
    for name in ["Book", "BookCreate", "BookListResponse",
                 "UserCreate", "UserResponse",
                 "LoginRequest", "TokenResponse", "RefreshRequest",
                 "Error", "ValidationError"]:
        assert name in schemas, f"Schema '{name}' missing"


def test_book_schema_has_required_fields(spec):
    required = spec["components"]["schemas"]["Book"]["required"]
    for field in ["id", "title", "author", "status", "year"]:
        assert field in required


def test_book_create_requires_title_author_year(spec):
    required = spec["components"]["schemas"]["BookCreate"]["required"]
    assert "title" in required
    assert "author" in required
    assert "year" in required


def test_book_status_enum_values(spec):
    status = spec["components"]["schemas"]["Book"]["properties"]["status"]
    assert set(status["enum"]) == {"available", "issued"}


def test_book_year_has_min_max_constraints(spec):
    year = spec["components"]["schemas"]["BookCreate"]["properties"]["year"]
    assert year["minimum"] == 1000
    assert year["maximum"] == 2100


def test_token_response_has_both_tokens(spec):
    props = spec["components"]["schemas"]["TokenResponse"]["properties"]
    assert "access_token" in props
    assert "refresh_token" in props
    assert "token_type" in props


def test_book_list_response_has_pagination_fields(spec):
    props = spec["components"]["schemas"]["BookListResponse"]["properties"]
    assert "items" in props
    assert "total" in props
    assert "limit" in props
    assert "offset" in props


# ── Reusable responses ────────────────────────────────────────────────────────

def test_spec_has_reusable_responses(spec):
    responses = spec["components"]["responses"]
    for name in ["Unauthorized", "Forbidden", "NotFound",
                 "UnprocessableEntity", "TooManyRequests"]:
        assert name in responses, f"Reusable response '{name}' missing"


def test_too_many_requests_has_retry_after_header(spec):
    response = spec["components"]["responses"]["TooManyRequests"]
    assert "Retry-After" in response.get("headers", {})


# ── Operation IDs ─────────────────────────────────────────────────────────────

def test_all_operations_have_operation_ids(spec):
    for path, path_item in spec["paths"].items():
        for method, operation in path_item.items():
            if isinstance(operation, dict) and method in (
                "get", "post", "put", "patch", "delete"
            ):
                assert "operationId" in operation, \
                    f"Missing operationId at {method.upper()} {path}"
