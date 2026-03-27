"""
Service Inbox Service — workspace-level conversation management (escalate, close, reopen, labels).
"""

from __future__ import annotations

import datetime as dt

from model.dto import (
    ConsumerInfoDTO,
    ConversationMessageDTO,
    InboxConversationDTO,
    InboxConversationDetailDTO,
    PaginationDTO,
    SessionRefDTO,
)
from repository import conversation_repo, service_inbox_repo


def _to_inbox_dto(c: dict) -> InboxConversationDTO:
    return InboxConversationDTO(
        id=c["id"],
        title=c["title"],
        consumer=ConsumerInfoDTO(
            user_id=c["consumer"]["user_id"],
            name=c["consumer"]["name"],
        ),
        status=c["status"],
        labels=c.get("labels", []),
        closed_at=c.get("closed_at"),
        created_at=c["created_at"],
        updated_at=c["updated_at"],
        message_count=conversation_repo.count_messages(c["id"]),
    )


# ── Public API ───────────────────────────────────────────────────────


def list_inbox(
    status: str | None = None,
    label: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    result = service_inbox_repo.list_inbox(
        status=status,
        label=label,
        cursor=cursor,
        limit=limit,
    )

    conversations = [_to_inbox_dto(c) for c in result["conversations"]]

    return {
        "conversations": conversations,
        "pagination": PaginationDTO(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            total=result["total"],
        ),
    }


def get_inbox_detail(conversation_id: str) -> InboxConversationDetailDTO | None:
    detail = service_inbox_repo.get_inbox_detail(conversation_id)
    if detail is None:
        return None

    # Fetch messages for the conversation
    msg_result = conversation_repo.list_messages(conversation_id)

    messages = [
        ConversationMessageDTO(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            created_at=m["created_at"],
        )
        for m in msg_result["messages"]
    ]

    referenced_by = [
        SessionRefDTO(
            session_id=ref["session_id"],
            session_title=ref["session_title"],
        )
        for ref in detail.get("referenced_by", [])
    ]

    return InboxConversationDetailDTO(
        id=detail["id"],
        title=detail["title"],
        consumer=ConsumerInfoDTO(
            user_id=detail["consumer"]["user_id"],
            name=detail["consumer"]["name"],
        ),
        status=detail["status"],
        labels=detail.get("labels", []),
        closed_at=detail.get("closed_at"),
        created_at=detail["created_at"],
        updated_at=detail["updated_at"],
        message_count=msg_result["total"],
        messages=messages,
        referenced_by=referenced_by,
        pagination=PaginationDTO(
            next_cursor=msg_result["next_cursor"],
            has_more=msg_result["has_more"],
            total=msg_result["total"],
        ),
    )


def escalate(conversation_id: str, reason: str | None = None) -> InboxConversationDetailDTO | None:
    conv = conversation_repo.get_conversation(conversation_id)
    if conv is None:
        return None

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    fields: dict = {"status": "escalated", "updated_at": now}

    conversation_repo.update_conversation(conversation_id, **fields)
    return get_inbox_detail(conversation_id)


def close(conversation_id: str) -> InboxConversationDetailDTO | None:
    conv = conversation_repo.get_conversation(conversation_id)
    if conv is None:
        return None

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    conversation_repo.update_conversation(
        conversation_id,
        status="closed",
        closed_at=now,
        updated_at=now,
    )
    return get_inbox_detail(conversation_id)


def reopen(conversation_id: str) -> InboxConversationDetailDTO | None:
    conv = conversation_repo.get_conversation(conversation_id)
    if conv is None:
        return None

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    conversation_repo.update_conversation(
        conversation_id,
        status="open",
        closed_at=None,
        updated_at=now,
    )
    return get_inbox_detail(conversation_id)


def update_labels(conversation_id: str, labels: list[str]) -> InboxConversationDetailDTO | None:
    conv = conversation_repo.get_conversation(conversation_id)
    if conv is None:
        return None

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    conversation_repo.update_conversation(
        conversation_id,
        labels=labels,
        updated_at=now,
    )
    return get_inbox_detail(conversation_id)
