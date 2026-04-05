from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from teamagent.harness.engine import HarnessEngine
from teamagent.harness.types import FileWatcher, ProviderInfo, Record


class ClaudeCLIEngine(HarnessEngine):
    id = "claude-code-cli"
    name = "Claude Code CLI"
    api_formats = ["anthropic"]

    def submit(self, path: str, message: str, provider: ProviderInfo) -> FileWatcher:
        sid = str(uuid.uuid4())
        subprocess.Popen(
            [
                "claude", "-p",
                "--session-id", sid,
                "--cwd", path,
                "--model", provider.model_id,
                message,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        slug = path.lstrip("/").replace("/", "-")
        jsonl_path = str(Path.home() / ".claude" / "projects" / slug / f"{sid}.jsonl")
        return FileWatcher(session_id=sid, file_path=jsonl_path)

    def watch(self, event) -> list[Record] | None:
        """event 是 FileChangeEvent，遍历 new_lines 转换。"""
        results = []
        for line in event.new_lines:
            msg_type = line.get("type")
            if msg_type == "assistant":
                message = line.get("message", {})
                content_blocks = message.get("content", [])
                text_parts = []
                for block in content_blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                content = "\n".join(text_parts)
                is_done = line.get("stop_reason") == "end_turn"
                results.append(Record(role="assistant", content=content, done=is_done))
            elif msg_type == "tool_use":
                tool_input = line.get("input", {})
                results.append(Record(
                    type="event",
                    actor="agent",
                    action=line.get("tool", ""),
                    target=tool_input.get("file_path", tool_input.get("path", tool_input.get("command", ""))),
                ))
        return results or None
