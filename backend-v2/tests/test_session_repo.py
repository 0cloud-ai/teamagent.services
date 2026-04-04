import pytest
from pathlib import Path

from repository.session_repo import SessionRepo


@pytest.fixture
def repo(tmp_path):
    return SessionRepo(tmp_path)


def _make_session(sid="sess-001", title="Test", path="/project", harness="opencode"):
    return {
        "id": sid,
        "title": title,
        "path": path,
        "harness": harness,
        "members": [],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "message_count": 0,
    }


def test_create_and_get(repo, tmp_path):
    session = _make_session()
    session_path = tmp_path / "project"
    session_path.mkdir(parents=True)
    repo.create_session(session_path, session)
    result = repo.get_session(session_path, "sess-001")
    assert result["title"] == "Test"


def test_get_not_found(repo, tmp_path):
    assert repo.get_session(tmp_path, "nope") is None


def test_list_sessions(repo, tmp_path):
    session_path = tmp_path / "project"
    session_path.mkdir(parents=True)
    for i in range(3):
        repo.create_session(session_path, _make_session(
            sid=f"sess-{i:03d}",
            title=f"Session {i}",
        ))
    sessions, total = repo.list_sessions(session_path, sort="created_at", limit=10, cursor=None)
    assert len(sessions) == 3
    assert total == 3


def test_list_sessions_with_limit(repo, tmp_path):
    session_path = tmp_path / "project"
    session_path.mkdir(parents=True)
    for i in range(5):
        repo.create_session(session_path, _make_session(sid=f"sess-{i:03d}"))
    sessions, total = repo.list_sessions(session_path, sort="created_at", limit=2, cursor=None)
    assert len(sessions) == 2
    assert total == 5


def test_update_session(repo, tmp_path):
    session_path = tmp_path / "project"
    session_path.mkdir(parents=True)
    repo.create_session(session_path, _make_session())
    repo.update_session(session_path, "sess-001", {"title": "Updated"})
    result = repo.get_session(session_path, "sess-001")
    assert result["title"] == "Updated"


def test_append_and_list_messages(repo, tmp_path):
    session_path = tmp_path / "project"
    session_path.mkdir(parents=True)
    repo.create_session(session_path, _make_session())
    repo.append_message(session_path, "sess-001", {
        "id": "msg-001", "type": "message", "role": "user", "content": "hello", "created_at": "2026-01-01T00:00:00Z",
    })
    repo.append_message(session_path, "sess-001", {
        "id": "msg-002", "type": "message", "role": "assistant", "content": "hi", "created_at": "2026-01-01T00:01:00Z",
    })
    messages, total = repo.list_messages(session_path, "sess-001", limit=10, cursor=None, order="asc")
    assert len(messages) == 2
    assert total == 2
    assert messages[0]["id"] == "msg-001"


def test_list_messages_desc(repo, tmp_path):
    session_path = tmp_path / "project"
    session_path.mkdir(parents=True)
    repo.create_session(session_path, _make_session())
    for i in range(3):
        repo.append_message(session_path, "sess-001", {
            "id": f"msg-{i:03d}", "type": "message", "role": "user", "content": f"msg {i}", "created_at": f"2026-01-01T00:0{i}:00Z",
        })
    messages, total = repo.list_messages(session_path, "sess-001", limit=10, cursor=None, order="desc")
    assert messages[0]["id"] == "msg-002"
