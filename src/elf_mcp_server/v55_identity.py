"""Public-safe H-matrix and far-field replay checks for v55."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .v56_identity import validate_source_v56_identity


HMATRIX = "hmatrix_cluster_admissibility_rank_tolerance_block_owner_identity"
FARFIELD = "bem_farfield_multipoleorder_expansioncenter_error_owner_identity"


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get("accepted_result_sha256") == row.get("result_sha256")


def _hmatrix_ok(row: Mapping[str, object]) -> bool:
    clusters = row.get("cluster_tree")
    clusters_ok = isinstance(clusters, Mapping) and "c0" in clusters and bool(clusters)
    if clusters_ok:
        clusters_ok = all(isinstance(name, str) and isinstance(node, Mapping) and set(node) == {"size", "children"} and isinstance(node["size"], int) and not isinstance(node["size"], bool) and node["size"] > 0 and isinstance(node["children"], list) and all(child in clusters for child in node["children"]) for name, node in clusters.items())
    blocks = row.get("block_partition")
    blocks_ok = clusters_ok and isinstance(blocks, list) and bool(blocks)
    if blocks_ok:
        seen: set[str] = set()
        for block in blocks:
            if not isinstance(block, Mapping) or set(block) != {"block_id", "source_cluster", "target_cluster", "admissible", "rank"} or not isinstance(block["block_id"], str) or block["block_id"] in seen or block["source_cluster"] not in clusters or block["target_cluster"] not in clusters or block["admissible"] is not True or not isinstance(block["rank"], int) or isinstance(block["rank"], bool) or not 0 < block["rank"] < min(clusters[block["source_cluster"]]["size"], clusters[block["target_cluster"]]["size"]):
                blocks_ok = False; break
            seen.add(block["block_id"])
    eta = row.get("admissibility_eta"); tolerance = row.get("compression_tolerance")
    return (_generations(row, "cluster_generation", "admissibility_generation", "rank_generation", "tolerance_generation", "block_generation", "owner_generation", "result_generation") and clusters_ok and row.get("replayed_cluster_tree") == clusters and _finite(eta) and float(eta) > 0.0 and row.get("replayed_admissibility_eta") == eta and _finite(tolerance) and 0.0 < float(tolerance) < 1.0 and row.get("replayed_compression_tolerance") == tolerance and blocks_ok and row.get("replayed_block_partition") == blocks and str(row.get("matrix_owner") or "").startswith("matrix:") and row.get("replayed_matrix_owner") == row.get("matrix_owner") and _result(row))


def _farfield_ok(row: Mapping[str, object]) -> bool:
    order = row.get("multipole_order"); center = row.get("expansion_center_m"); radius = row.get("expansion_radius_m"); errors = row.get("observation_errors"); tolerance = row.get("error_tolerance")
    center_ok = isinstance(center, Sequence) and not isinstance(center, (str, bytes)) and len(center) == 3 and all(_finite(value) for value in center)
    errors_ok = isinstance(errors, list) and len(errors) >= 2 and _finite(radius) and float(radius) > 0.0 and _finite(tolerance) and 0.0 < float(tolerance) < 1.0
    if errors_ok:
        errors_ok = all(isinstance(item, Mapping) and set(item) == {"distance_m", "relative_error"} and _finite(item["distance_m"]) and float(item["distance_m"]) > 2.0 * float(radius) and _finite(item["relative_error"]) and 0.0 <= float(item["relative_error"]) <= float(tolerance) for item in errors)
    if errors_ok:
        errors_ok = all(float(left["distance_m"]) < float(right["distance_m"]) and float(left["relative_error"]) >= float(right["relative_error"]) for left, right in zip(errors, errors[1:]))
    return (_generations(row, "order_generation", "center_generation", "distance_generation", "error_generation", "owner_generation", "result_generation") and isinstance(order, int) and not isinstance(order, bool) and order >= 1 and row.get("replayed_multipole_order") == order and center_ok and row.get("replayed_expansion_center_m") == center and row.get("replayed_expansion_radius_m") == radius and errors_ok and row.get("replayed_observation_errors") == errors and row.get("replayed_error_tolerance") == tolerance and str(row.get("run_owner") or "").startswith("run:") and row.get("replayed_run_owner") == row.get("run_owner") and _result(row))


def validate_source_v55_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    hmatrices = [row[HMATRIX] for row in rows if HMATRIX in row]; farfields = [row[FARFIELD] for row in rows if FARFIELD in row]
    checks: dict[str, bool] = validate_source_v56_identity(identities)
    if hmatrices:
        checks["source_v55_hmatrix_cluster_admissibility_rank_tolerance_owner"] = len(hmatrices) == len(rows) and all(isinstance(item, Mapping) and _hmatrix_ok(item) for item in hmatrices)
    if farfields:
        checks["source_v55_farfield_order_center_distance_error_owner"] = len(farfields) == len(rows) and all(isinstance(item, Mapping) and _farfield_ok(item) for item in farfields)
    return checks
