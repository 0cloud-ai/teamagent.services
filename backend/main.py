"""
Agent Service Backend

分层架构:
    api/        → HTTP 路由 (Controller)
    service/    → 业务逻辑
    repository/ → 数据访问
      db.py           → DuckDB 统一存储
      sdk_adapter.py      → Claude Agent SDK → DuckDB 同步
      claude_cli_adapter.py → Claude Code 本地文件 → DuckDB 同步
      stats_repo.py        → 统计查询
      session_repo.py      → 会话查询
    model/
      do.py     → Domain Objects (内部模型)
      dto.py    → Data Transfer Objects (API 响应)

数据流:
    Claude Agent SDK    ──┐
    Claude Code CLI 裸读 ──┼──→  DuckDB  ──→  API
    OpenCode (TODO)      ──┘

端点:
    GET /api/v1/stats/{path}     — 目录树统计
    GET /api/v1/sessions/{path}  — 会话列表 (游标分页)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.stats_api import router as stats_router
from api.session_api import router as session_router
from repository.db import get_conn
from repository.sdk_adapter import sync as sync_via_sdk
from repository.claude_cli_adapter import sync as sync_via_cli


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 初始化 DuckDB（建表）
    get_conn()
    # 2. 从各数据源同步会话到 DuckDB
    sync_via_sdk()
    sync_via_cli()
    yield


app = FastAPI(title="Agent Service API", version="0.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats_router)
app.include_router(session_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
