"""
Workspace Service Inbox API — /api/v1/workspace/service-inbox
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from model.dto import InboxConversationDTO, InboxConversationDetailDTO
from service import service_inbox_service

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace-service-inbox"])


# ── Request bodies ───────────────────────────────────────────────────

class EscalateRequest(BaseModel):
    reason: str | None = None


class UpdateLabelsRequest(BaseModel):
    labels: list[str]


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/service-inbox")
def list_inbox(
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    label: Annotated[str | None, Query(description="Filter by label")] = None,
    cursor: Annotated[str | None, Query(description="Cursor for pagination")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
) -> dict:
    return service_inbox_service.list_inbox(
        status=status, label=label, cursor=cursor, limit=limit,
    )


@router.get(
    "/service-inbox/{conversation_id}",
    response_model=InboxConversationDetailDTO,
)
def get_inbox_detail(conversation_id: str) -> InboxConversationDetailDTO:
    result = service_inbox_service.get_inbox_detail(conversation_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conversation_id}' not found",
        )
    return result


@router.post(
    "/service-inbox/{conversation_id}/escalate",
    response_model=InboxConversationDetailDTO,
)
def escalate(conversation_id: str, body: EscalateRequest) -> InboxConversationDetailDTO:
    return service_inbox_service.escalate(conversation_id, reason=body.reason)


@router.post(
    "/service-inbox/{conversation_id}/close",
    response_model=InboxConversationDetailDTO,
)
def close(conversation_id: str) -> InboxConversationDetailDTO:
    return service_inbox_service.close(conversation_id)


@router.post(
    "/service-inbox/{conversation_id}/reopen",
    response_model=InboxConversationDetailDTO,
)
def reopen(conversation_id: str) -> InboxConversationDetailDTO:
    return service_inbox_service.reopen(conversation_id)


@router.put(
    "/service-inbox/{conversation_id}/labels",
    response_model=InboxConversationDetailDTO,
)
def update_labels(
    conversation_id: str, body: UpdateLabelsRequest,
) -> InboxConversationDetailDTO:
    return service_inbox_service.update_labels(conversation_id, labels=body.labels)
