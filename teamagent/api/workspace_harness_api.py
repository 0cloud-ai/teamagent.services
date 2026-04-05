from fastapi import APIRouter, HTTPException

from teamagent.harness.registry import list_engines, get_engine

router = APIRouter(prefix="/api/v1/workspace/harness", tags=["workspace-harness"])


@router.get("")
def list_harness():
    engines = {}
    for engine_id, cls in list_engines().items():
        engines[engine_id] = {
            "id": cls.id,
            "name": cls.name,
            "api_formats": cls.api_formats,
        }
    return {"engines": engines}


@router.get("/{harness_id}")
def get_harness(harness_id: str):
    engine = get_engine(harness_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Engine not found")
    return {
        "id": engine.id,
        "name": engine.name,
        "api_formats": engine.api_formats,
    }
