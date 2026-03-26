"""
Stats Repository — 用 SQL 聚合计算目录统计。

核心思路：session.path 字段是目录路径（如 '/work/alibaba/k8s'），
通过 LIKE 前缀匹配实现递归统计，无需在 Python 里递归遍历。
"""

from __future__ import annotations

from repository.db import get_conn


def path_exists(path: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE path = ? OR path LIKE ? LIMIT 1",
        [path, path.rstrip("/") + "/%"],
    ).fetchone()
    return row is not None


def direct_counts(path: str) -> dict:
    conn = get_conn()
    row = conn.execute("""
        SELECT
            count(DISTINCT s.id)    AS sessions,
            count(m.id)             AS messages
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ?
    """, [path]).fetchone()

    sessions = row[0]
    messages = row[1]

    prefix = path.rstrip("/") + "/"
    children = conn.execute("""
        SELECT count(DISTINCT split_part(substr(path, length(?)+1), '/', 1))
        FROM sessions
        WHERE path LIKE ?
    """, [prefix, prefix + "%"]).fetchone()

    directories = children[0]

    return {"directories": directories, "sessions": sessions, "messages": messages}


def total_counts(path: str) -> dict:
    conn = get_conn()
    prefix = path.rstrip("/") + "/"
    row = conn.execute("""
        SELECT
            count(DISTINCT s.id)    AS sessions,
            count(m.id)             AS messages
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ? OR s.path LIKE ?
    """, [path, prefix + "%"]).fetchone()

    sessions = row[0]
    messages = row[1]

    all_paths = conn.execute(
        "SELECT DISTINCT path FROM sessions WHERE path LIKE ?",
        [prefix + "%"],
    ).fetchall()

    dir_set: set[str] = set()
    for (p,) in all_paths:
        rel = p[len(path):].strip("/")
        parts = rel.split("/")
        for i in range(len(parts)):
            dir_set.add("/".join(parts[: i + 1]))

    directories = len(dir_set)

    return {"directories": directories, "sessions": sessions, "messages": messages}


def child_stats(path: str) -> list[dict]:
    conn = get_conn()
    prefix = path.rstrip("/") + "/"

    rows = conn.execute("""
        SELECT DISTINCT split_part(substr(path, length(?)+1), '/', 1) AS child_name
        FROM sessions
        WHERE path LIKE ?
        ORDER BY child_name
    """, [prefix, prefix + "%"]).fetchall()

    results = []
    for (name,) in rows:
        child_path = path.rstrip("/") + "/" + name
        results.append({
            "name": name,
            "total": total_counts(child_path),
        })

    return results
