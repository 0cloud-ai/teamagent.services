"""
Tests for workspace_harness_api — /api/v1/workspace/harness
"""


def _create_provider(client, vendor="anthropic", model="claude-sonnet-4-20250514"):
    """Helper: create a provider and return its JSON."""
    resp = client.post(
        "/api/v1/workspace/providers",
        json={"vendor": vendor, "model": model},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_get_harness(client):
    """GET /api/v1/workspace/harness returns default engine and engine list."""
    resp = client.get("/api/v1/workspace/harness")
    assert resp.status_code == 200
    data = resp.json()
    assert "default" in data
    assert data["default"] == "claude-agent-sdk"
    assert "engines" in data
    assert len(data["engines"]) > 0
    engine_ids = [e["id"] for e in data["engines"]]
    assert "claude-agent-sdk" in engine_ids


def test_set_default(client):
    """PUT /api/v1/workspace/harness/default changes the default engine."""
    resp = client.put(
        "/api/v1/workspace/harness/default",
        json={"engine_id": "opencode"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["default"] == "opencode"


def test_add_binding(client):
    """POST a binding to an engine after creating a matching provider."""
    provider = _create_provider(client)
    provider_id = provider["id"]

    resp = client.post(
        "/api/v1/workspace/harness/engines/claude-agent-sdk/bindings",
        json={"provider_id": provider_id, "role": "default"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["provider_id"] == provider_id
    assert data["role"] == "default"
    assert data["vendor"] == "anthropic"


def test_delete_binding(client):
    """Add a binding then delete it."""
    provider = _create_provider(client)
    provider_id = provider["id"]

    # Add
    resp = client.post(
        "/api/v1/workspace/harness/engines/claude-agent-sdk/bindings",
        json={"provider_id": provider_id},
    )
    assert resp.status_code == 201

    # Delete
    resp = client.delete(
        f"/api/v1/workspace/harness/engines/claude-agent-sdk/bindings/{provider_id}"
    )
    assert resp.status_code == 204

    # Verify it's gone
    resp = client.get("/api/v1/workspace/harness/engines/claude-agent-sdk")
    assert resp.status_code == 200
    bindings = resp.json()["bindings"]
    provider_ids = [b["provider_id"] for b in bindings]
    assert provider_id not in provider_ids
