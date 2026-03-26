"""
Session Repository — 会话查询，游标分页。
"""

from __future__ import annotations

from repository.db import get_conn


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
        SELECT s.id, s.title, s.created_at, s.updated_at, count(m.id) AS message_count
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ?
        GROUP BY s.id, s.title, s.created_at, s.updated_at
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

    sessions = [
        {
            "id": r[0],
            "title": r[1],
            "created_at": r[2],
            "updated_at": r[3],
            "message_count": r[4],
        }
        for r in page
    ]

    return {
        "sessions": sessions,
        "has_more": has_more,
        "next_cursor": sessions[-1]["id"] if has_more and sessions else None,
        "total": total,
    }
