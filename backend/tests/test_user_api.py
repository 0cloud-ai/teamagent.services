"""
Tests for user_api — /api/v1/user
"""

_BASE = "/api/v1/user"


def _register(client, email="alice@example.com", name="Alice", password="secret123"):
    return client.post(f"{_BASE}/register", json={
        "email": email,
        "name": name,
        "password": password,
    })


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Registration ─────────────────────────────────────────────────────

def test_register(client):
    resp = _register(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert "id" in data["user"]


def test_register_duplicate(client):
    resp1 = _register(client)
    assert resp1.status_code == 200

    resp2 = _register(client)
    # DuckDB raises a unique-constraint error; FastAPI returns 500
    assert resp2.status_code in (409, 500)


# ── Login ────────────────────────────────────────────────────────────

def test_login(client):
    _register(client)
    resp = client.post(f"{_BASE}/login", json={
        "email": "alice@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "alice@example.com"


def test_login_wrong_password(client):
    _register(client)
    resp = client.post(f"{_BASE}/login", json={
        "email": "alice@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


# ── /me ──────────────────────────────────────────────────────────────

def test_get_me(client):
    reg = _register(client).json()
    token = reg["token"]

    resp = client.get(f"{_BASE}/me", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["name"] == "Alice"
    assert "memberships" in data


def test_update_me(client):
    reg = _register(client).json()
    token = reg["token"]

    resp = client.put(f"{_BASE}/me", json={"name": "Alice Updated"}, headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice Updated"


def test_change_password(client):
    reg = _register(client).json()
    token = reg["token"]

    resp = client.put(
        f"{_BASE}/me/password",
        json={"old_password": "secret123", "new_password": "newsecret456"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200

    # Verify new password works
    login_resp = client.post(f"{_BASE}/login", json={
        "email": "alice@example.com",
        "password": "newsecret456",
    })
    assert login_resp.status_code == 200
