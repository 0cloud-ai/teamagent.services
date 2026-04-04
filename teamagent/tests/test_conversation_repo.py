import pytest
from pathlib import Path

from teamagent.repository.conversation_repo import ConversationRepo


@pytest.fixture
def repo(tmp_path):
    conv_dir = tmp_path / "conversations"
    conv_dir.mkdir()
    return ConversationRepo(tmp_path)


def _make_conv(cid="conv-001", title="Test ticket", status="open"):
    return {
        "id": cid,
        "title": title,
        "status": status,
        "labels": [],
        "user_id": "user-001",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "closed_at": None,
        "message_count": 0,
    }


def test_create_and_get(repo):
    repo.create_conversation(_make_conv())
    result = repo.get_conversation("conv-001")
    assert result["title"] == "Test ticket"


def test_get_not_found(repo):
    assert repo.get_conversation("nope") is None


def test_list_conversations(repo):
    for i in range(3):
        repo.create_conversation(_make_conv(cid=f"conv-{i:03d}"))
    convs, total = repo.list_conversations(limit=10)
    assert len(convs) == 3
    assert total == 3


def test_list_filter_status(repo):
    repo.create_conversation(_make_conv(cid="conv-001", status="open"))
    repo.create_conversation(_make_conv(cid="conv-002", status="escalated"))
    repo.create_conversation(_make_conv(cid="conv-003", status="closed"))
    convs, total = repo.list_conversations(status="open", limit=10)
    assert len(convs) == 1
    assert convs[0]["id"] == "conv-001"


def test_list_filter_label(repo):
    c1 = _make_conv(cid="conv-001")
    c1["labels"] = ["bug"]
    c2 = _make_conv(cid="conv-002")
    c2["labels"] = ["feature"]
    repo.create_conversation(c1)
    repo.create_conversation(c2)
    convs, total = repo.list_conversations(label="bug", limit=10)
    assert len(convs) == 1


def test_update_conversation(repo):
    repo.create_conversation(_make_conv())
    repo.update_conversation("conv-001", {"status": "closed", "closed_at": "2026-01-02T00:00:00Z"})
    result = repo.get_conversation("conv-001")
    assert result["status"] == "closed"


def test_append_and_list_messages(repo):
    repo.create_conversation(_make_conv())
    repo.append_message("conv-001", {"id": "msg-001", "role": "user", "content": "hello", "created_at": "2026-01-01T00:00:00Z"})
    repo.append_message("conv-001", {"id": "msg-002", "role": "assistant", "content": "hi", "created_at": "2026-01-01T00:01:00Z"})
    messages, total = repo.list_messages("conv-001", limit=10)
    assert len(messages) == 2
    assert total == 2
