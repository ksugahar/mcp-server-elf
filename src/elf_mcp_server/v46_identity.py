from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


_SESSION = "v46_source_tool_licensed_session_attach_timeout_partial_mao_column_mismatch"
_FORCE = "v46_source_tool_virtual_work_displacement_unit_scale_coordinate_frame_nonfinite_mismatch"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _finite_sequence(value: object, *, minimum: int = 1) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) >= minimum
        and all(isinstance(item, (int, float)) and math.isfinite(float(item)) for item in value)
    )


def _linked(row: Mapping[str, object], fields: tuple[str, ...]) -> bool:
    generation = str(row.get("generation", "")).strip()
    present = [field for field in fields if field in row]
    return bool(generation) and all(row.get(field) == generation for field in present)


def _session_ok(row: Mapping[str, object]) -> bool:
    return (
        _linked(row, ("session_generation", "timeout_generation", "partial_generation", "column_generation", "result_generation"))
        and row.get("session_attached") == row.get("result_session_attached") is True
        and str(row.get("session_identity", "")).startswith("session:")
        and row.get("result_session_identity") == row.get("session_identity")
        and isinstance(row.get("timeout_s"), (int, float))
        and math.isfinite(float(row["timeout_s"]))
        and float(row["timeout_s"]) > 0.0
        and row.get("result_timeout_s") == row.get("timeout_s")
        and row.get("partial_result") == row.get("result_partial_result") is False
        and row.get("result_authority") == ".mao"
        and ("result_result_authority" not in row or row.get("result_result_authority") == ".mao")
        and row.get("column_order") == row.get("result_column_order") == ["time_s", "force_n", "torque_nm", "power_w"]
        and str(row.get("result_owner", "")).startswith("result:")
        and row.get("result_result_owner") == row.get("result_owner")
        and _digest(row.get("result_sha256"))
        and row.get("accepted_result_sha256") == row.get("result_sha256")
    )


def _force_ok(row: Mapping[str, object]) -> bool:
    return (
        _linked(row, ("displacement_generation", "unit_scale_generation", "frame_generation", "finite_generation", "convergence_generation", "result_generation"))
        and row.get("displacement_unit") == row.get("result_displacement_unit") == "m"
        and row.get("displacement_unit_scale_to_si") == row.get("result_displacement_unit_scale_to_si") == 1.0
        and row.get("coordinate_frame") == row.get("result_coordinate_frame") == "global_cartesian"
        and row.get("nonfinite_value_count") == row.get("result_nonfinite_value_count") == 0
        and row.get("converged") == row.get("result_converged") is True
        and _finite_sequence(row.get("displacement_direction"), minimum=3)
        and row.get("displacement_direction") == row.get("result_displacement_direction")
        and str(row.get("result_owner", "")).startswith("result:")
        and row.get("result_result_owner") == row.get("result_owner")
        and _digest(row.get("result_sha256"))
        and row.get("accepted_result_sha256") == row.get("result_sha256")
    )


def validate_source_v46_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    checks: dict[str, bool] = {}
    sessions = [row[_SESSION] for row in rows if _SESSION in row]
    forces = [row[_FORCE] for row in rows if _FORCE in row]
    if sessions:
        checks["elf_v46_mao_session_identity"] = len(sessions) == len(rows) and all(isinstance(row, Mapping) and _session_ok(row) for row in sessions)
    if forces:
        checks["elf_v46_virtual_work_identity"] = len(forces) == len(rows) and all(isinstance(row, Mapping) and _force_ok(row) for row in forces)
    return checks
