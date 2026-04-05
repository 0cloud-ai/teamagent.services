from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from teamagent.config.models import AppConfig
from teamagent.harness.registry import get_engine, list_engines
from teamagent.harness.runner import HarnessRunner
from teamagent.harness.types import ProviderInfo

logger = logging.getLogger(__name__)


class HarnessService:
    def get_compatible_providers(self, harness_id: str, config: AppConfig) -> list[str]:
        engine = get_engine(harness_id)
        if engine is None:
            return []
        compatible = []
        for name, provider in config.providers.items():
            if provider.apiFormat in engine.api_formats:
                compatible.append(name)
        return compatible

    def run_harness(
        self,
        harness_id: str,
        path: str,
        session_id: str,
        message: str,
        config: AppConfig,
        messages_path: Path,
    ) -> None:
        """触发 harness 引擎执行（后台 async task）。"""
        engine = get_engine(harness_id)
        if engine is None:
            logger.warning("Harness engine '%s' not found in registry", harness_id)
            return

        provider_info = self._resolve_provider(engine, config)
        if provider_info is None:
            logger.warning("No compatible provider found for harness '%s'", harness_id)
            return

        watcher = engine.submit(path, message, provider_info)
        runner = HarnessRunner(messages_path)
        asyncio.get_event_loop().create_task(runner.run(engine, watcher))
        logger.info(
            "Harness started: engine=%s, session=%s, watcher_session=%s",
            harness_id, session_id, watcher.session_id,
        )

    @staticmethod
    def _resolve_provider(engine, config: AppConfig) -> ProviderInfo | None:
        """从 config.providers 中找第一个与 engine.api_formats 兼容的 provider。"""
        for name, provider in config.providers.items():
            if provider.apiFormat in engine.api_formats:
                if not provider.models:
                    continue
                return ProviderInfo(
                    name=name,
                    base_url=provider.baseUrl,
                    api_key=provider.apiKey,
                    api_format=provider.apiFormat,
                    model_id=provider.models[0].id,
                )
        return None
