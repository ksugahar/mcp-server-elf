"""Public-safe magnetization-curve and surface-seam replay checks for v53."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .v54_identity import validate_source_v54_identity


CURVE = "magnetization_curve_interpolation_extrapolation_branch_material_owner_identity"
SEAM = "cad_surface_seam_duplicate_panel_normal_mesh_owner_identity"


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


def _curve_ok(row: Mapping[str, object]) -> bool:
    points = row.get("curve_points")
    points_ok = isinstance(points, Sequence) and not isinstance(points, (str, bytes)) and len(points) >= 3
    if points_ok:
        points_ok = all(isinstance(point, Mapping) and set(point) == {"h_a_per_m", "b_t"} and _finite(point["h_a_per_m"]) and _finite(point["b_t"]) for point in points)
    if points_ok:
        points_ok = all(float(left["h_a_per_m"]) < float(right["h_a_per_m"]) and float(left["b_t"]) <= float(right["b_t"]) for left, right in zip(points, points[1:]))
    return (
        _generations(row, "point_generation", "interpolation_generation", "extrapolation_generation", "branch_generation", "owner_generation", "result_generation")
        and points_ok
        and row.get("replayed_curve_points") == points
        and row.get("interpolation") == "monotone_cubic"
        and row.get("replayed_interpolation") == row.get("interpolation")
        and row.get("extrapolation") == "linear_recoil"
        and row.get("replayed_extrapolation") == row.get("extrapolation")
        and str(row.get("branch_id") or "").startswith("branch:")
        and row.get("replayed_branch_id") == row.get("branch_id")
        and str(row.get("material_owner") or "").startswith("material:")
        and row.get("replayed_material_owner") == row.get("material_owner")
        and _result(row)
    )


def _unit_normal(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 3 and all(_finite(item) for item in value) and math.isclose(sum(float(item) ** 2 for item in value), 1.0, rel_tol=1.0e-12, abs_tol=1.0e-12)


def _seam_ok(row: Mapping[str, object]) -> bool:
    seams = row.get("seam_pairs")
    normals = row.get("panel_normals")
    seams_ok = isinstance(seams, Sequence) and not isinstance(seams, (str, bytes)) and bool(seams)
    panel_ids: set[int] = set()
    if seams_ok:
        seen: set[tuple[int, int, int, int]] = set()
        for seam in seams:
            if not isinstance(seam, Mapping) or set(seam) != {"left_panel", "right_panel", "left_edge", "right_edge"}:
                seams_ok = False
                break
            values = tuple(seam[name] for name in ("left_panel", "right_panel", "left_edge", "right_edge"))
            if not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in values) or seam["left_panel"] == seam["right_panel"] or values in seen:
                seams_ok = False
                break
            seen.add(values); panel_ids.update((seam["left_panel"], seam["right_panel"]))
    normals_ok = isinstance(normals, Mapping) and set(normals) == {str(panel) for panel in panel_ids} and all(_unit_normal(normal) for normal in normals.values())
    return (
        _generations(row, "seam_generation", "duplicate_generation", "normal_generation", "owner_generation", "result_generation")
        and seams_ok
        and row.get("replayed_seam_pairs") == seams
        and row.get("duplicate_panel_ids") == []
        and row.get("replayed_duplicate_panel_ids") == []
        and normals_ok
        and row.get("replayed_panel_normals") == normals
        and str(row.get("mesh_owner") or "").startswith("mesh:")
        and row.get("replayed_mesh_owner") == row.get("mesh_owner")
        and _result(row)
    )


def validate_source_v53_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    curves = [row[CURVE] for row in rows if CURVE in row]
    seams = [row[SEAM] for row in rows if SEAM in row]
    checks = validate_source_v54_identity(identities)
    if curves:
        checks["source_v53_curve_interpolation_extrapolation_branch_owner"] = len(curves) == len(rows) and all(isinstance(row, Mapping) and _curve_ok(row) for row in curves)
    if seams:
        checks["source_v53_surface_seam_duplicate_normal_mesh_owner"] = len(seams) == len(rows) and all(isinstance(row, Mapping) and _seam_ok(row) for row in seams)
    return checks
