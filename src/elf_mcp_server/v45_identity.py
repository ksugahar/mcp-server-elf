from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _closed(row: Mapping[str, object], fields: tuple[str, ...]) -> bool:
    generation = str(row.get("generation", "")).strip()
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _finite(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value) and all(isinstance(item, (int, float)) and math.isfinite(float(item)) for item in value)


def validate_source_v45_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    checks: dict[str, bool] = {}
    tables = [row.get("v45_source_mao_result_release_units_column_order_model_generation_owner_digest_mismatch") for row in rows if isinstance(row.get("v45_source_mao_result_release_units_column_order_model_generation_owner_digest_mismatch"), Mapping)]
    if tables:
        checks["elf_v45_mao_table_generation"] = len(tables) == len(rows) and all(_closed(row, ("release_generation", "units_generation", "column_order_generation", "model_generation", "owner_generation", "result_generation")) for row in tables)
        checks["elf_v45_mao_table_values"] = all(row.get("release") == row.get("result_release") and row.get("units") == row.get("result_units") == {"force": "N", "torque": "N*m", "power": "W"} and row.get("column_order") == row.get("result_column_order") == ["time_s", "force_n", "torque_nm", "power_w"] for row in tables)
        checks["elf_v45_mao_table_owner"] = all(str(row.get("model_owner", "")).startswith("model:") and row.get("result_model_owner") == row.get("model_owner") and str(row.get("result_owner", "")).startswith("result:") and row.get("result_result_owner") == row.get("result_owner") and _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256") for row in tables)
    forces = [row.get("v45_source_virtual_work_displacement_direction_energy_fit_reference_geometry_owner_mismatch") for row in rows if isinstance(row.get("v45_source_virtual_work_displacement_direction_energy_fit_reference_geometry_owner_mismatch"), Mapping)]
    if forces:
        checks["elf_v45_virtual_work_generation"] = len(forces) == len(rows) and all(_closed(row, ("displacement_generation", "direction_generation", "energy_fit_generation", "reference_geometry_generation", "convergence_generation", "result_generation", "owner_generation")) for row in forces)
        checks["elf_v45_virtual_work_values"] = all(row.get("displacement_direction") == row.get("result_displacement_direction") and row.get("displacement_steps_m") == row.get("result_displacement_steps_m") == sorted(row.get("displacement_steps_m")) and row.get("energy_samples_j") == row.get("result_energy_samples_j") and row.get("energy_fit_order") == row.get("result_energy_fit_order") == 2 and row.get("force_n") == row.get("result_force_n") == 100.0 and str(row.get("reference_geometry", "")).startswith("geometry:") and row.get("result_reference_geometry") == row.get("reference_geometry") for row in forces)
        checks["elf_v45_virtual_work_owner"] = all(str(row.get("result_owner", "")).startswith("result:") and row.get("result_result_owner") == row.get("result_owner") and _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256") for row in forces)
    return checks
