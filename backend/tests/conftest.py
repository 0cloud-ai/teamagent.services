"""
Shared test fixtures — in-memory DuckDB + FastAPI TestClient.
"""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Stub out claude_agent_sdk before any module tries to import it
if "claude_agent_sdk" not in sys.modules:
    _stub = ModuleType("claude_agent_sdk")
    _stub.list_sessions = MagicMock(return_value=[])  # type: ignore[attr-defined]
    _stub.get_session_messages = MagicMock(return_value=[])  # type: ignore[attr-defined]
    sys.modules["claude_agent_sdk"] = _stub

from repository.db import get_test_conn, reset_conn


@pytest.fixture(autouse=True)
def _fresh_db():
    """Give every test a clean in-memory DuckDB (schema + seed data intact)."""
    get_test_conn()
    yield
    reset_conn()


@pytest.fixture()
def client() -> TestClient:
    from main import app

    return TestClient(app, raise_server_exceptions=False)
