"""
Tests for service_conversations_api — /api/v1/service/conversations
Uses X-User-Id header for authentication (testing convenience path).
"""

import uuid
import datetime as dt

from repository.db import get_conn

USER_ID = "test-user-001"
HEADERS = {"X-User-Id": USER_ID}


def _seed_user():
    """Insert a test user into the users table so FK constraints are satisfied."""
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (id, email, name, password, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        [USER_ID, "test@example.com", "Test User", "hashed", dt.datetime.now(dt.timezone.utc)],
    )


def _create_conversation(client, message="Hello, I need help"):
    """Helper: create a conversation via the API and return the JSON response."""
    _seed_user()
    resp = client.post(
        "/api/v1/service/conversations",
        json={"message": message},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    return resp.json()


# ── Tests ─────────────────────────────────────────────────────────────


def test_create_conversation(client):
    """POST /conversations creates a conversation with status=open."""
    data = _create_conversation(client)
    conv = data["conversation"]
    assert "id" in conv
    assert conv["status"] == "open"
    assert "message" in data
    assert data["message"]["role"] == "user"


def test_list_conversations(client):
    """GET /conversations returns the previously created conversation."""
    created = _create_conversation(client)
    conv_id = created["conversation"]["id"]

    resp = client.get("/api/v1/service/conversations", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    ids = [c["id"] for c in data["conversations"]]
    assert conv_id in ids


def test_get_conversation_detail(client):
    """GET /conversations/{id} returns conversation detail with messages."""
    created = _create_conversation(client, message="Detail test")
    conv_id = created["conversation"]["id"]

    resp = client.get(f"/api/v1/service/conversations/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == conv_id
    assert "messages" in data
    assert len(data["messages"]) >= 1


def test_add_message(client):
    """POST /conversations/{id}/messages adds a message."""
    created = _create_conversation(client)
    conv_id = created["conversation"]["id"]

    resp = client.post(
        f"/api/v1/service/conversations/{conv_id}/messages",
        json={"content": "Follow-up question"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["role"] == "user"
    assert msg["content"] == "Follow-up question"


def test_update_labels(client):
    """PUT /conversations/{id}/labels updates labels."""
    created = _create_conversation(client)
    conv_id = created["conversation"]["id"]

    resp = client.put(
        f"/api/v1/service/conversations/{conv_id}/labels",
        json={"labels": ["billing", "urgent"]},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["labels"]) == {"billing", "urgent"}


def test_close_conversation(client):
    """POST /conversations/{id}/close sets status to closed."""
    created = _create_conversation(client)
    conv_id = created["conversation"]["id"]

    resp = client.post(
        f"/api/v1/service/conversations/{conv_id}/close",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "closed"
