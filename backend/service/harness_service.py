"""
Harness Service — engine configuration, provider bindings, default engine.
"""

from __future__ import annotations

from model.dto import BindingDTO, EngineDTO, HarnessResponseDTO
from repository import harness_repo, provider_repo


def _binding_to_dto(b: dict) -> BindingDTO:
    return BindingDTO(
        provider_id=b["provider_id"],
        vendor=b.get("vendor", ""),
        model=b.get("model", ""),
        role=b["role"],
    )


def _engine_to_dto(e: dict) -> EngineDTO:
    return EngineDTO(
        id=e["id"],
        name=e["name"],
        description=e["description"],
        supported_vendors=e["supported_vendors"],
        bindings=[_binding_to_dto(b) for b in e.get("bindings", [])],
    )


# ── Public API ───────────────────────────────────────────────────────


def get_harness() -> HarnessResponseDTO:
    engines = harness_repo.list_engines()
    default = harness_repo.get_default_engine()
    return HarnessResponseDTO(
        default=default,
        engines=[_engine_to_dto(e) for e in engines],
    )


def set_default(engine_id: str) -> HarnessResponseDTO:
    engine = harness_repo.get_engine(engine_id)
    if engine is None:
        raise ValueError(f"Engine '{engine_id}' not found")

    harness_repo.set_default_engine(engine_id)
    return get_harness()


def get_engine(engine_id: str) -> EngineDTO | None:
    engine = harness_repo.get_engine(engine_id)
    if engine is None:
        return None
    return _engine_to_dto(engine)


def add_binding(
    engine_id: str,
    provider_id: str,
    role: str = "default",
) -> BindingDTO:
    # Validate engine exists
    engine = harness_repo.get_engine(engine_id)
    if engine is None:
        raise ValueError(f"Engine '{engine_id}' not found")

    # Validate provider exists
    prov = provider_repo.get_provider(provider_id)
    if prov is None:
        raise ValueError(f"Provider '{provider_id}' not found")

    # Validate engine supports the provider's vendor
    if prov["vendor"] not in engine["supported_vendors"]:
        raise ValueError(
            f"Engine '{engine_id}' does not support vendor '{prov['vendor']}'. "
            f"Supported: {engine['supported_vendors']}"
        )

    row = harness_repo.add_binding(engine_id, provider_id, role)
    return BindingDTO(
        provider_id=row["provider_id"],
        vendor=prov["vendor"],
        model=prov["model"],
        role=row["role"],
    )


def update_binding(
    engine_id: str,
    provider_id: str,
    role: str,
) -> BindingDTO | None:
    row = harness_repo.update_binding(engine_id, provider_id, role)
    if row is None:
        return None

    prov = provider_repo.get_provider(provider_id)
    return BindingDTO(
        provider_id=row["provider_id"],
        vendor=prov["vendor"] if prov else "",
        model=prov["model"] if prov else "",
        role=row["role"],
    )


def delete_binding(engine_id: str, provider_id: str) -> bool:
    return harness_repo.delete_binding(engine_id, provider_id)
