"""
Tests for workspace_members_api — /api/v1/workspace/members
"""

_BASE = "/api/v1/workspace/members"


def _add_user_member(client, name="Bob", email="bob@example.com", role="member"):
    return client.post(_BASE, json={
        "type": "user",
        "name": name,
        "email": email,
        "role": role,
    })


def _add_service_member(client, name="CodeBot", service_url="http://localhost:9000"):
    return client.post(_BASE, json={
        "type": "service",
        "name": name,
        "service_url": service_url,
    })


# ── Add members ──────────────────────────────────────────────────────

def test_add_user_member(client):
    resp = _add_user_member(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "user"
    assert data["name"] == "Bob"
    assert data["email"] == "bob@example.com"
    assert "id" in data


def test_add_service_member(client):
    resp = _add_service_member(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "service"
    assert data["name"] == "CodeBot"
    assert data["service_url"] == "http://localhost:9000"
    assert data["status"] == "connected"


# ── List members ─────────────────────────────────────────────────────

def test_list_members(client):
    _add_user_member(client, name="Member1", email="m1@example.com")
    _add_service_member(client, name="Service1")

    resp = client.get(_BASE)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_list_members_filter_type(client):
    _add_user_member(client, name="Member1", email="m1@example.com")
    _add_service_member(client, name="Service1")

    resp = client.get(_BASE, params={"type": "user"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["type"] == "user"


# ── Update member ────────────────────────────────────────────────────

def test_update_member(client):
    create_resp = _add_user_member(client)
    member_id = create_resp.json()["id"]

    resp = client.put(f"{_BASE}/{member_id}", json={"name": "Bob Updated", "role": "owner"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Bob Updated"
    assert data["role"] == "owner"


# ── Delete member ────────────────────────────────────────────────────

def test_delete_member(client):
    create_resp = _add_service_member(client)
    member_id = create_resp.json()["id"]

    resp = client.delete(f"{_BASE}/{member_id}")
    assert resp.status_code == 204

    # Verify member is gone
    list_resp = client.get(_BASE)
    assert len(list_resp.json()) == 0
