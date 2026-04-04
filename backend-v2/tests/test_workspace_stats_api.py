def test_stats(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "src" / "main.py").write_text("x")
    (project / "README.md").write_text("y")
    r = client.get(f"/api/v1/workspace/stats?path={project}")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "directory"
    names = [c["name"] for c in data["children"]]
    assert "src" in names
    assert "README.md" in names


def test_stats_not_found(client):
    r = client.get("/api/v1/workspace/stats?path=/nonexistent")
    assert r.status_code == 404
