"""
Conversation Repository — conversation & message CRUD with cursor pagination.
"""

from __future__ import annotations

import json

from repository.db import get_conn


def list_conversations(
    consumer_id: str | None = None,
    status: str | None = None,
    label: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    conn = get_conn()

    # ── Build WHERE clause ────────────────────────────────────────────
    conditions: list[str] = []
    params: list = []

    if consumer_id is not None:
        conditions.append("c.consumer_id = ?")
        params.append(consumer_id)
    if status is not None:
        conditions.append("c.status = ?")
        params.append(status)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    # Total count (before label filter, which is done in-app on JSON)
    total = conn.execute(
        f"SELECT count(*) FROM conversations c{where}", params
    ).fetchone()[0]

    rows = conn.execute(
        f"""
        SELECT c.id, c.title, c.consumer_id, c.status, c.labels,
               c.closed_at, c.created_at, c.updated_at
        FROM conversations c
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

    conversations = [_row_to_conversation(r) for r in page]

    return {
        "conversations": conversations,
        "has_more": has_more,
        "next_cursor": conversations[-1]["id"] if has_more and conversations else None,
        "total": total,
    }


def get_conversation(conversation_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, title, consumer_id, status, labels,
               closed_at, created_at, updated_at
        FROM conversations
        WHERE id = ?
        """,
        [conversation_id],
    ).fetchone()
    if row is None:
        return None
    return _row_to_conversation(row)


def create_conversation(
    id: str,
    title: str,
    consumer_id: str,
    status: str,
    labels: list,
    created_at,
    updated_at,
) -> dict:
    conn = get_conn()
    labels_json = json.dumps(labels)
    conn.execute(
        """
        INSERT INTO conversations (id, title, consumer_id, status, labels, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [id, title, consumer_id, status, labels_json, created_at, updated_at],
    )
    return get_conversation(id)


def update_conversation(conversation_id: str, **fields) -> dict | None:
    conn = get_conn()

    if not fields:
        return get_conversation(conversation_id)

    # Convert labels list to JSON string if present
    if "labels" in fields and isinstance(fields["labels"], list):
        fields["labels"] = json.dumps(fields["labels"])

    set_parts: list[str] = []
    params: list = []
    for key, value in fields.items():
        set_parts.append(f"{key} = ?")
        params.append(value)

    params.append(conversation_id)
    conn.execute(
        f"UPDATE conversations SET {', '.join(set_parts)} WHERE id = ?",
        params,
    )
    return get_conversation(conversation_id)


# ── Messages ──────────────────────────────────────────────────────────


def list_messages(
    conversation_id: str,
    cursor: str | None = None,
    limit: int = 50,
    order: str = "asc",
) -> dict:
    conn = get_conn()

    total = conn.execute(
        "SELECT count(*) FROM conversation_messages WHERE conversation_id = ?",
        [conversation_id],
    ).fetchone()[0]

    order_dir = "ASC" if order == "asc" else "DESC"

    rows = conn.execute(
        f"""
        SELECT id, conversation_id, role, content, created_at
        FROM conversation_messages
        WHERE conversation_id = ?
        ORDER BY created_at {order_dir}, id {order_dir}
        """,
        [conversation_id],
    ).fetchall()

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

    messages = [_row_to_message(r) for r in page]

    return {
        "messages": messages,
        "has_more": has_more,
        "next_cursor": messages[-1]["id"] if has_more and messages else None,
        "total": total,
    }


def add_message(
    id: str,
    conversation_id: str,
    role: str,
    content: str,
    created_at,
) -> dict:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO conversation_messages (id, conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [id, conversation_id, role, content, created_at],
    )
    row = conn.execute(
        "SELECT id, conversation_id, role, content, created_at FROM conversation_messages WHERE id = ?",
        [id],
    ).fetchone()
    return _row_to_message(row)


def count_messages(conversation_id: str) -> int:
    conn = get_conn()
    return conn.execute(
        "SELECT count(*) FROM conversation_messages WHERE conversation_id = ?",
        [conversation_id],
    ).fetchone()[0]


# ── Helpers ───────────────────────────────────────────────────────────


def _row_to_conversation(row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "consumer_id": row[2],
        "status": row[3],
        "labels": json.loads(row[4]),
        "closed_at": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }


def _row_to_message(row) -> dict:
    return {
        "id": row[0],
        "conversation_id": row[1],
        "role": row[2],
        "content": row[3],
        "created_at": row[4],
    }
