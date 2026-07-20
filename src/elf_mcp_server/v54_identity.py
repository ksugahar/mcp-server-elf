"""Public-safe near-singular quadrature and nonlinear-restart replay checks."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


NEAR = "bem_nearsingular_quadrature_distance_panelorder_orientation_owner_identity"
RESTART = "nonlinear_restart_curvebranch_iteration_residual_checkpoint_owner_identity"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _near_ok(row: Mapping[str, object]) -> bool:
    interactions = row.get("near_interactions")
    interactions_ok = isinstance(interactions, Sequence) and not isinstance(interactions, (str, bytes)) and bool(interactions)
    seen: set[tuple[int, int]] = set()
    if interactions_ok:
        for item in interactions:
            expected = {"source_panel", "target_panel", "distance_over_size", "distance_class", "quadrature_order", "source_panel_order", "target_panel_order", "orientation"}
            if not isinstance(item, Mapping) or set(item) != expected:
                interactions_ok = False
                break
            source = item["source_panel"]; target = item["target_panel"]; distance = item["distance_over_size"]
            source_order = item["source_panel_order"]; target_order = item["target_panel_order"]; quadrature = item["quadrature_order"]
            if not (
                isinstance(source, int) and not isinstance(source, bool) and source > 0
                and isinstance(target, int) and not isinstance(target, bool) and target > 0 and source != target and (source, target) not in seen
                and _finite(distance) and 0.0 < float(distance) <= 0.25 and item["distance_class"] == "near_singular"
                and isinstance(source_order, int) and not isinstance(source_order, bool) and source_order >= 1
                and isinstance(target_order, int) and not isinstance(target_order, bool) and target_order >= 1
                and isinstance(quadrature, int) and not isinstance(quadrature, bool) and quadrature >= 2 * max(source_order, target_order) + 2
                and isinstance(item["orientation"], int) and not isinstance(item["orientation"], bool) and item["orientation"] == 1
            ):
                interactions_ok = False
                break
            seen.add((source, target))
    return (
        _generations(row, "distance_generation", "quadrature_generation", "panelorder_generation", "orientation_generation", "owner_generation", "result_generation")
        and interactions_ok
        and row.get("replayed_near_interactions") == interactions
        and str(row.get("mesh_owner") or "").startswith("mesh:")
        and row.get("replayed_mesh_owner") == row.get("mesh_owner")
        and _result(row)
    )


def _restart_ok(row: Mapping[str, object]) -> bool:
    iteration = row.get("iteration_counter")
    residuals = row.get("residual_history")
    residuals_ok = (
        isinstance(iteration, int) and not isinstance(iteration, bool) and iteration >= 1
        and isinstance(residuals, Sequence) and not isinstance(residuals, (str, bytes)) and len(residuals) == iteration + 1
        and all(_finite(value) and float(value) >= 0.0 for value in residuals)
        and all(float(right) <= float(left) for left, right in zip(residuals, residuals[1:]))
    )
    checkpoint = row.get("restart_checkpoint")
    checkpoint_ok = (
        isinstance(checkpoint, Mapping) and set(checkpoint) == {"iteration", "state_sha256"}
        and checkpoint["iteration"] == iteration and _digest(checkpoint["state_sha256"])
    )
    return (
        _generations(row, "branch_generation", "iteration_generation", "residual_generation", "checkpoint_generation", "owner_generation", "result_generation")
        and str(row.get("curve_branch") or "").startswith("branch:")
        and row.get("replayed_curve_branch") == row.get("curve_branch")
        and residuals_ok
        and row.get("replayed_iteration_counter") == iteration
        and row.get("replayed_residual_history") == residuals
        and checkpoint_ok
        and row.get("replayed_restart_checkpoint") == checkpoint
        and str(row.get("run_owner") or "").startswith("run:")
        and row.get("replayed_run_owner") == row.get("run_owner")
        and _result(row)
    )


def validate_source_v54_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    near_rows = [row[NEAR] for row in rows if NEAR in row]
    restarts = [row[RESTART] for row in rows if RESTART in row]
    checks: dict[str, bool] = {}
    if near_rows:
        checks["source_v54_nearsingular_distance_quadrature_order_orientation_owner"] = len(near_rows) == len(rows) and all(isinstance(row, Mapping) and _near_ok(row) for row in near_rows)
    if restarts:
        checks["source_v54_nonlinear_restart_branch_iteration_residual_owner"] = len(restarts) == len(rows) and all(isinstance(row, Mapping) and _restart_ok(row) for row in restarts)
    return checks
