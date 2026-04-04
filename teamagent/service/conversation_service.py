import uuid
from datetime import datetime, timezone

from teamagent.repository.conversation_repo import ConversationRepo
from teamagent.repository.user_repo import UserRepo


class ConversationService:
    def __init__(self, conv_repo: ConversationRepo, user_repo: UserRepo):
        self._conv = conv_repo
        self._users = user_repo

    def create_conversation(self, user_id: str, message: str, labels: list[str] = []) -> dict:
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        title = message[:50] + ("..." if len(message) > 50 else "")
        conv = {
            "id": conv_id, "title": title, "status": "open", "labels": labels,
            "user_id": user_id, "created_at": now, "updated_at": now,
            "closed_at": None, "message_count": 1,
        }
        self._conv.create_conversation(conv)
        msg = {"id": f"msg-{uuid.uuid4().hex[:8]}", "role": "user", "content": message, "created_at": now}
        self._conv.append_message(conv_id, msg)
        return {"conversation": conv, "message": msg}

    def send_message(self, conv_id: str, content: str, role: str = "user") -> dict:
        conv = self._conv.get_conversation(conv_id)
        if conv is None:
            raise ValueError("Conversation not found")
        now = datetime.now(timezone.utc).isoformat()
        if conv["status"] == "closed":
            conv["status"] = "open"
            conv["closed_at"] = None
        msg = {"id": f"msg-{uuid.uuid4().hex[:8]}", "role": role, "content": content, "created_at": now}
        self._conv.append_message(conv_id, msg)
        conv["updated_at"] = now
        conv["message_count"] = conv.get("message_count", 0) + 1
        self._conv.update_conversation(conv_id, conv)
        return msg

    def get_conversation(self, conv_id: str) -> dict | None:
        return self._conv.get_conversation(conv_id)

    def get_detail(self, conv_id: str, limit: int = 50, cursor: str | None = None, order: str = "asc") -> dict:
        conv = self._conv.get_conversation(conv_id)
        if conv is None:
            raise ValueError("Conversation not found")
        messages, total = self._conv.list_messages(conv_id, limit=limit, cursor=cursor, order=order)
        has_more = len(messages) < total and len(messages) == limit
        next_cursor = messages[-1]["id"] if has_more else None
        return {**conv, "messages": messages, "pagination": {"next_cursor": next_cursor, "has_more": has_more, "total": total}}

    def get_workspace_detail(self, conv_id: str, limit: int = 50, cursor: str | None = None) -> dict:
        detail = self.get_detail(conv_id, limit=limit, cursor=cursor)
        user = self._users.get_user_by_id(detail.get("user_id", ""))
        consumer = {"user_id": detail.get("user_id", ""), "name": user["name"] if user else "Unknown"}
        detail["consumer"] = consumer
        detail["referenced_by"] = []
        return detail

    def list_conversations(self, status: str | None = None, label: str | None = None, limit: int = 20, cursor: str | None = None, user_id: str | None = None) -> dict:
        convs, total = self._conv.list_conversations(status=status, label=label, limit=limit, cursor=cursor)
        if user_id:
            convs = [c for c in convs if c.get("user_id") == user_id]
            total = len(convs)
        has_more = len(convs) < total and len(convs) == limit
        next_cursor = convs[-1]["id"] if has_more and convs else None
        return {"conversations": convs, "pagination": {"next_cursor": next_cursor, "has_more": has_more, "total": total}}

    def list_workspace_conversations(self, status: str | None = None, label: str | None = None, limit: int = 20, cursor: str | None = None) -> dict:
        result = self.list_conversations(status=status, label=label, limit=limit, cursor=cursor)
        for conv in result["conversations"]:
            user = self._users.get_user_by_id(conv.get("user_id", ""))
            conv["consumer"] = {"user_id": conv.get("user_id", ""), "name": user["name"] if user else "Unknown"}
        return result

    def escalate(self, conv_id: str, reason: str | None = None) -> dict:
        conv = self._conv.get_conversation(conv_id)
        if conv is None:
            raise ValueError("Conversation not found")
        conv["status"] = "escalated"
        conv["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._conv.update_conversation(conv_id, conv)
        return conv

    def close(self, conv_id: str) -> dict:
        conv = self._conv.get_conversation(conv_id)
        if conv is None:
            raise ValueError("Conversation not found")
        now = datetime.now(timezone.utc).isoformat()
        conv["status"] = "closed"
        conv["closed_at"] = now
        conv["updated_at"] = now
        self._conv.update_conversation(conv_id, conv)
        return conv

    def reopen(self, conv_id: str) -> dict:
        conv = self._conv.get_conversation(conv_id)
        if conv is None:
            raise ValueError("Conversation not found")
        conv["status"] = "open"
        conv["closed_at"] = None
        conv["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._conv.update_conversation(conv_id, conv)
        return conv

    def update_labels(self, conv_id: str, labels: list[str]) -> dict:
        conv = self._conv.get_conversation(conv_id)
        if conv is None:
            raise ValueError("Conversation not found")
        conv["labels"] = labels
        conv["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._conv.update_conversation(conv_id, conv)
        return conv
