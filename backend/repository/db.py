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


def reset_conn() -> None:
    """Close and reset the connection. Used in tests."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def get_test_conn() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB for testing."""
    global _conn
    _conn = duckdb.connect(":memory:")
    _init_schema(_conn)
    return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    # ── Users ────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          VARCHAR PRIMARY KEY,
            email       VARCHAR NOT NULL UNIQUE,
            name        VARCHAR NOT NULL,
            password    VARCHAR NOT NULL,
            created_at  TIMESTAMP NOT NULL
        )
    """)

    # ── Members ──────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id          VARCHAR PRIMARY KEY,
            type        VARCHAR NOT NULL,            -- 'user' | 'service'
            name        VARCHAR NOT NULL,
            -- type=user fields
            user_id     VARCHAR,                     -- FK to users.id
            email       VARCHAR,
            role        VARCHAR DEFAULT 'member',    -- 'owner' | 'member'
            -- type=service fields
            service_url VARCHAR,
            status      VARCHAR DEFAULT 'connected', -- 'connected' | 'disconnected'
            --
            joined_at   TIMESTAMP NOT NULL
        )
    """)

    # ── Providers (LLM 供应商) ───────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id          VARCHAR PRIMARY KEY,
            vendor      VARCHAR NOT NULL,             -- 'anthropic' | 'openai' | ...
            model       VARCHAR NOT NULL,
            api_base    VARCHAR NOT NULL,
            api_key     VARCHAR,
            status      VARCHAR NOT NULL DEFAULT 'unknown',
            created_at  TIMESTAMP NOT NULL
        )
    """)

    # ── Harness Engines ──────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS harness_engines (
            id                  VARCHAR PRIMARY KEY,
            name                VARCHAR NOT NULL,
            description         VARCHAR NOT NULL DEFAULT '',
            supported_vendors   VARCHAR NOT NULL DEFAULT '[]'  -- JSON array
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS harness_bindings (
            engine_id   VARCHAR NOT NULL REFERENCES harness_engines(id),
            provider_id VARCHAR NOT NULL REFERENCES providers(id),
            role        VARCHAR NOT NULL DEFAULT 'default',  -- 'default'|'reasoning'|'fast'|'local'
            PRIMARY KEY (engine_id, provider_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS harness_config (
            key   VARCHAR PRIMARY KEY,
            value VARCHAR NOT NULL
        )
    """)

    # ── Sessions (扩展) ──────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          VARCHAR PRIMARY KEY,
            title       VARCHAR NOT NULL,
            path        VARCHAR NOT NULL,
            source      VARCHAR NOT NULL DEFAULT 'unknown',
            harness     VARCHAR NOT NULL DEFAULT '',
            created_at  TIMESTAMP NOT NULL,
            updated_at  TIMESTAMP NOT NULL
        )
    """)

    # ── Messages ─────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          VARCHAR PRIMARY KEY,
            session_id  VARCHAR NOT NULL REFERENCES sessions(id),
            type        VARCHAR NOT NULL DEFAULT 'message',  -- 'message' | 'event'
            role        VARCHAR,                              -- 'user' | 'assistant' (type=message)
            content     VARCHAR,                              -- (type=message)
            actor       VARCHAR,                              -- (type=event)
            action      VARCHAR,                              -- (type=event)
            target      VARCHAR,                              -- (type=event)
            detail      VARCHAR,                              -- (type=event)
            created_at  TIMESTAMP NOT NULL
        )
    """)

    # ── Session Members ──────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_members (
            session_id  VARCHAR NOT NULL REFERENCES sessions(id),
            member_id   VARCHAR NOT NULL REFERENCES members(id),
            joined_via  VARCHAR NOT NULL DEFAULT 'manual',  -- 'creator'|'mention'|'manual'
            joined_at   TIMESTAMP NOT NULL,
            PRIMARY KEY (session_id, member_id)
        )
    """)

    # ── Conversations (服务工单) ─────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id          VARCHAR PRIMARY KEY,
            title       VARCHAR NOT NULL,
            consumer_id VARCHAR NOT NULL REFERENCES users(id),
            status      VARCHAR NOT NULL DEFAULT 'open',  -- 'open'|'escalated'|'closed'
            labels      VARCHAR NOT NULL DEFAULT '[]',    -- JSON array
            closed_at   TIMESTAMP,
            created_at  TIMESTAMP NOT NULL,
            updated_at  TIMESTAMP NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id              VARCHAR PRIMARY KEY,
            conversation_id VARCHAR NOT NULL,
            role            VARCHAR NOT NULL,  -- 'user' | 'assistant'
            content         VARCHAR NOT NULL,
            created_at      TIMESTAMP NOT NULL
        )
    """)

    # ── Conversation ↔ Session references ────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversation_refs (
            conversation_id VARCHAR NOT NULL,
            session_id      VARCHAR NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            PRIMARY KEY (conversation_id, session_id)
        )
    """)

    # ── Service Info ─────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS service_info (
            key   VARCHAR PRIMARY KEY,
            value VARCHAR NOT NULL
        )
    """)

    # ── Indexes ──────────────────────────────────────────────────────
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_path ON sessions(path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_members_type ON members(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_members_user_id ON members(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_consumer ON conversations(consumer_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_messages_conv ON conversation_messages(conversation_id)")

    # ── Seed default harness engines ─────────────────────────────────
    for engine_id, name, desc, vendors in [
        ("claude-agent-sdk", "Claude Agent SDK", "Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行", '["anthropic"]'),
        ("claude-code-cli", "Claude Code CLI", "Claude Code CLI 模式，贴近本地开发体验", '["anthropic"]'),
        ("opencode", "OpenCode", "开源 code agent 引擎，支持多种大模型供应商", '["anthropic","openai","deepseek","google","ollama"]'),
        ("openclaw", "OpenClaw", "开源多模态 agent 引擎", '["anthropic","openai"]'),
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO harness_engines (id, name, description, supported_vendors) VALUES (?, ?, ?, ?)",
            [engine_id, name, desc, vendors],
        )

    # Seed default harness config
    conn.execute(
        "INSERT OR IGNORE INTO harness_config (key, value) VALUES ('default_engine', 'claude-agent-sdk')"
    )
