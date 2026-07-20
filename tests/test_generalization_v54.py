from copy import deepcopy

from elf_mcp_server.v54_identity import NEAR, RESTART, validate_source_v54_identity


CASE_IDS = {
    "v54_source_tool_bem_nearsingular_quadrature_distance_panelorder_orientation_owner_mismatch",
    "v54_source_tool_nonlinear_restart_curvebranch_iteration_residual_checkpoint_owner_mismatch",
}


def _generations(generation: str, fields: tuple[str, ...]) -> dict[str, str]:
    return {"generation": generation, **{field: generation for field in fields}}


def _rows():
    interactions = [{"source_panel": 11, "target_panel": 12, "distance_over_size": 0.08, "distance_class": "near_singular", "quadrature_order": 8, "source_panel_order": 2, "target_panel_order": 2, "orientation": 1}]
    near = {**_generations("near-v54", ("distance_generation", "quadrature_generation", "panelorder_generation", "orientation_generation", "owner_generation", "result_generation")), "near_interactions": interactions, "replayed_near_interactions": interactions, "mesh_owner": "mesh:v54", "replayed_mesh_owner": "mesh:v54", "result_sha256": "3" * 64, "accepted_result_sha256": "3" * 64}
    residuals = [1.0, 0.2, 0.04, 0.008]; checkpoint = {"iteration": 3, "state_sha256": "a" * 64}
    restart = {**_generations("restart-v54", ("branch_generation", "iteration_generation", "residual_generation", "checkpoint_generation", "owner_generation", "result_generation")), "curve_branch": "branch:descending", "replayed_curve_branch": "branch:descending", "iteration_counter": 3, "replayed_iteration_counter": 3, "residual_history": residuals, "replayed_residual_history": residuals, "restart_checkpoint": checkpoint, "replayed_restart_checkpoint": checkpoint, "run_owner": "run:v54", "replayed_run_owner": "run:v54", "result_sha256": "4" * 64, "accepted_result_sha256": "4" * 64}
    return [{NEAR: near, RESTART: restart}]


def test_v54_positive_source_identities_are_accepted():
    assert all(validate_source_v54_identity(_rows()).values())


def test_v54_frozen_mutations_are_rejected():
    rows = deepcopy(_rows())
    rows[0][NEAR]["replayed_mesh_owner"] = "mesh:stale"
    rows[0][RESTART]["replayed_curve_branch"] = "branch:ascending"
    assert not all(validate_source_v54_identity(rows).values())


def test_v54_self_consistent_nonphysical_records_are_rejected():
    rows = deepcopy(_rows())
    bad_interactions = [{"source_panel": 11, "target_panel": 12, "distance_over_size": 0.08, "distance_class": "near_singular", "quadrature_order": 2, "source_panel_order": 2, "target_panel_order": 2, "orientation": -1}]
    rows[0][NEAR]["near_interactions"] = rows[0][NEAR]["replayed_near_interactions"] = bad_interactions
    rows[0][RESTART]["residual_history"] = rows[0][RESTART]["replayed_residual_history"] = [1.0, 2.0, 3.0, 4.0]
    assert not all(validate_source_v54_identity(rows).values())


def test_v54_malformed_values_reject_without_raising():
    rows = deepcopy(_rows())
    rows[0][NEAR]["near_interactions"] = [{"source_panel": [11], "target_panel": 12}]
    rows[0][RESTART]["restart_checkpoint"] = {"iteration": [3], "state_sha256": ["a"]}
    assert not all(validate_source_v54_identity(rows).values())
