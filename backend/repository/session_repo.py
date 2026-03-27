"""
Session Repository — 会话查询/创建，游标分页，消息，会话成员。
"""

from __future__ import annotations

import datetime as dt

from repository.db import get_conn


# ── List sessions ────────────────────────────────────────────────────

def list_sessions(
    path: str,
    cursor: str | None = None,
    limit: int = 20,
    sort: str = "updated_at",
) -> dict:
    conn = get_conn()

    total = conn.execute(
        "SELECT count(*) FROM sessions WHERE path = ?", [path]
    ).fetchone()[0]

    sort_col = sort if sort in ("updated_at", "created_at") else "updated_at"

    base_sql = f"""
        SELECT s.id, s.title, s.harness, s.created_at, s.updated_at, count(m.id) AS message_count
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ?
        GROUP BY s.id, s.title, s.harness, s.created_at, s.updated_at
        ORDER BY s.{sort_col} DESC, s.id DESC
    """

    rows = conn.execute(base_sql, [path]).fetchall()

    if cursor:
        found = False
        filtered = []
        for row in rows:
            if found:
                filtered.append(row)
            elif row[0] == cursor:
                found = True
        rows = filtered

    page = rows[:limit]
    has_more = len(rows) > limit

    sessions = []
    for r in page:
        members = _get_session_member_ids(r[0])
        sessions.append({
            "id": r[0],
            "title": r[1],
            "harness": r[2],
            "created_at": r[3],
            "updated_at": r[4],
            "message_count": r[5],
            "members": members,
        })

    return {
        "sessions": sessions,
        "has_more": has_more,
        "next_cursor": sessions[-1]["id"] if has_more and sessions else None,
        "total": total,
    }


# ── Create session ───────────────────────────────────────────────────

def create_session(
    id: str,
    title: str,
    path: str,
    harness: str,
    created_at: dt.datetime,
    updated_at: dt.datetime,
) -> dict:
    conn = get_conn()
    conn.execute(
        """INSERT INTO sessions (id, title, path, source, harness, created_at, updated_at)
           VALUES (?, ?, ?, 'workspace', ?, ?, ?)""",
        [id, title, path, harness, created_at, updated_at],
    )
    return get_session(id)


def get_session(session_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, title, path, harness, created_at, updated_at FROM sessions WHERE id = ?",
        [session_id],
    ).fetchone()
    if not row:
        return None
    msg_count = conn.execute(
        "SELECT count(*) FROM messages WHERE session_id = ?", [session_id]
    ).fetchone()[0]
    members = _get_session_member_ids(session_id)
    return {
        "id": row[0],
        "title": row[1],
        "path": row[2],
        "harness": row[3],
        "created_at": row[4],
        "updated_at": row[5],
        "message_count": msg_count,
        "members": members,
    }


# ── Messages ─────────────────────────────────────────────────────────

def list_messages(
    session_id: str,
    cursor: str | None = None,
    limit: int = 50,
    order: str = "asc",
) -> dict:
    conn = get_conn()

    total = conn.execute(
        "SELECT count(*) FROM messages WHERE session_id = ?", [session_id]
    ).fetchone()[0]

    direction = "ASC" if order == "asc" else "DESC"
    rows = conn.execute(
        f"""SELECT id, type, role, content, actor, action, target, detail, created_at
            FROM messages WHERE session_id = ?
            ORDER BY created_at {direction}, id {direction}""",
        [session_id],
    ).fetchall()

    if cursor:
        found = False
        filtered = []
        for row in rows:
            if found:
                filtered.append(row)
            elif row[0] == cursor:
                found = True
        rows = filtered

    page = rows[:limit]
    has_more = len(rows) > limit

    messages = [
        {
            "id": r[0],
            "type": r[1],
            "role": r[2],
            "content": r[3],
            "actor": r[4],
            "action": r[5],
            "target": r[6],
            "detail": r[7],
            "created_at": r[8],
        }
        for r in page
    ]

    return {
        "messages": messages,
        "has_more": has_more,
        "next_cursor": messages[-1]["id"] if has_more and messages else None,
        "total": total,
    }


def add_message(
    id: str,
    session_id: str,
    type: str = "message",
    role: str | None = None,
    content: str | None = None,
    actor: str | None = None,
    action: str | None = None,
    target: str | None = None,
    detail: str | None = None,
    created_at: dt.datetime | None = None,
) -> dict:
    conn = get_conn()
    now = created_at or dt.datetime.now()
    conn.execute(
        """INSERT INTO messages (id, session_id, type, role, content, actor, action, target, detail, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [id, session_id, type, role, content, actor, action, target, detail, now],
    )
    # Update session updated_at
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?", [now, session_id]
    )
    return {
        "id": id,
        "type": type,
        "role": role,
        "content": content,
        "actor": actor,
        "action": action,
        "target": target,
        "detail": detail,
        "created_at": now,
    }


# ── Session Members ──────────────────────────────────────────────────

def _get_session_member_ids(session_id: str) -> list[str]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT member_id FROM session_members WHERE session_id = ?", [session_id]
    ).fetchall()
    return [r[0] for r in rows]


def list_session_members(session_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """SELECT sm.member_id, m.type, m.name, m.service_url, m.status,
                  sm.joined_at, sm.joined_via
           FROM session_members sm
           JOIN members m ON m.id = sm.member_id
           WHERE sm.session_id = ?
           ORDER BY sm.joined_at ASC""",
        [session_id],
    ).fetchall()
    return [
        {
            "id": r[0],
            "type": r[1],
            "name": r[2],
            "service_url": r[3],
            "status": r[4],
            "joined_at": r[5],
            "joined_via": r[6],
        }
        for r in rows
    ]


def add_session_member(
    session_id: str,
    member_id: str,
    joined_via: str = "manual",
    joined_at: dt.datetime | None = None,
) -> dict | None:
    conn = get_conn()
    now = joined_at or dt.datetime.now()
    # Check if already a member
    existing = conn.execute(
        "SELECT 1 FROM session_members WHERE session_id = ? AND member_id = ?",
        [session_id, member_id],
    ).fetchone()
    if existing:
        return None
    conn.execute(
        "INSERT INTO session_members (session_id, member_id, joined_via, joined_at) VALUES (?, ?, ?, ?)",
        [session_id, member_id, joined_via, now],
    )
    # Get member info
    row = conn.execute(
        "SELECT id, type, name, service_url, status FROM members WHERE id = ?",
        [member_id],
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "type": row[1],
        "name": row[2],
        "service_url": row[3],
        "status": row[4],
        "joined_at": now,
        "joined_via": joined_via,
    }


def remove_session_member(session_id: str, member_id: str) -> bool:
    conn = get_conn()
    result = conn.execute(
        "DELETE FROM session_members WHERE session_id = ? AND member_id = ?",
        [session_id, member_id],
    )
    return result.fetchone() is not None if hasattr(result, 'fetchone') else True
