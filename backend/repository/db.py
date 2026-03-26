"""
DuckDB connection management + schema initialization.

DuckDB 是统一存储层，各数据源 (Claude Agent SDK, OpenCode, …)
通过各自的 adapter 把会话同步写入这里。
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

_DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "agent.duckdb"),
)

_conn: duckdb.DuckDBPyConnection | None = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(_DB_PATH)
        _init_schema(_conn)
    return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          VARCHAR PRIMARY KEY,
            title       VARCHAR NOT NULL,
            path        VARCHAR NOT NULL,       -- 所属目录，如 '/agent-service'
            source      VARCHAR NOT NULL DEFAULT 'unknown',  -- 数据来源: 'claude', 'opencode', ...
            created_at  TIMESTAMP NOT NULL,
            updated_at  TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          VARCHAR PRIMARY KEY,
            session_id  VARCHAR NOT NULL REFERENCES sessions(id),
            role        VARCHAR NOT NULL,        -- 'user' | 'assistant'
            content     VARCHAR NOT NULL,
            created_at  TIMESTAMP NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_path ON sessions(path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
