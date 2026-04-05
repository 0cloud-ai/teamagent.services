def test_list_harness(client):
    r = client.get("/api/v1/workspace/harness")
    assert r.status_code == 200
    data = r.json()
    assert "engines" in data
    assert "claude-agent-sdk" in data["engines"]
    assert "claude-code-cli" in data["engines"]


def test_get_harness(client):
    r = client.get("/api/v1/workspace/harness/claude-agent-sdk")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "claude-agent-sdk"
    assert "anthropic" in data["api_formats"]


def test_get_harness_not_found(client):
    r = client.get("/api/v1/workspace/harness/nonexistent")
    assert r.status_code == 404
