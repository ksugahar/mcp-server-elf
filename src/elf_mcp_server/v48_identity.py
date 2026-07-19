"""Public-safe complex-column and batch-deck semantic replay checks."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


COMPLEX = "mao_complex_encoding_phase_convention_unit_column_owner_identity"
BATCH = "batch_include_macro_override_precedence_workdir_run_owner_identity"


def _sha(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _generation(row: Mapping[str, object], names: tuple[str, ...]) -> bool:
    value = str(row.get("generation") or "")
    return bool(value) and all(row.get(name) == value for name in names)


def _digest(row: Mapping[str, object]) -> bool:
    return _sha(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _finite_pair(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 2 and all(
        isinstance(item, (int, float)) and math.isfinite(float(item)) for item in value
    )


def _complex_ok(row: Mapping[str, object]) -> bool:
    values = row.get("complex_rows")
    return (
        _generation(row, ("encoding_generation", "phase_generation", "unit_generation", "column_generation", "result_generation"))
        and row.get("complex_encoding") == row.get("replayed_complex_encoding") == "real_imaginary"
        and row.get("phase_convention") == row.get("replayed_phase_convention") == "positive_lead_deg"
        and str(row.get("column_name") or "")
        and row.get("replayed_column_name") == row.get("column_name")
        and row.get("column_unit") == row.get("replayed_column_unit") == "A_per_m"
        and isinstance(values, list)
        and bool(values)
        and all(_finite_pair(value) for value in values)
        and row.get("replayed_complex_rows") == values
        and str(row.get("column_owner") or "").startswith("column:")
        and row.get("replayed_column_owner") == row.get("column_owner")
        and _digest(row)
    )


def _batch_ok(row: Mapping[str, object]) -> bool:
    includes = row.get("include_order")
    overrides = row.get("macro_overrides")
    valid_overrides = (
        isinstance(overrides, list)
        and bool(overrides)
        and all(
            isinstance(override, Mapping)
            and bool(str(override.get("name") or ""))
            and override.get("source") in includes
            for override in overrides
        )
    ) if isinstance(includes, list) else False
    return (
        _generation(row, ("include_generation", "macro_generation", "workdir_generation", "run_generation", "result_generation"))
        and isinstance(includes, list)
        and bool(includes)
        and len(set(includes)) == len(includes)
        and all(str(include).endswith(".deck") for include in includes)
        and row.get("replayed_include_order") == includes
        and valid_overrides
        and row.get("replayed_macro_overrides") == overrides
        and row.get("override_precedence") == row.get("replayed_override_precedence") == "last_include_wins"
        and str(row.get("working_directory_id") or "").startswith("workdir:")
        and row.get("replayed_working_directory_id") == row.get("working_directory_id")
        and str(row.get("run_owner") or "").startswith("run:")
        and row.get("replayed_run_owner") == row.get("run_owner")
        and _digest(row)
    )


def validate_source_v48_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    complex_rows = [row[COMPLEX] for row in rows if COMPLEX in row]
    batch_rows = [row[BATCH] for row in rows if BATCH in row]
    checks: dict[str, bool] = {}
    if complex_rows:
        checks["source_v48_complex_encoding_phase_unit_column_owner"] = len(complex_rows) == len(rows) and all(isinstance(row, Mapping) and _complex_ok(row) for row in complex_rows)
    if batch_rows:
        checks["source_v48_batch_include_override_workdir_run_owner"] = len(batch_rows) == len(rows) and all(isinstance(row, Mapping) and _batch_ok(row) for row in batch_rows)
    return checks
