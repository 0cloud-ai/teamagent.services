"""
Session Service — session lifecycle, messaging, and member management.
"""

from __future__ import annotations

import re
import uuid
import datetime as dt

from model.dto import (
    MessageDTO,
    PaginationDTO,
    SessionDTO,
    SessionListResponseDTO,
    SessionMemberDTO,
    SessionMessagesResponseDTO,
)
from repository import session_repo, stats_repo, harness_repo, service_inbox_repo


def _normalize(path: str) -> str:
    if not path or path == "/":
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/")


# ── List sessions ────────────────────────────────────────────────────


def list_sessions(
    path: str,
    cursor: str | None = None,
    limit: int = 20,
    sort: str = "updated_at",
) -> SessionListResponseDTO | None:
    path = _normalize(path)

    if path != "/" and not stats_repo.path_exists(path):
        return None

    result = session_repo.list_sessions(path, cursor=cursor, limit=limit, sort=sort)

    return SessionListResponseDTO(
        path=path,
        sessions=[
            SessionDTO(
                id=s["id"],
                title=s["title"],
                harness=s.get("harness", ""),
                members=s.get("members", []),
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                message_count=s["message_count"],
            )
            for s in result["sessions"]
        ],
        pagination=PaginationDTO(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            total=result["total"],
        ),
    )


# ── Create session ───────────────────────────────────────────────────


def create_session(
    path: str,
    title: str | None = None,
    harness: str | None = None,
    members: list[str] | None = None,
) -> SessionDTO:
    """Create a new session. Uses default harness if not specified."""
    now = dt.datetime.now(dt.timezone.utc)
    session_id = str(uuid.uuid4())
    path = _normalize(path)

    # Use default harness from config if not provided
    if harness is None:
        harness = harness_repo.get_default_engine()

    session_title = title or f"Session {session_id[:8]}"

    session = session_repo.create_session(
        id=session_id,
        title=session_title,
        path=path,
        harness=harness,
        created_at=now,
        updated_at=now,
    )

    # Add creator as first session member (if members provided)
    if members:
        for member_id in members:
            session_repo.add_session_member(
                session_id=session_id,
                member_id=member_id,
                joined_via="creator",
                joined_at=now,
            )

    # Re-fetch to include members
    session = session_repo.get_session(session_id)

    return SessionDTO(
        id=session["id"],
        title=session["title"],
        path=session.get("path"),
        harness=session.get("harness", ""),
        members=session.get("members", []),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=session["message_count"],
    )


# ── Messages ─────────────────────────────────────────────────────────


def get_session_messages(
    session_id: str,
    cursor: str | None = None,
    limit: int = 50,
    order: str = "asc",
) -> SessionMessagesResponseDTO | None:
    """Return session info with paginated messages, or None if session not found."""
    session = session_repo.get_session(session_id)
    if session is None:
        return None

    result = session_repo.list_messages(
        session_id=session_id,
        cursor=cursor,
        limit=limit,
        order=order,
    )

    return SessionMessagesResponseDTO(
        session_id=session_id,
        session=SessionDTO(
            id=session["id"],
            title=session["title"],
            path=session.get("path"),
            harness=session.get("harness", ""),
            members=session.get("members", []),
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=session["message_count"],
        ),
        messages=[
            MessageDTO(
                id=m["id"],
                type=m.get("type", "message"),
                role=m.get("role"),
                content=m.get("content"),
                actor=m.get("actor"),
                action=m.get("action"),
                target=m.get("target"),
                detail=m.get("detail"),
                created_at=m["created_at"],
            )
            for m in result["messages"]
        ],
        pagination=PaginationDTO(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            total=result["total"],
        ),
    )


def send_message(
    session_id: str,
    content: str,
    mentions: list[str] | None = None,
) -> MessageDTO:
    """Send a user message. Process mentions: auto-add members, create conversation refs."""
    now = dt.datetime.now(dt.timezone.utc)
    msg_id = str(uuid.uuid4())

    # Process mentions — auto-add mentioned members to session
    if mentions:
        current_members = session_repo._get_session_member_ids(session_id)
        for mention in mentions:
            # Handle conversation references (conv-xxx pattern)
            if mention.startswith("conv-"):
                conversation_id = mention
                service_inbox_repo.add_conversation_ref(
                    conversation_id=conversation_id,
                    session_id=session_id,
                    created_at=now,
                )
            else:
                # Auto-add member if not already present
                if mention not in current_members:
                    session_repo.add_session_member(
                        session_id=session_id,
                        member_id=mention,
                        joined_via="mention",
                        joined_at=now,
                    )

    msg = session_repo.add_message(
        id=msg_id,
        session_id=session_id,
        type="message",
        role="user",
        content=content,
        created_at=now,
    )

    return MessageDTO(
        id=msg["id"],
        type=msg.get("type", "message"),
        role=msg.get("role"),
        content=msg.get("content"),
        actor=msg.get("actor"),
        action=msg.get("action"),
        target=msg.get("target"),
        detail=msg.get("detail"),
        created_at=msg["created_at"],
    )


# ── Session Members ──────────────────────────────────────────────────


def list_session_members(session_id: str) -> list[SessionMemberDTO]:
    """Return all members of a session."""
    members = session_repo.list_session_members(session_id)
    return [
        SessionMemberDTO(
            id=m["id"],
            type=m["type"],
            name=m["name"],
            service_url=m.get("service_url"),
            status=m.get("status"),
            joined_at=m["joined_at"],
            joined_via=m["joined_via"],
        )
        for m in members
    ]


def add_session_member(
    session_id: str,
    member_id: str,
) -> SessionMemberDTO | None:
    """Add a member to the session. Creates a member_added event. Returns None if already present."""
    now = dt.datetime.now(dt.timezone.utc)

    result = session_repo.add_session_member(
        session_id=session_id,
        member_id=member_id,
        joined_via="manual",
        joined_at=now,
    )

    if result is None:
        return None

    # Create a member_added event
    event_id = str(uuid.uuid4())
    session_repo.add_message(
        id=event_id,
        session_id=session_id,
        type="event",
        actor=member_id,
        action="member_added",
        target=member_id,
        detail=result["name"],
        created_at=now,
    )

    return SessionMemberDTO(
        id=result["id"],
        type=result["type"],
        name=result["name"],
        service_url=result.get("service_url"),
        status=result.get("status"),
        joined_at=result["joined_at"],
        joined_via=result["joined_via"],
    )


def remove_session_member(
    session_id: str,
    member_id: str,
) -> bool:
    """Remove a member from the session. Creates a member_removed event."""
    now = dt.datetime.now(dt.timezone.utc)

    # Get member info before removing (for the event detail)
    members = session_repo.list_session_members(session_id)
    member_name = None
    for m in members:
        if m["id"] == member_id:
            member_name = m["name"]
            break

    removed = session_repo.remove_session_member(session_id, member_id)

    if removed and member_name is not None:
        # Create a member_removed event
        event_id = str(uuid.uuid4())
        session_repo.add_message(
            id=event_id,
            session_id=session_id,
            type="event",
            actor=member_id,
            action="member_removed",
            target=member_id,
            detail=member_name,
            created_at=now,
        )

    return removed
