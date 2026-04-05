import json
import os
import re
from pathlib import Path

from teamagent.config.models import AppConfig


def _interpolate_env(text: str) -> str:
    def replacer(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(f"Environment variable '{var_name}' is not set")
        return value
    return re.sub(r"\$\{(\w+)\}", replacer, text)


_DEFAULT_CONFIG = {
    "providers": {},
    "members": [],
}


def ensure_config(base_path: Path) -> None:
    base_path.mkdir(parents=True, exist_ok=True)
    (base_path / "users").mkdir(exist_ok=True)
    (base_path / "conversations").mkdir(exist_ok=True)
    config_file = base_path / "teamagent.json"
    if not config_file.exists():
        config_file.write_text(json.dumps(_DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")


def load_config(path: Path) -> AppConfig:
    raw = path.read_text(encoding="utf-8")
    interpolated = _interpolate_env(raw)
    data = json.loads(interpolated)
    return AppConfig(**data)
