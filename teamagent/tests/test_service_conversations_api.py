from teamagent.tests.conftest import _register, _auth_header


def test_create_conversation(client):
    token = _register(client).json()["token"]
    r = client.post("/api/v1/service/conversations", json={
        "message": "I need help with payments", "labels": ["question"],
    }, headers=_auth_header(token))
    assert r.status_code == 200
    data = r.json()
    assert data["conversation"]["status"] == "open"
    assert data["message"]["role"] == "user"


def test_list_conversations(client):
    token = _register(client).json()["token"]
    h = _auth_header(token)
    client.post("/api/v1/service/conversations", json={"message": "q1"}, headers=h)
    client.post("/api/v1/service/conversations", json={"message": "q2"}, headers=h)
    r = client.get("/api/v1/service/conversations", headers=h)
    assert r.status_code == 200
    assert len(r.json()["conversations"]) == 2


def test_send_message(client):
    token = _register(client).json()["token"]
    h = _auth_header(token)
    conv_id = client.post("/api/v1/service/conversations", json={"message": "hello"}, headers=h).json()["conversation"]["id"]
    r = client.post(f"/api/v1/service/conversations/{conv_id}/messages", json={"content": "follow up"}, headers=h)
    assert r.status_code == 200
    assert r.json()["role"] == "user"


def test_close_and_reopen_on_message(client):
    token = _register(client).json()["token"]
    h = _auth_header(token)
    conv_id = client.post("/api/v1/service/conversations", json={"message": "hi"}, headers=h).json()["conversation"]["id"]
    client.post(f"/api/v1/service/conversations/{conv_id}/close", headers=h)
    detail = client.get(f"/api/v1/service/conversations/{conv_id}", headers=h).json()
    assert detail["status"] == "closed"
    client.post(f"/api/v1/service/conversations/{conv_id}/messages", json={"content": "reopen"}, headers=h)
    detail = client.get(f"/api/v1/service/conversations/{conv_id}", headers=h).json()
    assert detail["status"] == "open"


def test_update_labels(client):
    token = _register(client).json()["token"]
    h = _auth_header(token)
    conv_id = client.post("/api/v1/service/conversations", json={"message": "hi"}, headers=h).json()["conversation"]["id"]
    r = client.put(f"/api/v1/service/conversations/{conv_id}/labels", json={"labels": ["bug", "urgent"]}, headers=h)
    assert r.status_code == 200
    assert r.json()["labels"] == ["bug", "urgent"]
