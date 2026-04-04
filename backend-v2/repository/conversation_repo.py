import json
from pathlib import Path

from repository.file_utils import atomic_write, append_jsonl, read_jsonl, ensure_dir


class ConversationRepo:
    def __init__(self, base_path: Path):
        self._dir = base_path / "conversations"

    def _conv_dir(self, conv_id: str) -> Path:
        return self._dir / conv_id

    def create_conversation(self, conv: dict) -> None:
        d = self._conv_dir(conv["id"])
        ensure_dir(d)
        atomic_write(d / "conversation.json", conv)
        (d / "messages.jsonl").touch()

    def get_conversation(self, conv_id: str) -> dict | None:
        p = self._conv_dir(conv_id) / "conversation.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def list_conversations(
        self,
        status: str | None = None,
        label: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[dict], int]:
        if not self._dir.exists():
            return [], 0
        all_convs = []
        for d in self._dir.iterdir():
            if d.is_dir() and (d / "conversation.json").exists():
                c = json.loads((d / "conversation.json").read_text(encoding="utf-8"))
                if status and c.get("status") != status:
                    continue
                if label and label not in c.get("labels", []):
                    continue
                all_convs.append(c)
        all_convs.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
        total = len(all_convs)
        if cursor:
            idx = next((i for i, c in enumerate(all_convs) if c["id"] == cursor), -1)
            if idx >= 0:
                all_convs = all_convs[idx + 1:]
        return all_convs[:limit], total

    def update_conversation(self, conv_id: str, data: dict) -> dict | None:
        conv = self.get_conversation(conv_id)
        if conv is None:
            return None
        conv.update(data)
        atomic_write(self._conv_dir(conv_id) / "conversation.json", conv)
        return conv

    def append_message(self, conv_id: str, message: dict) -> None:
        append_jsonl(self._conv_dir(conv_id) / "messages.jsonl", message)

    def list_messages(
        self, conv_id: str, limit: int = 50, cursor: str | None = None, order: str = "asc"
    ) -> tuple[list[dict], int]:
        messages = read_jsonl(self._conv_dir(conv_id) / "messages.jsonl")
        total = len(messages)
        if order == "desc":
            messages = list(reversed(messages))
        if cursor:
            idx = next((i for i, m in enumerate(messages) if m["id"] == cursor), -1)
            if idx >= 0:
                messages = messages[idx + 1:]
        return messages[:limit], total
