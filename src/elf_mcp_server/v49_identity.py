"""Public-safe binary-layout and material-include replay checks for v49."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath


MAO = "mao_endian_float_precision_record_stride_column_offset_run_owner_identity"
MATERIAL = "material_include_relative_path_case_checksum_precedence_project_owner_identity"


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _offsets(value: object, stride: int, width: int) -> bool:
    return (
        isinstance(value, Mapping)
        and bool(value)
        and all(bool(str(name)) for name in value)
        and all(isinstance(offset, int) and 0 <= offset <= stride - width and offset % width == 0 for offset in value.values())
        and len(set(value.values())) == len(value)
    )


def _mao_ok(row: Mapping[str, object]) -> bool:
    endian = row.get("endianness")
    precision = row.get("float_precision_bits")
    stride = row.get("record_stride_bytes")
    offsets = row.get("column_offsets_bytes")
    owner = str(row.get("run_owner") or "")
    width = int(precision) // 8 if isinstance(precision, int) and precision in {32, 64} else 0
    return (
        _generations(row, "endian_generation", "precision_generation", "layout_generation", "run_generation", "result_generation")
        and endian in {"little", "big"}
        and row.get("replayed_endianness") == endian
        and precision in {32, 64}
        and row.get("replayed_float_precision_bits") == precision
        and isinstance(stride, int)
        and stride > 0
        and width > 0
        and stride % width == 0
        and row.get("replayed_record_stride_bytes") == stride
        and _offsets(offsets, stride, width)
        and row.get("replayed_column_offsets_bytes") == offsets
        and owner.startswith("run:")
        and row.get("replayed_run_owner") == owner
        and _result(row)
    )


def _relative_paths(value: object) -> bool:
    if not isinstance(value, list) or not value or len(set(value)) != len(value):
        return False
    for item in value:
        if not isinstance(item, str) or not item or "\\" in item:
            return False
        path = PurePosixPath(item)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".mat":
            return False
    return True


def _checksums(value: object, paths: list[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == set(paths) and all(_digest(digest) for digest in value.values())


def _material_ok(row: Mapping[str, object]) -> bool:
    paths = row.get("relative_include_paths")
    case_policy = row.get("path_case_policy")
    checksums = row.get("include_checksums")
    owner = str(row.get("project_owner") or "")
    return (
        _generations(
            row,
            "path_generation",
            "case_generation",
            "checksum_generation",
            "precedence_generation",
            "project_generation",
            "result_generation",
        )
        and _relative_paths(paths)
        and row.get("replayed_relative_include_paths") == paths
        and case_policy in {"case_sensitive", "case_insensitive"}
        and row.get("replayed_path_case_policy") == case_policy
        and _checksums(checksums, paths)
        and row.get("replayed_include_checksums") == checksums
        and row.get("override_precedence") == row.get("replayed_override_precedence") == "last_include_wins"
        and owner.startswith("project:")
        and row.get("replayed_project_owner") == owner
        and _result(row)
    )


def validate_source_v49_identity(identities: list[object]) -> dict[str, bool]:
    """Validate optional v49 layout/include records across every source run."""
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    mao_rows = [row[MAO] for row in rows if MAO in row]
    material_rows = [row[MATERIAL] for row in rows if MATERIAL in row]
    checks: dict[str, bool] = {}
    if mao_rows:
        checks["source_v49_mao_endian_precision_stride_offset_run_owner"] = len(mao_rows) == len(rows) and all(
            isinstance(row, Mapping) and _mao_ok(row) for row in mao_rows
        )
    if material_rows:
        checks["source_v49_material_path_case_checksum_precedence_project_owner"] = len(material_rows) == len(rows) and all(
            isinstance(row, Mapping) and _material_ok(row) for row in material_rows
        )
    return checks
