"""Public-safe BEM mesh and nonlinear B-H replay checks for v58."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


MESH = "bem_duplicatepanel_nonmanifold_normal_solidangle_meshowner_identity"
NONLINEAR = "nonlinear_bh_relaxation_residual_iteration_material_owner_identity"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _number(value: object, *, positive: bool = False, nonnegative: bool = False) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    number = float(value)
    return math.isfinite(number) and (not positive or number > 0.0) and (not nonnegative or number >= 0.0)


def _close(left: object, right: object) -> bool:
    return _number(left) and _number(right) and math.isclose(float(left), float(right), rel_tol=1.0e-9, abs_tol=1.0e-10)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _mesh_ok(row: Mapping[str, object]) -> bool:
    panel_count = row.get("panel_count")
    unique_count = row.get("unique_panel_count")
    duplicate_count = row.get("duplicate_panel_count")
    incidence = row.get("edge_incidence")
    counts_ok = all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (panel_count, unique_count, duplicate_count))
    incidence_ok = (
        isinstance(incidence, Mapping)
        and set(incidence) == {"boundary", "manifold", "nonmanifold"}
        and all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in incidence.values())
    )
    names = (
        "panel_count", "unique_panel_count", "duplicate_panel_count", "edge_incidence", "normal_orientation",
        "minimum_normal_centroid_dot", "solid_angle_sum_sr", "mesh_revision", "mesh_owner",
    )
    return (
        _generations(row, "panel_generation", "edge_generation", "normal_generation", "angle_generation", "owner_generation", "result_generation")
        and counts_ok and int(panel_count) > 0 and panel_count == unique_count and duplicate_count == 0
        and incidence_ok and incidence["boundary"] == 0 and incidence["nonmanifold"] == 0 and incidence["manifold"] > 0
        and row.get("normal_orientation") == "outward"
        and _number(row.get("minimum_normal_centroid_dot"), positive=True)
        and _close(row.get("solid_angle_sum_sr"), 4.0 * math.pi)
        and str(row.get("mesh_revision") or "").startswith("mesh:")
        and str(row.get("mesh_owner") or "").startswith("mesh-owner:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names)
        and _result(row)
    )


def _series(value: object, *, minimum: int = 2) -> list[float] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) < minimum or not all(_number(item) for item in value):
        return None
    return [float(item) for item in value]


def _nonlinear_ok(row: Mapping[str, object]) -> bool:
    b_values = _series(row.get("b_t"), minimum=3)
    h_values = _series(row.get("h_a_m"), minimum=3)
    residuals = _series(row.get("residual_history"), minimum=2)
    operating = row.get("operating_point")
    relaxation = row.get("relaxation_factor")
    tolerance = row.get("residual_tolerance")
    iterations = row.get("iteration_count")
    if (
        b_values is None or h_values is None or len(b_values) != len(h_values) or residuals is None
        or not isinstance(operating, Mapping) or set(operating) != {"b_t", "h_a_m"}
        or not all(_number(value, nonnegative=True) for value in operating.values())
        or not _number(relaxation, positive=True) or float(relaxation) > 1.0
        or not _number(tolerance, positive=True)
        or not isinstance(iterations, int) or isinstance(iterations, bool) or iterations != len(residuals)
    ):
        return False
    operating_on_curve = any(_close(operating["b_t"], b_value) and _close(operating["h_a_m"], h_value) for b_value, h_value in zip(b_values, h_values))
    names = (
        "b_t", "h_a_m", "operating_point", "relaxation_factor", "residual_history", "residual_tolerance",
        "iteration_count", "converged", "material_revision", "result_owner",
    )
    return (
        _generations(row, "bh_generation", "relaxation_generation", "residual_generation", "iteration_generation", "material_generation", "owner_generation", "result_generation")
        and all(left < right for left, right in zip(b_values, b_values[1:]))
        and all(left < right for left, right in zip(h_values, h_values[1:]))
        and operating_on_curve
        and all(left > right >= 0.0 for left, right in zip(residuals, residuals[1:]))
        and residuals[-1] <= float(tolerance) and row.get("converged") is True
        and str(row.get("material_revision") or "").startswith("material:")
        and str(row.get("result_owner") or "").startswith("result:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names)
        and _result(row)
    )


def validate_source_v58_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    meshes = [row[MESH] for row in rows if MESH in row]
    nonlinear = [row[NONLINEAR] for row in rows if NONLINEAR in row]
    checks: dict[str, bool] = {}
    if meshes:
        checks["source_v58_bem_mesh_panel_edge_normal_angle_owner"] = len(meshes) == len(rows) and all(isinstance(item, Mapping) and _mesh_ok(item) for item in meshes)
    if nonlinear:
        checks["source_v58_nonlinear_bh_relaxation_residual_material_owner"] = len(nonlinear) == len(rows) and all(isinstance(item, Mapping) and _nonlinear_ok(item) for item in nonlinear)
    return checks
