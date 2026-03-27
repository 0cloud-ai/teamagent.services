"""
Workspace Members API — /api/v1/workspace/members
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from model.dto import MemberDTO, PingResultDTO
from service import member_service

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace-members"])


# ── Request bodies ───────────────────────────────────────────────────

class AddMemberRequest(BaseModel):
    type: str
    name: str
    email: str | None = None
    role: str | None = None
    service_url: str | None = None


class UpdateMemberRequest(BaseModel):
    name: str | None = None
    role: str | None = None


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/members", response_model=list[MemberDTO])
def list_members(
    type: Annotated[str | None, Query(description="Filter by member type")] = None,
) -> list[MemberDTO]:
    return member_service.list_members(type_filter=type)


@router.post("/members", response_model=MemberDTO, status_code=201)
def add_member(body: AddMemberRequest) -> MemberDTO:
    result = member_service.add_member(
        type=body.type,
        name=body.name,
        email=body.email,
        role=body.role,
        service_url=body.service_url,
    )
    return result


@router.put("/members/{member_id}", response_model=MemberDTO)
def update_member(member_id: str, body: UpdateMemberRequest) -> MemberDTO:
    result = member_service.update_member(
        member_id, name=body.name, role=body.role,
    )
    return result


@router.delete("/members/{member_id}", status_code=204)
def remove_member(member_id: str) -> None:
    result = member_service.remove_member(member_id)
    if result is None:
        raise HTTPException(status_code=409, detail="Member cannot be removed")


@router.post("/members/{member_id}/ping", response_model=PingResultDTO)
def ping_member(member_id: str) -> PingResultDTO:
    return PingResultDTO(
        status="ok",
        latency_ms=42,
        message=f"Pong from member {member_id}",
    )
