"""Source-native MAO and licensed-run replay lineage checks."""

from __future__ import annotations

from collections.abc import Mapping


MAO = "v47_source_tool_mao_schema_column_case_index_order_duplicate_mismatch"
RUN = "v47_source_tool_licensed_run_model_result_generation_batch_index_owner_mismatch"


def _sha(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(char in "0123456789abcdef" for char in text)


def _generation(row: Mapping[str, object], names: tuple[str, ...]) -> bool:
    value = str(row.get("generation") or "")
    return bool(value) and all(row.get(name) == value for name in names)


def _digest(row: Mapping[str, object]) -> bool:
    return _sha(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _mao_ok(row: Mapping[str, object]) -> bool:
    columns = row.get("column_order")
    indices = row.get("case_indices")
    return (
        _generation(
            row,
            ("schema_generation", "column_generation", "case_index_generation", "run_generation", "result_generation"),
        )
        and row.get("schema_version") == row.get("replayed_schema_version") == "mao:v1"
        and isinstance(columns, list)
        and columns == ["case_index", "force_n", "torque_nm", "power_w"]
        and len(columns) == len(set(columns))
        and row.get("replayed_column_order") == columns
        and isinstance(indices, list)
        and bool(indices)
        and all(isinstance(index, int) and index >= 0 for index in indices)
        and indices == sorted(indices)
        and len(indices) == len(set(indices))
        and row.get("replayed_case_indices") == indices
        and str(row.get("run_owner") or "").startswith("run:")
        and row.get("replayed_run_owner") == row.get("run_owner")
        and _digest(row)
    )


def _run_ok(row: Mapping[str, object]) -> bool:
    batch = row.get("batch_index")
    return (
        _generation(
            row,
            ("license_generation", "model_generation", "result_generation", "batch_generation", "owner_generation"),
        )
        and row.get("session_attached") == row.get("result_session_attached") is True
        and str(row.get("model_generation_id") or "").startswith("model:")
        and row.get("replayed_model_generation_id") == row.get("model_generation_id")
        and str(row.get("result_generation_id") or "").startswith("result:")
        and row.get("replayed_result_generation_id") == row.get("result_generation_id")
        and isinstance(batch, int)
        and batch >= 0
        and row.get("replayed_batch_index") == batch
        and str(row.get("run_owner") or "").startswith("run:")
        and row.get("replayed_run_owner") == row.get("run_owner")
        and _digest(row)
    )


def validate_source_v47_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    mao_rows = [row[MAO] for row in rows if MAO in row]
    run_rows = [row[RUN] for row in rows if RUN in row]
    checks: dict[str, bool] = {}
    if mao_rows:
        checks["source_v47_mao_schema_column_case_owner_identity"] = (
            len(mao_rows) == len(rows) and all(isinstance(row, Mapping) and _mao_ok(row) for row in mao_rows)
        )
    if run_rows:
        checks["source_v47_licensed_run_generation_batch_owner_identity"] = (
            len(run_rows) == len(rows) and all(isinstance(row, Mapping) and _run_ok(row) for row in run_rows)
        )
    return checks
