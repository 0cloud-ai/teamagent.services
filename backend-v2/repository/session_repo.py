import json
from pathlib import Path

from repository.file_utils import atomic_write, append_jsonl, read_jsonl, ensure_dir


class SessionRepo:
    def __init__(self, base_path: Path):
        self._base = base_path

    def _sessions_dir(self, path: Path) -> Path:
        return path / ".teamagent" / "sessions"

    def _session_dir(self, path: Path, session_id: str) -> Path:
        return self._sessions_dir(path) / session_id

    def create_session(self, path: Path, session: dict) -> None:
        d = self._session_dir(path, session["id"])
        ensure_dir(d)
        atomic_write(d / "session.json", session)
        (d / "messages.jsonl").touch()

    def get_session(self, path: Path, session_id: str) -> dict | None:
        p = self._session_dir(path, session_id) / "session.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def list_sessions(
        self, path: Path, sort: str = "updated_at", limit: int = 20, cursor: str | None = None
    ) -> tuple[list[dict], int]:
        sessions_dir = self._sessions_dir(path)
        if not sessions_dir.exists():
            return [], 0
        all_sessions = []
        for d in sessions_dir.iterdir():
            if d.is_dir() and (d / "session.json").exists():
                s = json.loads((d / "session.json").read_text(encoding="utf-8"))
                all_sessions.append(s)
        all_sessions.sort(key=lambda s: s.get(sort, ""), reverse=True)
        total = len(all_sessions)
        if cursor:
            idx = next((i for i, s in enumerate(all_sessions) if s["id"] == cursor), -1)
            if idx >= 0:
                all_sessions = all_sessions[idx + 1:]
        return all_sessions[:limit], total

    def update_session(self, path: Path, session_id: str, data: dict) -> dict | None:
        session = self.get_session(path, session_id)
        if session is None:
            return None
        session.update(data)
        atomic_write(self._session_dir(path, session_id) / "session.json", session)
        return session

    def append_message(self, path: Path, session_id: str, message: dict) -> None:
        append_jsonl(self._session_dir(path, session_id) / "messages.jsonl", message)

    def list_messages(
        self, path: Path, session_id: str, limit: int = 50, cursor: str | None = None, order: str = "asc"
    ) -> tuple[list[dict], int]:
        messages = read_jsonl(self._session_dir(path, session_id) / "messages.jsonl")
        total = len(messages)
        if order == "desc":
            messages = list(reversed(messages))
        if cursor:
            idx = next((i for i, m in enumerate(messages) if m["id"] == cursor), -1)
            if idx >= 0:
                messages = messages[idx + 1:]
        return messages[:limit], total
