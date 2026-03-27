"""
Tests for workspace_sessions_api — /api/v1/workspace/sessions
"""

import datetime as dt

from repository.db import get_conn


# ── helpers ──────────────────────────────────────────────────────────

def _seed_member(member_id: str = "member-1", name: str = "Agent A"):
    """Insert a member row so session_members FK is satisfied."""
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO members (id, type, name, joined_at) VALUES (?, 'service', ?, ?)",
        [member_id, name, dt.datetime.now(dt.timezone.utc)],
    )


def _create_session(client, path: str = "/", title: str = "Test Session"):
    """Create a session via the API and return the response JSON."""
    resp = client.post(
        "/api/v1/workspace/sessions",
        json={"path": path, "title": title},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── tests ────────────────────────────────────────────────────────────

def test_create_session(client):
    """POST /api/v1/workspace/sessions creates a session with id and path."""
    data = _create_session(client, path="/proj", title="My Session")
    assert "id" in data
    assert data["path"] == "/proj"
    assert data["title"] == "My Session"


def test_list_sessions(client):
    """After creating a session, it appears in the listing for that path."""
    session = _create_session(client, path="/work")

    resp = client.get("/api/v1/workspace/sessions/work")
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "/work"
    ids = [s["id"] for s in data["sessions"]]
    assert session["id"] in ids


def test_get_session_messages(client):
    """GET messages for a fresh session returns 200 with empty messages list."""
    session = _create_session(client)

    resp = client.get(f"/api/v1/workspace/sessions/{session['id']}/messages")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session["id"]
    assert data["messages"] == []


def test_send_message(client):
    """POST a message to a session returns 201."""
    session = _create_session(client)

    resp = client.post(
        f"/api/v1/workspace/sessions/{session['id']}/messages",
        json={"content": "Hello, world!"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Hello, world!"
    assert data["role"] == "user"


def test_session_members(client):
    """Add a member, list members, then remove that member."""
    session = _create_session(client)
    _seed_member("agent-x", "Agent X")

    # Add member
    resp = client.post(
        f"/api/v1/workspace/sessions/{session['id']}/members",
        json={"member_id": "agent-x"},
    )
    assert resp.status_code == 201
    member = resp.json()
    assert member["id"] == "agent-x"
    assert member["name"] == "Agent X"

    # List members
    resp = client.get(f"/api/v1/workspace/sessions/{session['id']}/members")
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()]
    assert "agent-x" in ids

    # Remove member
    resp = client.delete(
        f"/api/v1/workspace/sessions/{session['id']}/members/agent-x"
    )
    assert resp.status_code == 204

    # Verify removal
    resp = client.get(f"/api/v1/workspace/sessions/{session['id']}/members")
    ids = [m["id"] for m in resp.json()]
    assert "agent-x" not in ids
