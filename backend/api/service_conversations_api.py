"""
Service Conversations API — /api/v1/service/conversations
消费者侧会话管理：创建、列表、发送消息、标签、关闭。
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from model.dto import ConversationDTO, ConversationDetailDTO, ConversationMessageDTO
from service import conversation_service, user_service

router = APIRouter(prefix="/api/v1/service", tags=["service-conversations"])


# ── Request Bodies ──────────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    message: str
    labels: list[str] | None = None


class AddMessageRequest(BaseModel):
    content: str


class UpdateLabelsRequest(BaseModel):
    labels: list[str]


# ── Auth Helper ─────────────────────────────────────────────────────

def _get_current_user_id(request: Request) -> str:
    """Extract user identity for the request.

    Checks in order:
    1. Bearer token in Authorization header (production path).
    2. X-User-Id header (testing convenience).

    Raises 401 if neither is present or the token is invalid.
    """
    # Try Bearer token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        user_id = user_service.verify_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_id

    # Fall back to X-User-Id header for testing
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return user_id

    raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")


# ── Routes ──────────────────────────────────────────────────────────

@router.get("/conversations")
def list_conversations(
    request: Request,
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    label: Annotated[str | None, Query(description="Filter by label")] = None,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> dict:
    user_id = _get_current_user_id(request)
    return conversation_service.list_conversations(
        consumer_id=user_id,
        status=status,
        label=label,
        cursor=cursor,
        limit=limit,
    )


@router.post("/conversations", response_model=dict)
def create_conversation(request: Request, body: CreateConversationRequest) -> dict:
    user_id = _get_current_user_id(request)
    return conversation_service.create_conversation(
        consumer_id=user_id,
        message=body.message,
        labels=body.labels,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailDTO)
def get_conversation(conversation_id: str) -> ConversationDetailDTO:
    result = conversation_service.get_conversation(conversation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessageDTO,
)
def add_message(
    request: Request,
    conversation_id: str,
    body: AddMessageRequest,
) -> ConversationMessageDTO:
    _get_current_user_id(request)  # ensure authenticated
    return conversation_service.add_message(
        conversation_id=conversation_id,
        role="user",
        content=body.content,
    )


@router.put("/conversations/{conversation_id}/labels", response_model=ConversationDTO)
def update_labels(
    request: Request,
    conversation_id: str,
    body: UpdateLabelsRequest,
) -> ConversationDTO:
    _get_current_user_id(request)  # ensure authenticated
    result = conversation_service.update_labels(
        conversation_id=conversation_id,
        labels=body.labels,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.post("/conversations/{conversation_id}/close", response_model=ConversationDTO)
def close_conversation(
    request: Request,
    conversation_id: str,
) -> ConversationDTO:
    _get_current_user_id(request)  # ensure authenticated
    result = conversation_service.close_conversation(conversation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result
