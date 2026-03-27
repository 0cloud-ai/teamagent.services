"""
Workspace Sessions API — /api/v1/workspace/sessions
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from model.dto import (
    MessageDTO,
    SessionListResponseDTO,
    SessionMessagesResponseDTO,
    SessionDTO,
    SessionMemberDTO,
)
from service import session_service

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace-sessions"])


# ── Request bodies ───────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    path: str
    title: str | None = None
    harness: str | None = None
    members: list[str] | None = None


class SendMessageRequest(BaseModel):
    content: str
    mentions: list[str] | None = None


class AddSessionMemberRequest(BaseModel):
    member_id: str


# ── Routes ───────────────────────────────────────────────────────────

# NOTE: Specific routes MUST be defined before the catch-all {path:path}
# route, otherwise FastAPI's path matching will greedily capture
# e.g. "{session_id}/messages" as a path segment.

@router.post("/sessions", response_model=SessionDTO, status_code=201)
def create_session(body: CreateSessionRequest) -> SessionDTO:
    result = session_service.create_session(
        path=body.path,
        title=body.title,
        harness=body.harness,
        members=body.members,
    )
    return result


@router.get(
    "/sessions/{session_id}/messages",
    response_model=SessionMessagesResponseDTO,
)
def get_session_messages(
    session_id: str,
    cursor: Annotated[str | None, Query(description="Cursor for pagination")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 50,
    order: Annotated[str, Query(description="Sort order", pattern="^(asc|desc)$")] = "asc",
) -> SessionMessagesResponseDTO:
    result = session_service.get_session_messages(
        session_id, cursor=cursor, limit=limit, order=order,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return result


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageDTO,
    status_code=201,
)
def send_message(session_id: str, body: SendMessageRequest) -> MessageDTO:
    result = session_service.send_message(
        session_id, content=body.content, mentions=body.mentions,
    )
    return result


@router.get(
    "/sessions/{session_id}/members",
    response_model=list[SessionMemberDTO],
)
def list_session_members(session_id: str) -> list[SessionMemberDTO]:
    return session_service.list_session_members(session_id)


@router.post(
    "/sessions/{session_id}/members",
    response_model=SessionMemberDTO,
    status_code=201,
)
def add_session_member(session_id: str, body: AddSessionMemberRequest) -> SessionMemberDTO:
    result = session_service.add_session_member(session_id, member_id=body.member_id)
    if result is None:
        raise HTTPException(status_code=409, detail="Member already in session")
    return result


@router.delete("/sessions/{session_id}/members/{member_id}", status_code=204)
def remove_session_member(session_id: str, member_id: str) -> None:
    session_service.remove_session_member(session_id, member_id=member_id)


@router.get("/sessions/{path:path}", response_model=SessionListResponseDTO)
def list_sessions(
    path: str,
    cursor: Annotated[str | None, Query(description="Cursor for pagination")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    sort: Annotated[
        str,
        Query(description="Sort field", pattern="^(updated_at|created_at)$"),
    ] = "updated_at",
) -> SessionListResponseDTO:
    result = session_service.list_sessions(path, cursor=cursor, limit=limit, sort=sort)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Path '{path}' not found")
    return result
