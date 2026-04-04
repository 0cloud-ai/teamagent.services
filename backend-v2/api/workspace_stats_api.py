from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/api/v1/workspace/stats", tags=["workspace-stats"])


def _scan_tree(path: Path, max_depth: int = 3, current_depth: int = 0) -> dict:
    if not path.is_dir():
        return {"name": path.name, "type": "file", "size": path.stat().st_size}
    children = []
    if current_depth < max_depth:
        for entry in sorted(path.iterdir()):
            if entry.name.startswith("."):
                continue
            children.append(_scan_tree(entry, max_depth, current_depth + 1))
    return {"name": path.name, "type": "directory", "children": children}


@router.get("")
def get_stats(path: str):
    p = Path(path)
    if not p.is_dir():
        raise HTTPException(status_code=404, detail="Path not found")
    return _scan_tree(p)
