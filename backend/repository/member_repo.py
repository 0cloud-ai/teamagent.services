"""
Member Repository — members table CRUD.
"""

from __future__ import annotations

from repository.db import get_conn

_COLUMNS = ("id", "type", "name", "user_id", "email", "role", "service_url", "status", "joined_at")


def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return dict(zip(_COLUMNS, row))


def list_members(type_filter: str | None = None) -> list[dict]:
    conn = get_conn()
    if type_filter:
        rows = conn.execute(
            "SELECT * FROM members WHERE type = ? ORDER BY joined_at DESC", [type_filter]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM members ORDER BY joined_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_member(member_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM members WHERE id = ?", [member_id]).fetchone()
    return _row_to_dict(row)


def create_member(
    id: str,
    type: str,
    name: str,
    joined_at,
    user_id: str | None = None,
    email: str | None = None,
    role: str = "member",
    service_url: str | None = None,
    status: str = "connected",
) -> dict:
    conn = get_conn()
    conn.execute(
        """INSERT INTO members (id, type, name, user_id, email, role, service_url, status, joined_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [id, type, name, user_id, email, role, service_url, status, joined_at],
    )
    row = conn.execute("SELECT * FROM members WHERE id = ?", [id]).fetchone()
    return _row_to_dict(row)


def update_member(member_id: str, **fields) -> dict | None:
    if not fields:
        return get_member(member_id)

    allowed = {"name", "email", "role", "service_url", "status"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_member(member_id)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [member_id]

    conn = get_conn()
    conn.execute(f"UPDATE members SET {set_clause} WHERE id = ?", params)
    return get_member(member_id)


def delete_member(member_id: str) -> bool:
    conn = get_conn()
    before = conn.execute("SELECT count(*) FROM members WHERE id = ?", [member_id]).fetchone()[0]
    if before == 0:
        return False
    conn.execute("DELETE FROM members WHERE id = ?", [member_id])
    return True


def count_owners() -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT count(*) FROM members WHERE type = 'user' AND role = 'owner'"
    ).fetchone()
    return row[0]


def get_member_by_user_id(user_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM members WHERE user_id = ?", [user_id]).fetchone()
    return _row_to_dict(row)
