"""Public-safe linear-system and closed-surface replay checks for v52."""

from __future__ import annotations

import math
from collections.abc import Mapping


LINEAR_SYSTEM = "linear_system_preconditioner_ordering_tolerance_residual_matrix_owner_identity"
SURFACE = "surface_component_closedness_genus_orientation_mesh_owner_identity"


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


def _linear_system_ok(row: Mapping[str, object]) -> bool:
    tolerance = row.get("relative_tolerance")
    residuals = row.get("residual_history")
    residuals_ok = (
        isinstance(residuals, list)
        and len(residuals) >= 2
        and all(_finite(value) and float(value) >= 0.0 for value in residuals)
        and all(float(right) <= float(left) for left, right in zip(residuals, residuals[1:]))
    )
    return (
        _generations(row, "preconditioner_generation", "ordering_generation", "tolerance_generation", "residual_generation", "owner_generation", "result_generation")
        and row.get("preconditioner") in {"jacobi", "ilu0", "amg"}
        and row.get("replayed_preconditioner") == row.get("preconditioner")
        and row.get("matrix_ordering") in {"natural", "reverse_cuthill_mckee", "nested_dissection"}
        and row.get("replayed_matrix_ordering") == row.get("matrix_ordering")
        and _finite(tolerance)
        and 0.0 < float(tolerance) <= 1.0e-2
        and row.get("replayed_relative_tolerance") == tolerance
        and residuals_ok
        and float(residuals[-1]) <= float(tolerance)
        and row.get("replayed_residual_history") == residuals
        and str(row.get("matrix_owner") or "").startswith("matrix:")
        and row.get("replayed_matrix_owner") == row.get("matrix_owner")
        and _result(row)
    )


def _surface_ok(row: Mapping[str, object]) -> bool:
    count = row.get("component_count")
    closedness = row.get("component_closedness")
    genus = row.get("component_genus")
    orientation = row.get("component_orientation")
    components_ok = (
        isinstance(count, int)
        and not isinstance(count, bool)
        and count > 0
        and isinstance(closedness, list)
        and isinstance(genus, list)
        and isinstance(orientation, list)
        and len(closedness) == len(genus) == len(orientation) == count
        and all(value is True for value in closedness)
        and all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in genus)
        and all(value == "outward" for value in orientation)
    )
    return (
        _generations(row, "component_generation", "closedness_generation", "genus_generation", "orientation_generation", "owner_generation", "result_generation")
        and components_ok
        and row.get("replayed_component_count") == count
        and row.get("replayed_component_closedness") == closedness
        and row.get("replayed_component_genus") == genus
        and row.get("replayed_component_orientation") == orientation
        and str(row.get("mesh_owner") or "").startswith("mesh:")
        and row.get("replayed_mesh_owner") == row.get("mesh_owner")
        and _result(row)
    )


def validate_source_v52_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    linear_systems = [row[LINEAR_SYSTEM] for row in rows if LINEAR_SYSTEM in row]
    surfaces = [row[SURFACE] for row in rows if SURFACE in row]
    checks: dict[str, bool] = {}
    if linear_systems:
        checks["source_v52_linear_system_preconditioner_ordering_residual_owner"] = len(linear_systems) == len(rows) and all(isinstance(row, Mapping) and _linear_system_ok(row) for row in linear_systems)
    if surfaces:
        checks["source_v52_surface_components_closed_genus_orientation_owner"] = len(surfaces) == len(rows) and all(isinstance(row, Mapping) and _surface_ok(row) for row in surfaces)
    return checks
