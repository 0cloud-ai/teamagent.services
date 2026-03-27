"""
Tests for workspace_stats_api — GET /api/v1/workspace/stats
"""

from repository.db import get_conn


def test_get_root_stats(client):
    """GET /api/v1/workspace/stats returns 200 with path='/'."""
    resp = client.get("/api/v1/workspace/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "/"
    assert "direct" in data
    assert "total" in data
    assert "children" in data


def test_get_nonexistent_path(client):
    """GET /api/v1/workspace/stats/nonexistent returns 404."""
    resp = client.get("/api/v1/workspace/stats/nonexistent")
    assert resp.status_code == 404
