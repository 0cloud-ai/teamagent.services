from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import get_current_user
from model.conversation import CreateConversationRequest, SendConversationMessageRequest, UpdateLabelsRequest
from repository.conversation_repo import ConversationRepo
from repository.user_repo import UserRepo
from service.conversation_service import ConversationService

router = APIRouter(prefix="/api/v1/service/conversations", tags=["service-conversations"])


def _get_conv_service(request: Request) -> ConversationService:
    return ConversationService(
        ConversationRepo(request.app.state.base_path),
        UserRepo(request.app.state.base_path),
    )


@router.get("")
def list_conversations(
    status: str | None = None, label: str | None = None, limit: int = 20, cursor: str | None = None,
    user: dict = Depends(get_current_user), svc: ConversationService = Depends(_get_conv_service),
):
    return svc.list_conversations(status=status, label=label, limit=limit, cursor=cursor, user_id=user["id"])


@router.post("")
def create_conversation(
    req: CreateConversationRequest, user: dict = Depends(get_current_user), svc: ConversationService = Depends(_get_conv_service),
):
    return svc.create_conversation(user["id"], req.message, req.labels)


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str, limit: int = 50, cursor: str | None = None, order: str = "asc",
    user: dict = Depends(get_current_user), svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.get_detail(conversation_id, limit=limit, cursor=cursor, order=order)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: str, req: SendConversationMessageRequest,
    user: dict = Depends(get_current_user), svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.send_message(conversation_id, req.content)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.put("/{conversation_id}/labels")
def update_labels(
    conversation_id: str, req: UpdateLabelsRequest,
    user: dict = Depends(get_current_user), svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.update_labels(conversation_id, req.labels)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/{conversation_id}/close")
def close_conversation(
    conversation_id: str, user: dict = Depends(get_current_user), svc: ConversationService = Depends(_get_conv_service),
):
    try:
        return svc.close(conversation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
