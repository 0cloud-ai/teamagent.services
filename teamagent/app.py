from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os

from teamagent.config.loader import load_config
from teamagent.api.user_api import router as user_router
from teamagent.api.workspace_providers_api import router as providers_router
from teamagent.api.workspace_harness_api import router as harness_router
from teamagent.api.workspace_members_api import router as members_router
from teamagent.api.workspace_sessions_api import router as sessions_router
from teamagent.api.workspace_files_api import router as files_router
from teamagent.api.workspace_terminal_api import router as terminal_router
from teamagent.api.service_info_api import router as service_info_router
from teamagent.api.workspace_stats_api import router as stats_router
from teamagent.api.service_conversations_api import router as service_conv_router
from teamagent.api.workspace_conversations_api import router as workspace_conv_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    base_path = Path(os.environ.get("TEAMAGENT_BASE", ".")) / ".teamagent"
    app.state.base_path = base_path
    app.state.config = load_config(base_path / "teamagent.json")
    app.state.jwt_secret = os.environ.get("JWT_SECRET", "changeme")
    yield


app = FastAPI(title="teamagent.services", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(providers_router)
app.include_router(harness_router)
app.include_router(members_router)
app.include_router(sessions_router)
app.include_router(files_router)
app.include_router(terminal_router)
app.include_router(service_info_router)
app.include_router(stats_router)
app.include_router(service_conv_router)
app.include_router(workspace_conv_router)


@app.get("/health")
def health():
    return {"status": "ok"}
