"""
User Repository — users table CRUD.
"""

from __future__ import annotations

from repository.db import get_conn

_COLUMNS = ("id", "email", "name", "password", "created_at")


def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return dict(zip(_COLUMNS, row))


def create_user(id: str, email: str, name: str, password: str, created_at) -> dict:
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (id, email, name, password, created_at) VALUES (?, ?, ?, ?, ?)",
        [id, email, name, password, created_at],
    )
    row = conn.execute("SELECT * FROM users WHERE id = ?", [id]).fetchone()
    return _row_to_dict(row)


def get_by_email(email: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ?", [email]).fetchone()
    return _row_to_dict(row)


def get_by_id(user_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    return _row_to_dict(row)


def update_user(user_id: str, **fields) -> dict | None:
    if not fields:
        return get_by_id(user_id)

    allowed = {"email", "name"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_by_id(user_id)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [user_id]

    conn = get_conn()
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", params)
    return get_by_id(user_id)


def update_password(user_id: str, new_password: str) -> None:
    conn = get_conn()
    conn.execute("UPDATE users SET password = ? WHERE id = ?", [new_password, user_id])
