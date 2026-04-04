import json
import os
import re
from pathlib import Path

from config.models import AppConfig


def _interpolate_env(text: str) -> str:
    def replacer(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise ValueError(f"Environment variable '{var_name}' is not set")
        return value
    return re.sub(r"\$\{(\w+)\}", replacer, text)


def load_config(path: Path) -> AppConfig:
    raw = path.read_text(encoding="utf-8")
    interpolated = _interpolate_env(raw)
    data = json.loads(interpolated)
    return AppConfig(**data)
