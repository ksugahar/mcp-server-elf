"""Public-safe contract for a normalized ELF/MAGIC project feature inventory."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime


SCHEMA = "elf.project-feature-inventory.v1"

FEATURE_ROUTES: dict[str, tuple[str, ...]] = {
    "static_permanent_magnet_and_demagnetization": ("magic",),
    "nonlinear_magnetic_materials": ("magic",),
    "stationary_eddy_current_and_shielding": ("magic",),
    "moving_conductor_and_rotation": ("magic",),
    "force_torque_motor_and_maglev": ("magic",),
    "harmonic_balance": ("magic",),
    "vector_hysteresis": ("magic",),
    "model_order_reduction_and_cln": ("postprocess",),
    "bem_acceleration_and_mesh_research": ("magic",),
    "benchmark_and_validation_projects": ("validation",),
    "charged_particle_tracking": ("beam",),
    "electrostatic_and_dielectric_fields": ("elfin",),
}

ARTIFACT_KINDS = (
    ".csv",
    ".mac",
    ".mag",
    ".mai",
    ".mao",
    ".mat",
    ".meg",
    ".mei",
    ".meo",
)

_TOP_LEVEL_KEYS = {
    "schema",
    "created_at_utc",
    "generation",
    "feature_generation",
    "route_generation",
    "artifact_generation",
    "owner_generation",
    "result_generation",
    "feature_families",
    "feature_routes",
    "artifact_kinds",
    "project_family_count",
    "inventory_owner",
    "inventory_sha256",
    "accepted_inventory_sha256",
    "result_sha256",
    "accepted_result_sha256",
}


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _string_sequence(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    if not all(isinstance(item, str) and item for item in value):
        return None
    return tuple(value)


def inventory_digest(
    feature_families: Sequence[str],
    feature_routes: Mapping[str, Sequence[str]],
    artifact_kinds: Sequence[str],
    project_family_count: int,
) -> str:
    """Return the canonical digest bound by the inventory contract."""

    payload = {
        "artifact_kinds": list(artifact_kinds),
        "feature_families": list(feature_families),
        "feature_routes": {
            name: list(feature_routes[name]) for name in sorted(feature_routes)
        },
        "project_family_count": project_family_count,
    }
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def project_feature_inventory_contract_gate(summary_json: str) -> dict[str, object]:
    """Validate normalized feature coverage without opening user-local paths."""

    try:
        payload = json.loads(summary_json)
    except (TypeError, ValueError):
        payload = None
    if not isinstance(payload, Mapping):
        return {
            "policy": SCHEMA,
            "status": "needs_attention",
            "checks": {"summary_is_json_object": False},
            "issues": ["summary_is_json_object"],
        }

    feature_families = _string_sequence(payload.get("feature_families"))
    artifact_kinds = _string_sequence(payload.get("artifact_kinds"))
    routes = payload.get("feature_routes")
    routes = routes if isinstance(routes, Mapping) else {}
    normalized_routes = {
        name: _string_sequence(value) for name, value in routes.items()
    }
    count = payload.get("project_family_count")
    generation = str(payload.get("generation") or "")

    exact_features = tuple(sorted(FEATURE_ROUTES))
    exact_routes = (
        set(normalized_routes) == set(FEATURE_ROUTES)
        and all(normalized_routes[name] == FEATURE_ROUTES[name] for name in FEATURE_ROUTES)
    )
    digest_ready = (
        feature_families is not None
        and artifact_kinds is not None
        and exact_routes
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count > 0
    )
    expected_digest = (
        inventory_digest(feature_families, normalized_routes, artifact_kinds, count)
        if digest_ready
        else ""
    )
    checks = {
        "summary_is_json_object": True,
        "top_level_schema_is_exact": set(payload) == _TOP_LEVEL_KEYS,
        "schema_matches": payload.get("schema") == SCHEMA,
        "created_at_is_iso8601": _timestamp(payload.get("created_at_utc")),
        "generation_is_bound": bool(generation)
        and all(
            payload.get(key) == generation
            for key in (
                "feature_generation",
                "route_generation",
                "artifact_generation",
                "owner_generation",
                "result_generation",
            )
        ),
        "feature_families_are_exact_sorted_unique": feature_families == exact_features,
        "feature_routes_are_exact": exact_routes,
        "artifact_kinds_are_exact_sorted_unique": artifact_kinds == ARTIFACT_KINDS,
        "project_family_count_is_positive": isinstance(count, int)
        and not isinstance(count, bool)
        and count > 0,
        "inventory_owner_is_explicit": str(payload.get("inventory_owner") or "").startswith("inventory:"),
        "inventory_digest_matches_content": _digest(payload.get("inventory_sha256"))
        and payload.get("inventory_sha256") == expected_digest,
        "accepted_inventory_digest_matches": payload.get("accepted_inventory_sha256")
        == payload.get("inventory_sha256"),
        "result_digest_is_bound": _digest(payload.get("result_sha256"))
        and payload.get("accepted_result_sha256") == payload.get("result_sha256"),
    }
    validated = all(checks.values())
    return {
        "policy": SCHEMA,
        "status": "validated" if validated else "needs_attention",
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "feature_count": len(feature_families or ()),
        "route_owners": sorted({owner for owners in normalized_routes.values() if owners for owner in owners}),
        "opens_local_paths": False,
        "exposes_solved_values": False,
    }


__all__ = [
    "ARTIFACT_KINDS",
    "FEATURE_ROUTES",
    "SCHEMA",
    "inventory_digest",
    "project_feature_inventory_contract_gate",
]
