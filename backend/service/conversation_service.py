"""
Conversation Service — consumer-facing conversation management.
"""

from __future__ import annotations

import uuid
import datetime as dt
import json

from model.dto import (
    ConversationDTO,
    ConversationDetailDTO,
    ConversationMessageDTO,
    PaginationDTO,
)
from repository import conversation_repo


def list_conversations(
    consumer_id: str,
    status: str | None = None,
    label: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    """Return {conversations: [ConversationDTO], pagination: PaginationDTO}."""
    result = conversation_repo.list_conversations(
        consumer_id=consumer_id,
        status=status,
        label=label,
        cursor=cursor,
        limit=limit,
    )

    conversations = [
        ConversationDTO(
            id=c["id"],
            title=c["title"],
            status=c["status"],
            labels=c["labels"],
            closed_at=c.get("closed_at"),
            created_at=c["created_at"],
            updated_at=c["updated_at"],
            message_count=conversation_repo.count_messages(c["id"]),
        )
        for c in result["conversations"]
    ]

    return {
        "conversations": conversations,
        "pagination": PaginationDTO(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            total=result["total"],
        ),
    }


def create_conversation(
    consumer_id: str,
    message: str,
    labels: list[str] | None = None,
) -> dict:
    """Create a new conversation with its first message.

    Returns {conversation: ConversationDTO, message: ConversationMessageDTO}.
    """
    now = dt.datetime.now(dt.timezone.utc)
    conv_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())
    title = message[:50]

    conv = conversation_repo.create_conversation(
        id=conv_id,
        title=title,
        consumer_id=consumer_id,
        status="open",
        labels=labels or [],
        created_at=now,
        updated_at=now,
    )

    msg = conversation_repo.add_message(
        id=msg_id,
        conversation_id=conv_id,
        role="user",
        content=message,
        created_at=now,
    )

    return {
        "conversation": ConversationDTO(
            id=conv["id"],
            title=conv["title"],
            status=conv["status"],
            labels=conv["labels"],
            closed_at=conv.get("closed_at"),
            created_at=conv["created_at"],
            updated_at=conv["updated_at"],
            message_count=conversation_repo.count_messages(conv["id"]),
        ),
        "message": ConversationMessageDTO(
            id=msg["id"],
            role=msg["role"],
            content=msg["content"],
            created_at=msg["created_at"],
        ),
    }


def get_conversation(
    conversation_id: str,
    cursor: str | None = None,
    limit: int = 50,
    order: str = "asc",
) -> ConversationDetailDTO | None:
    """Return full conversation with paginated messages, or None if not found."""
    conv = conversation_repo.get_conversation(conversation_id)
    if conv is None:
        return None

    msg_result = conversation_repo.list_messages(
        conversation_id=conversation_id,
        cursor=cursor,
        limit=limit,
        order=order,
    )

    return ConversationDetailDTO(
        id=conv["id"],
        title=conv["title"],
        status=conv["status"],
        labels=conv["labels"],
        closed_at=conv.get("closed_at"),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        message_count=conversation_repo.count_messages(conversation_id),
        messages=[
            ConversationMessageDTO(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                created_at=m["created_at"],
            )
            for m in msg_result["messages"]
        ],
        pagination=PaginationDTO(
            next_cursor=msg_result["next_cursor"],
            has_more=msg_result["has_more"],
            total=msg_result["total"],
        ),
    )


def add_message(
    conversation_id: str,
    role: str,
    content: str,
) -> ConversationMessageDTO:
    """Add a message to a conversation. Reopens closed conversations on user messages."""
    now = dt.datetime.now(dt.timezone.utc)
    msg_id = str(uuid.uuid4())

    # Reopen closed conversation if user sends a message
    conv = conversation_repo.get_conversation(conversation_id)
    if conv and conv["status"] == "closed" and role == "user":
        conversation_repo.update_conversation(
            conversation_id, status="open", updated_at=now
        )
    else:
        conversation_repo.update_conversation(
            conversation_id, updated_at=now
        )

    msg = conversation_repo.add_message(
        id=msg_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=now,
    )

    return ConversationMessageDTO(
        id=msg["id"],
        role=msg["role"],
        content=msg["content"],
        created_at=msg["created_at"],
    )


def update_labels(
    conversation_id: str,
    labels: list[str],
) -> ConversationDTO | None:
    """Update conversation labels. Returns None if conversation not found."""
    conv = conversation_repo.update_conversation(conversation_id, labels=labels)
    if conv is None:
        return None

    return ConversationDTO(
        id=conv["id"],
        title=conv["title"],
        status=conv["status"],
        labels=conv["labels"],
        closed_at=conv.get("closed_at"),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        message_count=conversation_repo.count_messages(conversation_id),
    )


def close_conversation(conversation_id: str) -> ConversationDTO | None:
    """Close a conversation. Returns None if conversation not found."""
    now = dt.datetime.now(dt.timezone.utc)
    conv = conversation_repo.update_conversation(
        conversation_id, status="closed", closed_at=now, updated_at=now
    )
    if conv is None:
        return None

    return ConversationDTO(
        id=conv["id"],
        title=conv["title"],
        status=conv["status"],
        labels=conv["labels"],
        closed_at=conv.get("closed_at"),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        message_count=conversation_repo.count_messages(conversation_id),
    )


def escalate_conversation(conversation_id: str) -> ConversationDTO | None:
    """Escalate a conversation. Returns None if conversation not found."""
    now = dt.datetime.now(dt.timezone.utc)
    conv = conversation_repo.update_conversation(
        conversation_id, status="escalated", updated_at=now
    )
    if conv is None:
        return None

    return ConversationDTO(
        id=conv["id"],
        title=conv["title"],
        status=conv["status"],
        labels=conv["labels"],
        closed_at=conv.get("closed_at"),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        message_count=conversation_repo.count_messages(conversation_id),
    )
