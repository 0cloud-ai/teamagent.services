import json
import os
import pytest
from pathlib import Path

from teamagent.config.loader import load_config


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "teamagent.json"
    p.write_text(json.dumps(data))
    return p


def test_load_minimal_config(tmp_path):
    path = _write_config(tmp_path, {})
    cfg = load_config(path)
    assert cfg.providers == {}
    assert cfg.members == []


def test_load_providers(tmp_path):
    path = _write_config(tmp_path, {
        "providers": {
            "claude": {
                "baseUrl": "https://api.anthropic.com",
                "apiKey": "sk-test",
                "apiFormat": "anthropic",
                "models": [{"id": "claude-sonnet-4", "name": "Claude Sonnet 4"}]
            }
        }
    })
    cfg = load_config(path)
    assert "claude" in cfg.providers
    assert cfg.providers["claude"].apiFormat == "anthropic"
    assert len(cfg.providers["claude"].models) == 1


def test_env_var_interpolation(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "sk-from-env")
    path = _write_config(tmp_path, {
        "providers": {
            "test": {
                "baseUrl": "https://example.com",
                "apiKey": "${TEST_API_KEY}",
                "apiFormat": "openai-completions",
                "models": []
            }
        }
    })
    cfg = load_config(path)
    assert cfg.providers["test"].apiKey == "sk-from-env"


def test_missing_env_var_raises(tmp_path):
    path = _write_config(tmp_path, {
        "providers": {
            "test": {
                "baseUrl": "${NONEXISTENT_VAR}",
                "apiFormat": "openai-completions",
                "models": []
            }
        }
    })
    with pytest.raises(ValueError, match="NONEXISTENT_VAR"):
        load_config(path)


def test_load_members(tmp_path):
    path = _write_config(tmp_path, {
        "members": [
            {"id": "mem-001", "type": "user", "name": "Alice", "email": "alice@test.com", "role": "owner"},
            {"id": "mem-002", "type": "service", "name": "Design Team", "serviceUrl": "https://design.test"}
        ]
    })
    cfg = load_config(path)
    assert len(cfg.members) == 2
    assert cfg.members[0].type == "user"
    assert cfg.members[1].serviceUrl == "https://design.test"
