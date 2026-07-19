"""Source-native identity checks for product result replays."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


_TABLE = "mao_result_table_release_units_column_order_model_owner_digest_identity"
_FORCE = "mao_force_virtualwork_displacement_energyfit_reference_owner_identity"


def _same(row: Mapping[str, object], left: str, right: str) -> bool:
    return row.get(left) == row.get(right)


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _finite_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value) and all(
        isinstance(item, (int, float)) and math.isfinite(float(item)) for item in value
    )


def _table_ok(row: Mapping[str, object]) -> bool:
    generation = str(row.get("mao_table_generation", "")).strip()
    linked = ("release_generation", "units_generation", "column_order_generation", "model_generation", "owner_generation", "result_generation")
    return (
        bool(generation)
        and all(row.get(key) == generation for key in linked)
        and _same(row, "release", "result_release")
        and isinstance(row.get("units"), Mapping)
        and _same(row, "units", "result_units")
        and row.get("units") == {"force": "N", "torque": "N*m", "power": "W"}
        and isinstance(row.get("column_order"), list)
        and row.get("column_order") == row.get("result_column_order")
        and row.get("column_order") == ["time_s", "force_n", "torque_nm", "power_w"]
        and str(row.get("model_owner", "")).startswith("model:")
        and row.get("result_model_owner") == row.get("model_owner")
        and str(row.get("result_owner", "")).startswith("result:")
        and row.get("result_result_owner") == row.get("result_owner")
        and _digest(row.get("mao_result_sha256"))
        and row.get("accepted_mao_result_sha256") == row.get("mao_result_sha256")
    )


def _force_ok(row: Mapping[str, object]) -> bool:
    generation = str(row.get("mao_force_generation", "")).strip()
    linked = ("displacement_generation", "direction_generation", "energyfit_generation", "reference_generation", "convergence_generation", "result_generation", "owner_generation")
    direction = row.get("displacement_direction")
    return (
        bool(generation)
        and all(row.get(key) == generation for key in linked)
        and isinstance(direction, list)
        and len(direction) == 3
        and _finite_sequence(direction)
        and row.get("result_displacement_direction") == direction
        and row.get("displacement_steps_m") == row.get("result_displacement_steps_m")
        and isinstance(row.get("displacement_steps_m"), list)
        and row.get("displacement_steps_m") == sorted(row.get("displacement_steps_m"))
        and _finite_sequence(row.get("energy_samples_j"))
        and row.get("energy_samples_j") == row.get("result_energy_samples_j")
        and row.get("energy_fit_order") == row.get("result_energy_fit_order") == 2
        and row.get("force_n") == row.get("result_force_n") == 100.0
        and str(row.get("reference_geometry", "")).startswith("geometry:")
        and row.get("result_reference_geometry") == row.get("reference_geometry")
        and str(row.get("result_owner", "")).startswith("result:")
        and row.get("result_result_owner") == row.get("result_owner")
        and _digest(row.get("mao_force_result_sha256"))
        and row.get("accepted_mao_force_result_sha256") == row.get("mao_force_result_sha256")
    )


def validate_source_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    table_rows = [row[_TABLE] for row in rows if _TABLE in row]
    force_rows = [row[_FORCE] for row in rows if _FORCE in row]
    checks: dict[str, bool] = {}
    if table_rows:
        checks["source_v44_mao_table_release_units_identity"] = len(table_rows) == len(rows) and all(isinstance(row, Mapping) and _table_ok(row) for row in table_rows)
    if force_rows:
        checks["source_v44_virtualwork_force_identity"] = len(force_rows) == len(rows) and all(isinstance(row, Mapping) and _force_ok(row) for row in force_rows)
    return checks
