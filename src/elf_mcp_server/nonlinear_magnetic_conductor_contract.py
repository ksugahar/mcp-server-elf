"""Public-safe validation gate for nonlinear magnetic conductors."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import datetime


SCHEMA = "elf.nonlinear-magnetic-conductor-validation.v1"

_TOP_LEVEL_KEYS = {
    "schema",
    "created_at_utc",
    "generation",
    "material_scope",
    "transient_step_count",
    "model_identity_sha256",
    "accepted_model_identity_sha256",
    "result_sha256",
    "accepted_result_sha256",
    "evidence_checks",
    "normalized_errors",
    "tolerances",
}

_EVIDENCE_KEYS = {
    "same_geometry_material_source_time_identity",
    "nonlinear_iterations_converged",
    "source_mean_b_mesh_converged",
    "source_joule_mesh_converged",
    "independent_mean_b_checked",
    "independent_joule_checked",
    "reduced_parent_joule_checked",
    "response_order_saturation_checked",
    "joule_nonnegative",
    "energy_balance_closed",
}

_METRIC_KEYS = {
    "source_mean_b_mesh_relative",
    "source_joule_mesh_relative",
    "independent_mean_b_relative",
    "independent_joule_relative",
    "reduced_parent_joule_relative",
    "response_order_saturation_relative",
    "energy_balance_mixed_norm",
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


def _finite_nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _finite_positive(value: object) -> bool:
    return _finite_nonnegative(value) and float(value) > 0.0


def nonlinear_magnetic_conductor_validation_gate(
    summary_json: str,
) -> dict[str, object]:
    """Validate observable-specific convergence without exposing solved values.

    Mean magnetic flux density and Joule loss are deliberately gated
    independently. Agreement in a field average does not establish convergence
    of a quadratic loss observable.
    """

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
            "observable_status": {
                "mean_b": "needs_attention",
                "joule_loss": "needs_attention",
            },
            "opens_local_paths": False,
            "exposes_solved_values": False,
        }

    evidence = payload.get("evidence_checks")
    metrics = payload.get("normalized_errors")
    tolerances = payload.get("tolerances")
    evidence_exact = (
        isinstance(evidence, Mapping)
        and set(evidence) == _EVIDENCE_KEYS
        and all(isinstance(evidence[name], bool) for name in _EVIDENCE_KEYS)
    )
    metrics_exact = (
        isinstance(metrics, Mapping)
        and set(metrics) == _METRIC_KEYS
        and all(_finite_nonnegative(metrics[name]) for name in _METRIC_KEYS)
    )
    tolerances_exact = (
        isinstance(tolerances, Mapping)
        and set(tolerances) == _METRIC_KEYS
        and all(_finite_positive(tolerances[name]) for name in _METRIC_KEYS)
    )

    model_digest = payload.get("model_identity_sha256")
    result_digest = payload.get("result_sha256")
    common_checks = {
        "summary_is_json_object": True,
        "top_level_schema_is_exact": set(payload) == _TOP_LEVEL_KEYS,
        "schema_matches": payload.get("schema") == SCHEMA,
        "created_at_is_iso8601": _timestamp(payload.get("created_at_utc")),
        "generation_is_bound": bool(str(payload.get("generation") or "")),
        "material_scope_is_same_region": payload.get("material_scope")
        == "same_region_nonlinear_magnetic_conductor",
        "transient_grid_is_nontrivial": isinstance(payload.get("transient_step_count"), int)
        and not isinstance(payload.get("transient_step_count"), bool)
        and int(payload["transient_step_count"]) >= 2,
        "model_identity_is_bound": _digest(model_digest)
        and payload.get("accepted_model_identity_sha256") == model_digest,
        "result_identity_is_bound": _digest(result_digest)
        and payload.get("accepted_result_sha256") == result_digest,
        "evidence_checks_are_exact_booleans": evidence_exact,
        "normalized_errors_are_exact_finite_nonnegative": metrics_exact,
        "tolerances_are_exact_finite_positive": tolerances_exact,
    }
    common_valid = all(common_checks.values())

    def evidence_true(name: str) -> bool:
        return evidence_exact and evidence[name] is True

    def metric_within(name: str) -> bool:
        return metrics_exact and tolerances_exact and float(metrics[name]) <= float(tolerances[name])

    mean_b_checks = {
        "same_identity": evidence_true("same_geometry_material_source_time_identity"),
        "nonlinear_iterations_converged": evidence_true("nonlinear_iterations_converged"),
        "source_mean_b_mesh_converged": evidence_true("source_mean_b_mesh_converged"),
        "independent_mean_b_checked": evidence_true("independent_mean_b_checked"),
        "source_mean_b_error_within_tolerance": metric_within("source_mean_b_mesh_relative"),
        "independent_mean_b_error_within_tolerance": metric_within("independent_mean_b_relative"),
    }
    joule_checks = {
        "same_identity": evidence_true("same_geometry_material_source_time_identity"),
        "nonlinear_iterations_converged": evidence_true("nonlinear_iterations_converged"),
        "source_joule_mesh_converged": evidence_true("source_joule_mesh_converged"),
        "independent_joule_checked": evidence_true("independent_joule_checked"),
        "reduced_parent_joule_checked": evidence_true("reduced_parent_joule_checked"),
        "response_order_saturation_checked": evidence_true("response_order_saturation_checked"),
        "joule_nonnegative": evidence_true("joule_nonnegative"),
        "energy_balance_closed": evidence_true("energy_balance_closed"),
        "source_joule_error_within_tolerance": metric_within("source_joule_mesh_relative"),
        "independent_joule_error_within_tolerance": metric_within("independent_joule_relative"),
        "reduced_parent_joule_error_within_tolerance": metric_within("reduced_parent_joule_relative"),
        "response_order_saturation_within_tolerance": metric_within("response_order_saturation_relative"),
        "energy_balance_within_tolerance": metric_within("energy_balance_mixed_norm"),
    }
    mean_b_valid = common_valid and all(mean_b_checks.values())
    joule_valid = common_valid and all(joule_checks.values())

    checks = {
        **common_checks,
        "mean_b_observable_is_validated": mean_b_valid,
        "joule_observable_is_validated": joule_valid,
    }
    return {
        "policy": SCHEMA,
        "status": "validated" if mean_b_valid and joule_valid else "needs_attention",
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "observable_status": {
            "mean_b": "validated" if mean_b_valid else "needs_attention",
            "joule_loss": "validated" if joule_valid else "needs_attention",
        },
        "notes": [
            "A converged mean-B observable does not prove convergence of Joule loss.",
            "Do not use a source-solver Joule value as a cross-validation gate until its own mesh ladder converges.",
            "When a reduced solve overpredicts Joule loss, isolate magnetic-response reduction from the current space with reduced-parent and response-order checks.",
        ],
        "opens_local_paths": False,
        "exposes_solved_values": False,
    }


__all__ = ["SCHEMA", "nonlinear_magnetic_conductor_validation_gate"]
