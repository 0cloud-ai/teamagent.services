"""
Claude Code CLI Adapter — 直接读取 ~/.claude/ 本地文件同步到 DuckDB。

不依赖 claude-agent-sdk，裸读 Claude Code 的本地存储结构：
  ~/.claude/projects/{project-slug}/{session-id}.jsonl  — 会话消息
  ~/.claude/history.jsonl                               — 会话元数据（prompt 历史）

适用场景：没装 claude-agent-sdk 或者想绕过 SDK 直接读原始数据。
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
from pathlib import Path

from repository.db import get_conn

logger = logging.getLogger(__name__)

CLAUDE_HOME = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
SOURCE_NAME = "claude-cli"


def _slug_to_cwd(slug: str) -> str:
    """将 project slug 还原为 cwd 路径。如 '-home-twwyzh-agent-service' → '/home/twwyzh/agent-service'"""
    return slug.replace("-", "/", 1).replace("-", "/")


def _cwd_to_path(cwd: str, root: Path | None = None) -> str:
    """将 cwd 转为相对路径。"""
    if root is None:
        root = Path.home()
    try:
        rel = Path(cwd).resolve().relative_to(root.resolve())
        return "/" + str(rel) if str(rel) != "." else "/"
    except ValueError:
        return cwd


def _parse_jsonl_sessions(project_dir: Path) -> list[dict]:
    """解析一个 project 目录下的所有 session JSONL 文件。"""
    sessions = []

    for jsonl_file in project_dir.glob("*.jsonl"):
        session_id = jsonl_file.stem
        # 跳过非 UUID 格式的文件
        if len(session_id) < 30:
            continue

        title = None
        first_user_msg = None
        created_at = None
        updated_at = None
        messages = []

        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    entry_type = entry.get("type")
                    raw_ts = entry.get("timestamp")
                    timestamp = None
                    if isinstance(raw_ts, (int, float)):
                        timestamp = raw_ts
                    elif isinstance(raw_ts, str):
                        try:
                            timestamp = float(raw_ts)
                        except ValueError:
                            pass

                    if timestamp:
                        ts = dt.datetime.fromtimestamp(timestamp / 1000)
                        if created_at is None or ts < created_at:
                            created_at = ts
                        if updated_at is None or ts > updated_at:
                            updated_at = ts

                    if entry_type in ("user", "assistant"):
                        msg = entry.get("message", {})
                        role = entry_type
                        content = ""

                        if isinstance(msg, dict):
                            raw = msg.get("content", "")
                            if isinstance(raw, str):
                                content = raw
                            elif isinstance(raw, list):
                                # 提取 text blocks
                                parts = []
                                for block in raw:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        parts.append(block.get("text", ""))
                                content = "\n".join(parts)
                        elif isinstance(msg, str):
                            content = msg

                        if content and len(content) > 10000:
                            content = content[:10000]

                        uuid = entry.get("uuid", f"{session_id}_{len(messages)}")

                        messages.append({
                            "id": uuid,
                            "role": role,
                            "content": content,
                            "created_at": ts if timestamp else (created_at or dt.datetime.now()),
                        })

                        if role == "user" and first_user_msg is None and content:
                            first_user_msg = content

        except Exception as e:
            logger.warning("Failed to parse %s: %s", jsonl_file, e)
            continue

        if not messages:
            continue

        if not title:
            title = first_user_msg or "Untitled"
        if len(title) > 80:
            title = title[:77] + "..."

        now = dt.datetime.now()
        sessions.append({
            "id": session_id,
            "title": title,
            "created_at": created_at or now,
            "updated_at": updated_at or now,
            "messages": messages,
        })

    return sessions


def sync() -> int:
    """
    扫描 ~/.claude/projects/ 下所有项目目录，
    解析 JSONL 会话文件，同步到 DuckDB。
    返回同步的会话数。
    """
    conn = get_conn()
    projects_dir = CLAUDE_HOME / "projects"

    if not projects_dir.is_dir():
        logger.warning("Claude projects dir not found: %s", projects_dir)
        return 0

    synced = 0

    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir() or project_dir.name == "__pycache__":
            continue

        # slug → cwd → relative path
        cwd = _slug_to_cwd(project_dir.name)
        path = _cwd_to_path(cwd)

        sessions = _parse_jsonl_sessions(project_dir)

        for s in sessions:
            # 跳过已被其他 adapter 同步过的 session
            exists = conn.execute(
                "SELECT 1 FROM sessions WHERE id = ?", [s["id"]]
            ).fetchone()
            if exists:
                continue

            conn.execute("""
                INSERT INTO sessions (id, title, path, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING
            """, [s["id"], s["title"], path, SOURCE_NAME, s["created_at"], s["updated_at"]])

            for msg in s["messages"]:
                conn.execute("""
                    INSERT INTO messages (id, session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO NOTHING
                """, [msg["id"], s["id"], msg["role"], msg["content"], msg["created_at"]])

            synced += 1

    logger.info("Claude CLI sync complete: %d sessions from %s", synced, projects_dir)
    return synced
