from tests.conftest import _register, _auth_header


def _create_conv(client):
    token = _register(client).json()["token"]
    h = _auth_header(token)
    return client.post("/api/v1/service/conversations", json={"message": "ticket"}, headers=h).json()["conversation"]["id"]


def test_workspace_list(client):
    _create_conv(client)
    r = client.get("/api/v1/workspace/conversations")
    assert r.status_code == 200
    convs = r.json()["conversations"]
    assert len(convs) == 1
    assert "consumer" in convs[0]


def test_workspace_detail(client):
    conv_id = _create_conv(client)
    r = client.get(f"/api/v1/workspace/conversations/{conv_id}")
    assert r.status_code == 200
    assert "consumer" in r.json()
    assert "messages" in r.json()


def test_escalate(client):
    conv_id = _create_conv(client)
    r = client.post(f"/api/v1/workspace/conversations/{conv_id}/escalate", json={"reason": "need help"})
    assert r.status_code == 200
    assert r.json()["status"] == "escalated"


def test_close_and_reopen(client):
    conv_id = _create_conv(client)
    client.post(f"/api/v1/workspace/conversations/{conv_id}/close")
    r = client.get(f"/api/v1/workspace/conversations/{conv_id}")
    assert r.json()["status"] == "closed"
    client.post(f"/api/v1/workspace/conversations/{conv_id}/reopen")
    r = client.get(f"/api/v1/workspace/conversations/{conv_id}")
    assert r.json()["status"] == "open"


def test_not_found(client):
    r = client.get("/api/v1/workspace/conversations/nonexistent")
    assert r.status_code == 404
