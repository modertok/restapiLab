from fastapi.testclient import TestClient

ADMIN = {"username": "admin_test", "password": "admin123", "role": "admin"}
USER = {"username": "user_test", "password": "user123", "role": "user"}


# ── POST /auth/register ───────────────────────────────────────────────────────

def test_register_returns_201(client: TestClient):
    assert client.post("/auth/register", json=ADMIN).status_code == 201


def test_register_returns_user_data(client: TestClient):
    data = client.post("/auth/register", json=ADMIN).json()
    assert data["username"] == ADMIN["username"]
    assert data["role"] == "admin"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_default_role_is_user(client: TestClient):
    creds = {"username": "noroler", "password": "pass12"}
    data = client.post("/auth/register", json=creds).json()
    assert data["role"] == "user"


def test_register_duplicate_username_returns_409(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    assert client.post("/auth/register", json=ADMIN).status_code == 409


def test_register_username_too_short_returns_422(client: TestClient):
    assert client.post("/auth/register", json={**ADMIN, "username": "ab"}).status_code == 422


def test_register_password_too_short_returns_422(client: TestClient):
    assert client.post("/auth/register", json={**ADMIN, "password": "12345"}).status_code == 422


def test_register_missing_username_returns_422(client: TestClient):
    assert client.post("/auth/register", json={"password": "pass12"}).status_code == 422


def test_register_missing_password_returns_422(client: TestClient):
    assert client.post("/auth/register", json={"username": "someone"}).status_code == 422


# ── POST /auth/login ──────────────────────────────────────────────────────────

def test_login_returns_200(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    assert client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).status_code == 200


def test_login_returns_both_tokens(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    data = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_tokens_are_non_empty_strings(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    data = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    assert len(data["access_token"]) > 20
    assert len(data["refresh_token"]) > 20


def test_login_wrong_password_returns_401(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    assert client.post("/auth/login", json={"username": ADMIN["username"], "password": "wrongpass"}).status_code == 401


def test_login_unknown_user_returns_401(client: TestClient):
    assert client.post("/auth/login", json={"username": "ghost", "password": "pass123"}).status_code == 401


def test_login_401_has_detail(client: TestClient):
    resp = client.post("/auth/login", json={"username": "ghost", "password": "pass123"})
    assert "detail" in resp.json()


# ── POST /auth/refresh ────────────────────────────────────────────────────────

def test_refresh_returns_200(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    tokens = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200


def test_refresh_returns_new_token_pair(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    t1 = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    t2 = client.post("/auth/refresh", json={"refresh_token": t1["refresh_token"]}).json()
    assert "access_token" in t2
    assert "refresh_token" in t2
    assert t2["access_token"] != t1["access_token"]
    assert t2["refresh_token"] != t1["refresh_token"]


def test_refresh_rotates_token_old_token_invalid(client: TestClient):
    """Old refresh token must not work after rotation."""
    client.post("/auth/register", json=ADMIN)
    t1 = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    client.post("/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    # Old refresh token is now invalidated
    assert client.post("/auth/refresh", json={"refresh_token": t1["refresh_token"]}).status_code == 401


def test_refresh_new_token_works(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    t1 = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    t2 = client.post("/auth/refresh", json={"refresh_token": t1["refresh_token"]}).json()
    t3 = client.post("/auth/refresh", json={"refresh_token": t2["refresh_token"]}).json()
    assert t3["access_token"] != t2["access_token"]


def test_refresh_invalid_token_returns_401(client: TestClient):
    assert client.post("/auth/refresh", json={"refresh_token": "not.a.valid.jwt"}).status_code == 401


def test_refresh_access_token_as_refresh_returns_401(client: TestClient):
    """Access token must not be accepted as refresh token."""
    client.post("/auth/register", json=ADMIN)
    tokens = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    assert client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code == 401


# ── POST /auth/logout ─────────────────────────────────────────────────────────

def test_logout_returns_200(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    tokens = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 200


def test_logout_invalidates_refresh_token(client: TestClient):
    client.post("/auth/register", json=ADMIN)
    tokens = client.post("/auth/login", json={"username": ADMIN["username"], "password": ADMIN["password"]}).json()
    client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_logout_unknown_token_still_returns_200(client: TestClient):
    """Logout is idempotent."""
    assert client.post("/auth/logout", json={"refresh_token": "unknown_token"}).status_code == 200
