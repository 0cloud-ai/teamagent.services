"""
Service Info API — /api/v1/service
服务元信息的查询与更新。
"""

from fastapi import APIRouter
from pydantic import BaseModel

from model.dto import ServiceInfoDTO

router = APIRouter(prefix="/api/v1/service", tags=["service"])


# ── Request Bodies ──────────────────────────────────────────────────

class UpdateServiceInfoRequest(BaseModel):
    name: str
    description: str
    status: str
    capabilities: list[str] = []


# ── In-memory store (placeholder until DB table is wired) ──────────

_service_info = ServiceInfoDTO(
    name="Agent Service",
    description="Default agent service instance",
    status="running",
    capabilities=[],
)


# ── Routes ──────────────────────────────────────────────────────────

@router.get("/info", response_model=ServiceInfoDTO)
def get_service_info() -> ServiceInfoDTO:
    return _service_info


@router.put("/info", response_model=ServiceInfoDTO)
def update_service_info(body: UpdateServiceInfoRequest) -> ServiceInfoDTO:
    global _service_info
    _service_info = ServiceInfoDTO(
        name=body.name,
        description=body.description,
        status=body.status,
        capabilities=body.capabilities,
    )
    return _service_info
