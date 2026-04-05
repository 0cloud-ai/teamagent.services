from fastapi import APIRouter, HTTPException, Request
from pathlib import Path

router = APIRouter(prefix="/api/v1/workspace/stats", tags=["workspace-stats"])


def _scan_tree(path: Path, max_depth: int = 3, current_depth: int = 0) -> dict:
    if not path.is_dir():
        try:
            return {"name": path.name, "type": "file", "size": path.stat().st_size}
        except OSError:
            return {"name": path.name, "type": "file", "size": 0}
    children = []
    if current_depth < max_depth:
        for entry in sorted(path.iterdir()):
            if entry.name.startswith("."):
                continue
            children.append(_scan_tree(entry, max_depth, current_depth + 1))
    return {"name": path.name, "type": "directory", "children": children}


@router.get("")
def get_stats(request: Request, path: str = "/"):
    root = request.app.state.base_path.parent.resolve()
    rel = path.lstrip("/")
    target = (root / rel).resolve()
    if not str(target).startswith(str(root)):
        raise HTTPException(status_code=400, detail="Path traversal not allowed")
    if not target.is_dir():
        raise HTTPException(status_code=404, detail="Path not found")
    return _scan_tree(target)
