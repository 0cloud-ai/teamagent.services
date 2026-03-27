"""
Workspace Harness API — /api/v1/workspace/harness
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from model.dto import HarnessResponseDTO, EngineDTO, BindingDTO
from service import harness_service

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace-harness"])


# ── Request bodies ───────────────────────────────────────────────────

class SetDefaultRequest(BaseModel):
    engine_id: str


class AddBindingRequest(BaseModel):
    provider_id: str
    role: str = "default"


class UpdateBindingRequest(BaseModel):
    role: str


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/harness", response_model=HarnessResponseDTO)
def get_harness() -> HarnessResponseDTO:
    return harness_service.get_harness()


@router.put("/harness/default", response_model=HarnessResponseDTO)
def set_default(body: SetDefaultRequest) -> HarnessResponseDTO:
    return harness_service.set_default(engine_id=body.engine_id)


@router.get("/harness/engines/{engine_id}", response_model=EngineDTO)
def get_engine(engine_id: str) -> EngineDTO:
    result = harness_service.get_engine(engine_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Engine '{engine_id}' not found")
    return result


@router.post(
    "/harness/engines/{engine_id}/bindings",
    response_model=BindingDTO,
    status_code=201,
)
def add_binding(engine_id: str, body: AddBindingRequest) -> BindingDTO:
    return harness_service.add_binding(
        engine_id, provider_id=body.provider_id, role=body.role,
    )


@router.put(
    "/harness/engines/{engine_id}/bindings/{provider_id}",
    response_model=BindingDTO,
)
def update_binding(
    engine_id: str, provider_id: str, body: UpdateBindingRequest,
) -> BindingDTO:
    return harness_service.update_binding(
        engine_id, provider_id=provider_id, role=body.role,
    )


@router.delete(
    "/harness/engines/{engine_id}/bindings/{provider_id}",
    status_code=204,
)
def delete_binding(engine_id: str, provider_id: str) -> None:
    harness_service.delete_binding(engine_id, provider_id=provider_id)
