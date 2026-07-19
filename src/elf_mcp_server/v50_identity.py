"""Public-safe input-deck and sparse-table replay checks for v50."""

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import PurePosixPath


DECK = "input_deck_continuation_include_encoding_newline_checksum_run_owner_identity"
SPARSE = "mao_sparse_table_sentinel_missing_row_exponent_unit_result_owner_identity"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _include_paths(value: object) -> bool:
    if not isinstance(value, list) or not value or len(set(value)) != len(value):
        return False
    for item in value:
        if not isinstance(item, str) or not item or "\\" in item:
            return False
        path = PurePosixPath(item)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() not in {".inc", ".mat"}:
            return False
    return True


def _deck_ok(row: Mapping[str, object]) -> bool:
    marker = row.get("continuation_marker")
    paths = row.get("include_paths")
    encoding = row.get("encoding")
    newline = row.get("newline_convention")
    deck_digest = row.get("deck_sha256")
    owner = str(row.get("run_owner") or "")
    return (
        _generations(row, "continuation_generation", "include_generation", "encoding_generation", "newline_generation", "checksum_generation", "result_generation")
        and marker in {"&", "+"}
        and row.get("replayed_continuation_marker") == marker
        and _include_paths(paths)
        and row.get("replayed_include_paths") == paths
        and encoding in {"utf-8", "ascii", "shift_jis"}
        and row.get("replayed_encoding") == encoding
        and newline in {"crlf", "lf"}
        and row.get("replayed_newline_convention") == newline
        and _digest(deck_digest)
        and row.get("replayed_deck_sha256") == deck_digest
        and owner.startswith("run:")
        and row.get("replayed_run_owner") == owner
        and _result(row)
    )


def _missing_rows(value: object) -> bool:
    return (
        isinstance(value, list)
        and value == sorted(set(value))
        and all(isinstance(index, int) and index >= 0 for index in value)
    )


def _sentinel(value: object) -> bool:
    if not isinstance(value, str) or "E" not in value.upper():
        return False
    try:
        number = float(value.replace("D", "E").replace("d", "e"))
    except ValueError:
        return False
    return math.isfinite(number) and abs(number) >= 1.0e20


def _sparse_ok(row: Mapping[str, object]) -> bool:
    sentinel = row.get("missing_value_sentinel")
    missing = row.get("missing_row_indices")
    exponent = row.get("exponent_notation")
    unit = str(row.get("value_unit") or "")
    owner = str(row.get("result_owner") or "")
    return (
        _generations(row, "sentinel_generation", "row_generation", "exponent_generation", "unit_generation", "result_generation")
        and _sentinel(sentinel)
        and row.get("replayed_missing_value_sentinel") == sentinel
        and _missing_rows(missing)
        and row.get("replayed_missing_row_indices") == missing
        and exponent in {"E", "D"}
        and row.get("replayed_exponent_notation") == exponent
        and bool(unit)
        and row.get("replayed_value_unit") == unit
        and owner.startswith("result:")
        and row.get("replayed_result_owner") == owner
        and _result(row)
    )


def validate_source_v50_identity(identities: list[object]) -> dict[str, bool]:
    """Validate optional v50 deck/sparse records across every source run."""
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    deck_rows = [row[DECK] for row in rows if DECK in row]
    sparse_rows = [row[SPARSE] for row in rows if SPARSE in row]
    checks: dict[str, bool] = {}
    if deck_rows:
        checks["source_v50_deck_continuation_include_encoding_newline_checksum_owner"] = len(deck_rows) == len(rows) and all(isinstance(row, Mapping) and _deck_ok(row) for row in deck_rows)
    if sparse_rows:
        checks["source_v50_mao_sparse_sentinel_rows_exponent_unit_owner"] = len(sparse_rows) == len(rows) and all(isinstance(row, Mapping) and _sparse_ok(row) for row in sparse_rows)
    return checks
