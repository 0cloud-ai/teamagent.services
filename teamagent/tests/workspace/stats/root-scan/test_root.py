def test_root_scan(client):
    """path=/ should scan the workspace root (base_path.parent), not the system root."""
    # base_path is tmp_path/.teamagent, so workspace root is tmp_path
    # The conftest make_client already creates .teamagent/ with files inside tmp_path
    # Create some visible files in the workspace root (tmp_path)
    import pathlib

    root = client.app.state.base_path.parent
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("x")
    (root / "README.md").write_text("hello")

    r = client.get("/api/v1/workspace/stats?path=/")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "directory"
    names = [c["name"] for c in data["children"]]
    assert "src" in names
    assert "README.md" in names


def test_path_traversal_rejected(client):
    """path=/../etc/passwd should be rejected."""
    r = client.get("/api/v1/workspace/stats?path=/../etc/passwd")
    assert r.status_code == 400
