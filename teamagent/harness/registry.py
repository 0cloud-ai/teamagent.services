from __future__ import annotations

import importlib
import pkgutil
import logging

from teamagent.harness.engine import HarnessEngine

logger = logging.getLogger(__name__)

_engines: dict[str, type[HarnessEngine]] = {}


def register_engine(cls: type[HarnessEngine]) -> None:
    _engines[cls.id] = cls


def get_engine(engine_id: str) -> HarnessEngine | None:
    cls = _engines.get(engine_id)
    if cls is None:
        return None
    return cls()


def list_engines() -> dict[str, type[HarnessEngine]]:
    return dict(_engines)


def discover_plugins() -> None:
    """扫描 teamagent.plugins.harness 包，注册所有 HarnessEngine 子类。"""
    try:
        import teamagent.plugins.harness as pkg
    except ImportError:
        logger.warning("teamagent.plugins.harness package not found, skipping plugin discovery")
        return

    for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            logger.exception("Failed to import plugin module %s", modname)
            continue
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, HarnessEngine)
                and attr is not HarnessEngine
                and hasattr(attr, "id")
            ):
                register_engine(attr)
                logger.info("Registered harness engine: %s (%s)", attr.id, attr.name)
