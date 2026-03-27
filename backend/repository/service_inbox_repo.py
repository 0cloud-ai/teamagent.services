"""
Service Inbox Repository — workspace-level conversation queries with consumer info.
"""

from __future__ import annotations

import json

from repository.db import get_conn


def list_inbox(
    status: str | None = None,
    label: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    conn = get_conn()

    # ── Build WHERE clause ────────────────────────────────────────────
    conditions: list[str] = []
    params: list = []

    if status is not None:
        conditions.append("c.status = ?")
        params.append(status)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total = conn.execute(
        f"SELECT count(*) FROM conversations c{where}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"""
        SELECT c.id, c.title, c.consumer_id, c.status, c.labels,
               c.closed_at, c.created_at, c.updated_at,
               u.id AS user_id, u.name AS user_name
        FROM conversations c
        LEFT JOIN users u ON u.id = c.consumer_id
        {where}
        ORDER BY c.updated_at DESC, c.id DESC
        """,
        params,
    ).fetchall()

    # ── Label filter (in-app, labels stored as JSON array) ────────────
    if label is not None:
        rows = [r for r in rows if label in json.loads(r[4])]
        total = len(rows)

    # ── Cursor pagination ─────────────────────────────────────────────
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

    conversations = [_row_to_inbox_item(r) for r in page]

    return {
        "conversations": conversations,
        "has_more": has_more,
        "next_cursor": conversations[-1]["id"] if has_more and conversations else None,
        "total": total,
    }


def get_inbox_detail(conversation_id: str) -> dict | None:
    conn = get_conn()

    row = conn.execute(
        """
        SELECT c.id, c.title, c.consumer_id, c.status, c.labels,
               c.closed_at, c.created_at, c.updated_at,
               u.id AS user_id, u.name AS user_name
        FROM conversations c
        LEFT JOIN users u ON u.id = c.consumer_id
        WHERE c.id = ?
        """,
        [conversation_id],
    ).fetchone()

    if row is None:
        return None

    item = _row_to_inbox_item(row)
    item["referenced_by"] = get_refs_for_conversation(conversation_id)
    return item


def add_conversation_ref(conversation_id: str, session_id: str, created_at) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO conversation_refs (conversation_id, session_id, created_at)
        VALUES (?, ?, ?)
        """,
        [conversation_id, session_id, created_at],
    )


def get_refs_for_conversation(conversation_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT cr.session_id, s.title
        FROM conversation_refs cr
        LEFT JOIN sessions s ON s.id = cr.session_id
        WHERE cr.conversation_id = ?
        ORDER BY cr.created_at ASC
        """,
        [conversation_id],
    ).fetchall()
    return [{"session_id": r[0], "session_title": r[1]} for r in rows]


# ── Helpers ───────────────────────────────────────────────────────────


def _row_to_inbox_item(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "consumer_id": row[2],
        "status": row[3],
        "labels": json.loads(row[4]),
        "closed_at": row[5],
        "created_at": row[6],
        "updated_at": row[7],
        "consumer": {
            "user_id": row[8],
            "name": row[9],
        },
    }
