"""
Claude Agent SDK Adapter — 从 Claude Code 本地会话同步数据到 DuckDB。

这是众多数据源之一（其他还可以有 OpenCode 等），
每个 adapter 的职责就是：读取外部数据 → 写入统一的 DuckDB 存储。
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path

from claude_agent_sdk import get_session_messages, list_sessions

from repository.db import get_conn

logger = logging.getLogger(__name__)

SESSION_ROOT = Path(
    os.environ.get("SESSION_ROOT", Path.home())
).resolve()

SOURCE_NAME = "claude"


def _cwd_to_path(cwd: str) -> str:
    """将 cwd 绝对路径转为相对于 SESSION_ROOT 的路径。"""
    try:
        rel = Path(cwd).resolve().relative_to(SESSION_ROOT)
        return "/" + str(rel) if str(rel) != "." else "/"
    except ValueError:
        return cwd


def sync() -> int:
    """
    从 Claude Agent SDK 拉取所有会话，同步到 DuckDB。
    返回同步的会话数量。
    """
    conn = get_conn()
    raw_sessions = list_sessions()
    synced = 0

    for s in raw_sessions:
        path = _cwd_to_path(s.cwd)

        title = s.custom_title or s.summary or s.first_prompt or "Untitled"
        if len(title) > 80:
            title = title[:77] + "..."

        created = dt.datetime.fromtimestamp(s.created_at / 1000)
        updated = dt.datetime.fromtimestamp(s.last_modified / 1000)

        # Upsert session
        conn.execute("""
            INSERT INTO sessions (id, title, path, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                title = excluded.title,
                path = excluded.path,
                updated_at = excluded.updated_at
        """, [s.session_id, title, path, SOURCE_NAME, created, updated])

        # Sync messages
        try:
            msgs = get_session_messages(session_id=s.session_id)
        except Exception:
            logger.warning("Failed to load messages for session %s", s.session_id)
            continue

        for msg in msgs:
            role = msg.type if msg.type in ("user", "assistant") else "system"
            content = ""
            if isinstance(msg.message, dict):
                content = str(msg.message.get("content", ""))
            elif isinstance(msg.message, str):
                content = msg.message

            if len(content) > 10000:
                content = content[:10000]

            msg_created = created  # SDK 消息没有独立时间戳，用 session 时间

            conn.execute("""
                INSERT INTO messages (id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING
            """, [msg.uuid, s.session_id, role, content, msg_created])

        synced += 1

    logger.info("Claude SDK sync complete: %d sessions", synced)
    return synced
