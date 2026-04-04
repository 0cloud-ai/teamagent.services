from fastapi import APIRouter, Depends, HTTPException, Request

from model.conversation import UpdateLabelsRequest, EscalateRequest
from repository.conversation_repo import ConversationRepo
from repository.user_repo import UserRepo
from service.conversation_service import ConversationService

router = APIRouter(prefix="/api/v1/workspace/conversations", tags=["workspace-conversations"])


def _get_conv_service(request: Request) -> ConversationService:
    return ConversationService(
        ConversationRepo(request.app.state.base_path),
        UserRepo(request.app.state.base_path),
    )


@router.get("")
def list_conversations(
    status: str | None = None, label: str | None = None, limit: int = 20, cursor: str | None = None,
    svc: ConversationService = Depends(_get_conv_service),
):
    return svc.list_workspace_conversations(status=status, label=label, limit=limit, cursor=cursor)


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str, limit: int = 50, cursor: str | None = None,
    svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.get_workspace_detail(conversation_id, limit=limit, cursor=cursor)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/escalate")
def escalate(
    conversation_id: str, req: EscalateRequest | None = None,
    svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.escalate(conversation_id, reason=req.reason if req else None)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/close")
def close(conversation_id: str, svc: ConversationService = Depends(_get_conv_service)):
    try:
        return svc.close(conversation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/reopen")
def reopen(conversation_id: str, svc: ConversationService = Depends(_get_conv_service)):
    try:
        return svc.reopen(conversation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.put("/{conversation_id}/labels")
def update_labels(
    conversation_id: str, req: UpdateLabelsRequest,
    svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.update_labels(conversation_id, req.labels)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
