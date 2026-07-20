"""Public-safe multi-zone and vector result replay checks for v51."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


MULTIZONE = "mao_multizone_timeblock_header_timestep_rowcount_result_owner_identity"
VECTOR = "mao_vector_component_order_coordinate_frame_unit_result_owner_identity"


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


def _multizone_ok(row: Mapping[str, object]) -> bool:
    zones = row.get("zone_names")
    timesteps = row.get("timesteps_s")
    headers = row.get("time_block_headers")
    counts = row.get("row_counts")
    zones_ok = isinstance(zones, list) and bool(zones) and all(isinstance(zone, str) and bool(zone) for zone in zones) and len(zones) == len(set(zones))
    times_ok = isinstance(timesteps, list) and bool(timesteps) and all(_finite(value) for value in timesteps) and all(float(left) < float(right) for left, right in zip(timesteps, timesteps[1:]))
    expected = {(zone, float(time)) for time in timesteps for zone in zones} if zones_ok and times_ok else set()
    header_pairs = {(item.get("zone"), float(item["time_s"])) for item in headers if isinstance(item, Mapping) and _finite(item.get("time_s"))} if isinstance(headers, list) else set()
    count_pairs = {(item.get("zone"), float(item["time_s"])) for item in counts if isinstance(item, Mapping) and _finite(item.get("time_s")) and isinstance(item.get("rows"), int) and not isinstance(item.get("rows"), bool) and item["rows"] > 0} if isinstance(counts, list) else set()
    return (
        _generations(row, "zone_generation", "header_generation", "timestep_generation", "rowcount_generation", "owner_generation", "result_generation")
        and zones_ok
        and row.get("replayed_zone_names") == zones
        and times_ok
        and row.get("replayed_timesteps_s") == timesteps
        and isinstance(headers, list)
        and len(headers) == len(expected)
        and header_pairs == expected
        and row.get("replayed_time_block_headers") == headers
        and isinstance(counts, list)
        and len(counts) == len(expected)
        and count_pairs == expected
        and row.get("replayed_row_counts") == counts
        and str(row.get("result_owner") or "").startswith("result:")
        and row.get("replayed_result_owner") == row.get("result_owner")
        and _result(row)
    )


def _vector_ok(row: Mapping[str, object]) -> bool:
    components = row.get("component_order")
    vectors = row.get("vector_rows")
    return (
        _generations(row, "component_generation", "frame_generation", "unit_generation", "value_generation", "owner_generation", "result_generation")
        and components == ["x", "y", "z"]
        and row.get("replayed_component_order") == components
        and row.get("coordinate_frame") == "global_cartesian"
        and row.get("replayed_coordinate_frame") == row.get("coordinate_frame")
        and row.get("vector_unit") == "T"
        and row.get("replayed_vector_unit") == row.get("vector_unit")
        and isinstance(vectors, list)
        and bool(vectors)
        and all(isinstance(vector, Sequence) and not isinstance(vector, (str, bytes)) and len(vector) == 3 and all(_finite(value) for value in vector) for vector in vectors)
        and row.get("replayed_vector_rows") == vectors
        and str(row.get("result_owner") or "").startswith("result:")
        and row.get("replayed_result_owner") == row.get("result_owner")
        and _result(row)
    )


def validate_source_v51_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    multizone_rows = [row[MULTIZONE] for row in rows if MULTIZONE in row]
    vector_rows = [row[VECTOR] for row in rows if VECTOR in row]
    checks: dict[str, bool] = {}
    if multizone_rows:
        checks["source_v51_mao_multizone_headers_timesteps_rows_owner"] = len(multizone_rows) == len(rows) and all(isinstance(row, Mapping) and _multizone_ok(row) for row in multizone_rows)
    if vector_rows:
        checks["source_v51_mao_vector_components_frame_unit_owner"] = len(vector_rows) == len(rows) and all(isinstance(row, Mapping) and _vector_ok(row) for row in vector_rows)
    return checks
