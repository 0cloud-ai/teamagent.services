"""
Provider Service — LLM provider management, vendor defaults, health checks.
"""

from __future__ import annotations

import uuid
import datetime as dt

from model.dto import PingResultDTO, ProviderDTO
from repository import provider_repo

# ── Vendor default API base URLs ─────────────────────────────────────

_VENDOR_DEFAULTS: dict[str, str] = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com",
    "deepseek": "https://api.deepseek.com",
    "google": "https://generativelanguage.googleapis.com",
    "ollama": "http://localhost:11434",
}


def _to_dto(p: dict) -> ProviderDTO:
    return ProviderDTO(
        id=p["id"],
        vendor=p["vendor"],
        model=p["model"],
        api_base=p["api_base"],
        status=p["status"],
        used_by=p.get("used_by", []),
        created_at=p["created_at"],
    )


# ── Public API ───────────────────────────────────────────────────────


def list_providers() -> list[ProviderDTO]:
    rows = provider_repo.list_providers()
    return [_to_dto(r) for r in rows]


def create_provider(
    vendor: str,
    model: str,
    api_base: str | None = None,
    api_key: str | None = None,
) -> ProviderDTO:
    # Resolve api_base: explicit > vendor default > required for custom
    if api_base is None:
        if vendor in _VENDOR_DEFAULTS:
            api_base = _VENDOR_DEFAULTS[vendor]
        else:
            raise ValueError(
                f"api_base is required for vendor '{vendor}'"
            )

    provider_id = str(uuid.uuid4())
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    row = provider_repo.create_provider(
        id=provider_id,
        vendor=vendor,
        model=model,
        api_base=api_base,
        api_key=api_key,
        status="unknown",
        created_at=now,
    )
    return _to_dto(row)


def update_provider(provider_id: str, **fields) -> ProviderDTO | None:
    row = provider_repo.update_provider(provider_id, **fields)
    if row is None:
        return None
    return _to_dto(row)


def delete_provider(provider_id: str) -> bool:
    # Check if any harness binding references this provider
    bindings = provider_repo.get_bindings_for_provider(provider_id)
    if bindings:
        return False

    return provider_repo.delete_provider(provider_id)


def ping_provider(provider_id: str) -> PingResultDTO:
    provider = provider_repo.get_provider(provider_id)
    if provider is None:
        return PingResultDTO(
            status="unhealthy",
            latency_ms=None,
            model=None,
            message=None,
            error="Provider not found",
        )

    # Mock healthy result — real implementation would call the provider API
    return PingResultDTO(
        status="healthy",
        latency_ms=42,
        model=provider["model"],
        message="Mock ping successful",
        error=None,
    )
