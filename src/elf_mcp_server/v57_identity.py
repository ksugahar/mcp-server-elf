"""Public-safe singular BEM and multipole replay checks for v57."""

from __future__ import annotations

import math
from collections.abc import Mapping

from .v58_identity import validate_source_v58_identity


SINGULAR = "bem_singularquadrature_panelorientation_solidangle_collocation_owner_identity"
MULTIPOLE = "multipole_tree_order_translation_error_blockowner_resultowner_identity"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _number(value: object, *, positive: bool = False, nonnegative: bool = False) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    number = float(value)
    return math.isfinite(number) and (not positive or number > 0.0) and (not nonnegative or number >= 0.0)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _singular_ok(row: Mapping[str, object]) -> bool:
    names = ("singular_quadrature", "quadrature_order", "panel_orientation", "solid_angle_sr", "collocation_identity", "panel_owner")
    return (
        _generations(row, "quadrature_generation", "orientation_generation", "angle_generation", "collocation_generation", "owner_generation", "result_generation")
        and row.get("singular_quadrature") in {"duffy", "singularity_subtraction", "analytic"}
        and isinstance(row.get("quadrature_order"), int) and not isinstance(row.get("quadrature_order"), bool) and row.get("quadrature_order") > 0
        and row.get("panel_orientation") == "outward"
        and _number(row.get("solid_angle_sr"), positive=True) and math.isclose(float(row["solid_angle_sr"]), 2.0 * math.pi, rel_tol=1.0e-9)
        and str(row.get("collocation_identity") or "").startswith("collocation:")
        and str(row.get("panel_owner") or "").startswith("panel-owner:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names)
        and _result(row)
    )


def _multipole_ok(row: Mapping[str, object]) -> bool:
    ownership = row.get("block_ownership")
    ownership_ok = isinstance(ownership, Mapping) and bool(ownership) and all(isinstance(block, str) and block.startswith("block:") and isinstance(rank, str) and rank.startswith("rank:") and rank[5:].isdigit() for block, rank in ownership.items())
    estimate = row.get("relative_error_estimate")
    tolerance = row.get("relative_error_tolerance")
    names = ("tree_depth", "multipole_order", "translation_operator", "relative_error_estimate", "relative_error_tolerance", "block_ownership", "result_owner")
    return (
        _generations(row, "tree_generation", "order_generation", "translation_generation", "error_generation", "block_generation", "owner_generation", "result_generation")
        and isinstance(row.get("tree_depth"), int) and not isinstance(row.get("tree_depth"), bool) and row.get("tree_depth") > 0
        and isinstance(row.get("multipole_order"), int) and not isinstance(row.get("multipole_order"), bool) and row.get("multipole_order") > 0
        and row.get("translation_operator") == "m2l"
        and _number(estimate, nonnegative=True) and _number(tolerance, positive=True) and float(tolerance) < 1.0 and float(estimate) <= float(tolerance)
        and ownership_ok and str(row.get("result_owner") or "").startswith("result:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names)
        and _result(row)
    )


def validate_source_v57_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    singular = [row[SINGULAR] for row in rows if SINGULAR in row]
    multipole = [row[MULTIPOLE] for row in rows if MULTIPOLE in row]
    checks: dict[str, bool] = validate_source_v58_identity(identities)
    if singular:
        checks["source_v57_bem_singular_orientation_angle_owner"] = len(singular) == len(rows) and all(isinstance(item, Mapping) and _singular_ok(item) for item in singular)
    if multipole:
        checks["source_v57_multipole_tree_translation_error_owner"] = len(multipole) == len(rows) and all(isinstance(item, Mapping) and _multipole_ok(item) for item in multipole)
    return checks
