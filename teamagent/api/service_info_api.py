from fastapi import APIRouter, Depends

from teamagent.api.deps import get_config
from teamagent.config.models import AppConfig

router = APIRouter(prefix="/api/v1/service", tags=["service-info"])


@router.get("/info")
def get_info(config: AppConfig = Depends(get_config)):
    return {
        "name": "teamagent.services",
        "version": "2.0.0",
        "status": "active",
        "providers": len(config.providers),
        "harnesses": len(config.harnesses.engines),
        "members": len(config.members),
    }
