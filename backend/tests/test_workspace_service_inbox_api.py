"""
Tests for workspace_service_inbox_api — /api/v1/workspace/service-inbox
Conversations are created via conversation_repo directly.
"""

import uuid
import json
import datetime as dt

from repository.db import get_conn
from repository import conversation_repo


def _seed_user(user_id="inbox-user-001", name="Inbox Test User"):
    """Insert a test user so FK constraints and JOIN queries work."""
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (id, email, name, password, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        [user_id, f"{user_id}@example.com", name, "hashed", dt.datetime.now(dt.timezone.utc)],
    )
    return user_id


def _create_conversation(user_id=None, message="Inbox test message"):
    """Create a conversation + first message via the repo layer and return its id."""
    if user_id is None:
        user_id = _seed_user()
    now = dt.datetime.now(dt.timezone.utc)
    conv_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())

    conversation_repo.create_conversation(
        id=conv_id,
        title=message[:50],
        consumer_id=user_id,
        status="open",
        labels=[],
        created_at=now,
        updated_at=now,
    )
    conversation_repo.add_message(
        id=msg_id,
        conversation_id=conv_id,
        role="user",
        content=message,
        created_at=now,
    )
    return conv_id


# ── Tests ─────────────────────────────────────────────────────────────


def test_list_inbox(client):
    """GET /workspace/service-inbox includes the created conversation."""
    conv_id = _create_conversation()

    resp = client.get("/api/v1/workspace/service-inbox")
    assert resp.status_code == 200
    data = resp.json()
    # The response is either a list or a dict with "conversations" key,
    # depending on whether response_model serialization wraps it.
    if isinstance(data, list):
        ids = [c["id"] for c in data]
    else:
        ids = [c["id"] for c in data.get("conversations", [])]
    assert conv_id in ids


def test_get_inbox_detail(client):
    """GET /workspace/service-inbox/{id} returns 200 with conversation detail."""
    conv_id = _create_conversation()

    resp = client.get(f"/api/v1/workspace/service-inbox/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == conv_id
    assert "messages" in data
    assert "consumer" in data


def test_escalate(client):
    """POST /service-inbox/{id}/escalate sets status to escalated."""
    conv_id = _create_conversation()

    resp = client.post(
        f"/api/v1/workspace/service-inbox/{conv_id}/escalate",
        json={"reason": "Needs human review"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "escalated"


def test_close_inbox(client):
    """POST /service-inbox/{id}/close sets status to closed."""
    conv_id = _create_conversation()

    resp = client.post(f"/api/v1/workspace/service-inbox/{conv_id}/close")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "closed"


def test_reopen(client):
    """Close then POST /service-inbox/{id}/reopen sets status back to open."""
    conv_id = _create_conversation()

    # Close first
    client.post(f"/api/v1/workspace/service-inbox/{conv_id}/close")

    # Reopen
    resp = client.post(f"/api/v1/workspace/service-inbox/{conv_id}/reopen")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "open"


def test_update_labels(client):
    """PUT /service-inbox/{id}/labels updates labels."""
    conv_id = _create_conversation()

    resp = client.put(
        f"/api/v1/workspace/service-inbox/{conv_id}/labels",
        json={"labels": ["vip", "refund"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert set(data["labels"]) == {"vip", "refund"}
