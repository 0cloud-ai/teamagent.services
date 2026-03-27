"""
Harness Repository — 引擎、绑定、配置的增删改查。
"""

from __future__ import annotations

import json

from repository.db import get_conn


def _engine_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "supported_vendors": json.loads(row[3]) if row[3] else [],
    }


def _attach_bindings(conn, engine: dict) -> dict:
    """Attach bindings (with provider vendor/model info) to an engine dict."""
    rows = conn.execute(
        """
        SELECT b.engine_id, b.provider_id, b.role, p.vendor, p.model
        FROM harness_bindings b
        LEFT JOIN providers p ON p.id = b.provider_id
        WHERE b.engine_id = ?
        """,
        [engine["id"]],
    ).fetchall()
    engine["bindings"] = [
        {
            "engine_id": r[0],
            "provider_id": r[1],
            "role": r[2],
            "vendor": r[3],
            "model": r[4],
        }
        for r in rows
    ]
    return engine


def list_engines() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, description, supported_vendors FROM harness_engines ORDER BY id"
    ).fetchall()
    engines = [_engine_row_to_dict(r) for r in rows]
    for e in engines:
        _attach_bindings(conn, e)
    return engines


def get_engine(engine_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, name, description, supported_vendors FROM harness_engines WHERE id = ?",
        [engine_id],
    ).fetchone()
    if row is None:
        return None
    engine = _engine_row_to_dict(row)
    _attach_bindings(conn, engine)
    return engine


def get_default_engine() -> str:
    conn = get_conn()
    row = conn.execute(
        "SELECT value FROM harness_config WHERE key = 'default_engine'"
    ).fetchone()
    if row is None:
        return "claude-agent-sdk"  # fallback default
    return row[0]


def set_default_engine(engine_id: str) -> None:
    conn = get_conn()
    # Upsert: try update first, insert if no rows matched
    existing = conn.execute(
        "SELECT 1 FROM harness_config WHERE key = 'default_engine'"
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE harness_config SET value = ? WHERE key = 'default_engine'",
            [engine_id],
        )
    else:
        conn.execute(
            "INSERT INTO harness_config (key, value) VALUES ('default_engine', ?)",
            [engine_id],
        )


def add_binding(engine_id: str, provider_id: str, role: str = "default") -> dict:
    conn = get_conn()
    conn.execute(
        "INSERT INTO harness_bindings (engine_id, provider_id, role) VALUES (?, ?, ?)",
        [engine_id, provider_id, role],
    )
    return {"engine_id": engine_id, "provider_id": provider_id, "role": role}


def update_binding(engine_id: str, provider_id: str, role: str) -> dict | None:
    conn = get_conn()
    existing = conn.execute(
        "SELECT 1 FROM harness_bindings WHERE engine_id = ? AND provider_id = ?",
        [engine_id, provider_id],
    ).fetchone()
    if existing is None:
        return None
    conn.execute(
        "UPDATE harness_bindings SET role = ? WHERE engine_id = ? AND provider_id = ?",
        [role, engine_id, provider_id],
    )
    return {"engine_id": engine_id, "provider_id": provider_id, "role": role}


def delete_binding(engine_id: str, provider_id: str) -> bool:
    conn = get_conn()
    existing = conn.execute(
        "SELECT 1 FROM harness_bindings WHERE engine_id = ? AND provider_id = ?",
        [engine_id, provider_id],
    ).fetchone()
    if existing is None:
        return False
    conn.execute(
        "DELETE FROM harness_bindings WHERE engine_id = ? AND provider_id = ?",
        [engine_id, provider_id],
    )
    return True
