"""
Member Service — workspace member management (users and services).
"""

from __future__ import annotations

import datetime as dt
import uuid

from model.dto import MemberDTO
from repository import member_repo, user_repo


# ── helpers ──────────────────────────────────────────────────────────

def _member_dto(row: dict) -> MemberDTO:
    return MemberDTO(
        id=row["id"],
        type=row["type"],
        name=row["name"],
        email=row.get("email"),
        role=row.get("role"),
        service_url=row.get("service_url"),
        status=row.get("status"),
        joined_at=row["joined_at"],
    )


# ── public API ───────────────────────────────────────────────────────

def list_members(type_filter: str | None = None) -> list[MemberDTO]:
    rows = member_repo.list_members(type_filter=type_filter)
    return [_member_dto(r) for r in rows]


def add_member(
    type: str,
    name: str,
    email: str | None = None,
    role: str = "member",
    service_url: str | None = None,
) -> MemberDTO:
    member_id = str(uuid.uuid4())
    now = dt.datetime.utcnow()

    user_id = None
    status = None

    if type == "user" and email:
        user_row = user_repo.get_by_email(email)
        if user_row:
            user_id = user_row["id"]

    if type == "service":
        status = "connected"

    row = member_repo.create_member(
        id=member_id,
        type=type,
        name=name,
        joined_at=now,
        user_id=user_id,
        email=email,
        role=role,
        service_url=service_url,
        status=status or "active",
    )
    return _member_dto(row)


def update_member(member_id: str, **fields) -> MemberDTO | None:
    row = member_repo.update_member(member_id, **fields)
    if row is None:
        return None
    return _member_dto(row)


def remove_member(member_id: str) -> bool:
    existing = member_repo.get_member(member_id)
    if existing is None:
        return False

    # Prevent removing the last owner
    if existing.get("role") == "owner" and existing.get("type") == "user":
        if member_repo.count_owners() <= 1:
            return False

    return member_repo.delete_member(member_id)


def get_member(member_id: str) -> MemberDTO | None:
    row = member_repo.get_member(member_id)
    if row is None:
        return None
    return _member_dto(row)
