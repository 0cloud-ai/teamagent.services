def test_get_info(client):
    r = client.get("/api/v1/service/info")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "active"
    assert data["providers"] == 2
    assert "harnesses" in data
    assert data["members"] == 3
