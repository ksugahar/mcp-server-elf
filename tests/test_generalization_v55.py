from copy import deepcopy

from elf_mcp_server.v55_identity import FARFIELD, HMATRIX, validate_source_v55_identity


CASE_IDS = {"v55_source_tool_hmatrix_cluster_admissibility_rank_tolerance_block_owner_mismatch", "v55_source_tool_bem_farfield_multipoleorder_expansioncenter_error_owner_mismatch"}


def _rows():
    gen = lambda name, fields: {"generation": name, **{field: name for field in fields}}
    clusters = {"c0": {"size": 64, "children": ["c1", "c2"]}, "c1": {"size": 32, "children": []}, "c2": {"size": 32, "children": []}}; blocks = [{"block_id": "b12", "source_cluster": "c1", "target_cluster": "c2", "admissible": True, "rank": 8}]
    hmatrix = {**gen("hmatrix-v55", ("cluster_generation", "admissibility_generation", "rank_generation", "tolerance_generation", "block_generation", "owner_generation", "result_generation")), "cluster_tree": clusters, "replayed_cluster_tree": clusters, "admissibility_eta": 2.0, "replayed_admissibility_eta": 2.0, "compression_tolerance": 1.0e-6, "replayed_compression_tolerance": 1.0e-6, "block_partition": blocks, "replayed_block_partition": blocks, "matrix_owner": "matrix:hmatrix-v55", "replayed_matrix_owner": "matrix:hmatrix-v55", "result_sha256": "b" * 64, "accepted_result_sha256": "b" * 64}
    center = [0.0, 0.0, 0.0]; errors = [{"distance_m": 2.0, "relative_error": 2.0e-4}, {"distance_m": 4.0, "relative_error": 4.0e-5}]
    farfield = {**gen("farfield-v55", ("order_generation", "center_generation", "distance_generation", "error_generation", "owner_generation", "result_generation")), "multipole_order": 5, "replayed_multipole_order": 5, "expansion_center_m": center, "replayed_expansion_center_m": center, "expansion_radius_m": 0.5, "replayed_expansion_radius_m": 0.5, "observation_errors": errors, "replayed_observation_errors": errors, "error_tolerance": 1.0e-3, "replayed_error_tolerance": 1.0e-3, "run_owner": "run:farfield-v55", "replayed_run_owner": "run:farfield-v55", "result_sha256": "c" * 64, "accepted_result_sha256": "c" * 64}
    return [{HMATRIX: hmatrix, FARFIELD: farfield}]


def test_v55_positive_source_identities_are_accepted():
    assert all(validate_source_v55_identity(_rows()).values())


def test_v55_frozen_mutations_are_rejected():
    rows = deepcopy(_rows()); rows[0][HMATRIX]["replayed_matrix_owner"] = "matrix:stale"; rows[0][FARFIELD]["replayed_run_owner"] = "run:stale"
    assert not all(validate_source_v55_identity(rows).values())


def test_v55_self_consistent_nonphysical_records_are_rejected():
    rows = deepcopy(_rows()); rows[0][HMATRIX]["compression_tolerance"] = rows[0][HMATRIX]["replayed_compression_tolerance"] = 2.0
    rows[0][FARFIELD]["observation_errors"] = rows[0][FARFIELD]["replayed_observation_errors"] = [{"distance_m": 0.1, "relative_error": 1.0}, {"distance_m": 0.2, "relative_error": 2.0}]
    assert not all(validate_source_v55_identity(rows).values())


def test_v55_malformed_values_reject_without_raising():
    rows = deepcopy(_rows()); rows[0][HMATRIX]["cluster_tree"] = {"c0": {"size": [64], "children": []}}; rows[0][FARFIELD]["expansion_center_m"] = [[0.0], 0.0, 0.0]
    assert not all(validate_source_v55_identity(rows).values())
