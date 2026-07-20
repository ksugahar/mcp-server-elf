"""Public-safe BEM mesh and iterative-solver replay checks."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

MESH = "bem_closedmesh_solidangle_orientation_region_owner_identity"
SOLVER = "solver_residual_tolerance_iteration_matrixrevision_owner_identity"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _number(value: object, *, positive: bool = False) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    number = float(value)
    return math.isfinite(number) and (not positive or number > 0.0)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _mesh_ok(row: Mapping[str, object]) -> bool:
    regions = row.get("region_assignment"); names = ("closed_surface", "solid_angle_sr", "panel_orientation", "region_assignment", "mesh_owner")
    return (
        _generations(row, "closure_generation", "angle_generation", "orientation_generation", "region_generation", "owner_generation", "result_generation")
        and row.get("closed_surface") is True and _number(row.get("solid_angle_sr"), positive=True) and math.isclose(float(row["solid_angle_sr"]), 4.0 * math.pi, rel_tol=1.0e-9)
        and row.get("panel_orientation") == "outward" and isinstance(regions, Mapping) and set(regions) == {"inside", "outside"} and str(regions.get("inside") or "").startswith("region:") and regions.get("outside") == "region:vacuum"
        and str(row.get("mesh_owner") or "").startswith("mesh:") and all(row.get("replayed_" + name) == row.get(name) for name in names) and _result(row)
    )


def _solver_ok(row: Mapping[str, object]) -> bool:
    residuals = row.get("residual_history"); tolerance = row.get("relative_tolerance")
    residuals_ok = isinstance(residuals, Sequence) and not isinstance(residuals, (str, bytes)) and len(residuals) >= 2 and all(_number(value, positive=True) for value in residuals) and all(float(left) > float(right) for left, right in zip(residuals, residuals[1:]))
    names = ("residual_history", "relative_tolerance", "iteration_count", "matrix_revision", "run_owner")
    return (
        _generations(row, "residual_generation", "tolerance_generation", "iteration_generation", "matrix_generation", "owner_generation", "result_generation")
        and residuals_ok and _number(tolerance, positive=True) and float(tolerance) < 1.0 and float(residuals[-1]) <= float(tolerance)
        and isinstance(row.get("iteration_count"), int) and not isinstance(row.get("iteration_count"), bool) and row.get("iteration_count") == len(residuals) - 1
        and str(row.get("matrix_revision") or "").startswith("matrix:") and str(row.get("run_owner") or "").startswith("run:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names) and _result(row)
    )


def validate_source_v56_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    meshes = [row[MESH] for row in rows if MESH in row]; solvers = [row[SOLVER] for row in rows if SOLVER in row]
    checks: dict[str, bool] = {}
    if meshes:
        checks["source_v56_bem_closedmesh_solidangle_region_owner"] = len(meshes) == len(rows) and all(isinstance(item, Mapping) and _mesh_ok(item) for item in meshes)
    if solvers:
        checks["source_v56_solver_residual_tolerance_iteration_owner"] = len(solvers) == len(rows) and all(isinstance(item, Mapping) and _solver_ok(item) for item in solvers)
    return checks
