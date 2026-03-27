"""
Tests for service_info_api — GET/PUT /api/v1/service/info
"""


def test_get_info(client):
    """GET /api/v1/service/info returns 200 with name and status."""
    resp = client.get("/api/v1/service/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "status" in data


def test_update_info(client):
    """PUT /api/v1/service/info updates and returns the new values."""
    payload = {
        "name": "My Custom Service",
        "description": "Updated description",
        "status": "paused",
        "capabilities": ["chat", "search"],
    }
    resp = client.put("/api/v1/service/info", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "My Custom Service"
    assert data["description"] == "Updated description"
    assert data["status"] == "paused"
    assert data["capabilities"] == ["chat", "search"]

    # Verify the update persists on a subsequent GET
    resp2 = client.get("/api/v1/service/info")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "My Custom Service"
