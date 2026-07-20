from copy import deepcopy
import math

from elf_mcp_server.v56_identity import MESH, SOLVER, validate_source_v56_identity

CASE_IDS = {"v56_source_tool_bem_closedmesh_solidangle_orientation_region_owner_mismatch", "v56_source_tool_solver_residual_tolerance_iteration_matrixrevision_owner_mismatch"}


def _identities() -> list[dict[str, object]]:
    generation = "elf-source-v56-test"; generations = lambda fields: {field: generation for field in fields}
    regions = {"inside": "region:magnet", "outside": "region:vacuum"}; residuals = [1.0, 0.12, 0.014, 8.0e-4, 4.0e-7]
    row = {
        MESH: {"generation": generation, **generations(("closure_generation", "angle_generation", "orientation_generation", "region_generation", "owner_generation", "result_generation")), "closed_surface": True, "replayed_closed_surface": True, "solid_angle_sr": 4.0 * math.pi, "replayed_solid_angle_sr": 4.0 * math.pi, "panel_orientation": "outward", "replayed_panel_orientation": "outward", "region_assignment": regions, "replayed_region_assignment": regions, "mesh_owner": "mesh:bem-v56", "replayed_mesh_owner": "mesh:bem-v56", "result_sha256": "f" * 64, "accepted_result_sha256": "f" * 64},
        SOLVER: {"generation": generation, **generations(("residual_generation", "tolerance_generation", "iteration_generation", "matrix_generation", "owner_generation", "result_generation")), "residual_history": residuals, "replayed_residual_history": residuals, "relative_tolerance": 1.0e-6, "replayed_relative_tolerance": 1.0e-6, "iteration_count": len(residuals) - 1, "replayed_iteration_count": len(residuals) - 1, "matrix_revision": "matrix:v56-r9", "replayed_matrix_revision": "matrix:v56-r9", "run_owner": "run:solver-v56", "replayed_run_owner": "run:solver-v56", "result_sha256": "1" * 64, "accepted_result_sha256": "1" * 64},
    }
    return [deepcopy(row), deepcopy(row)]


def test_v56_positive_identity_is_accepted() -> None:
    assert all(validate_source_v56_identity(_identities()).values())


def test_v56_frozen_replay_mutations_are_rejected() -> None:
    rows = _identities(); rows[0][MESH]["replayed_closed_surface"] = False; rows[0][SOLVER]["replayed_iteration_count"] = 99
    assert not all(validate_source_v56_identity(rows).values())


def test_v56_self_consistent_mesh_and_solver_errors_are_rejected() -> None:
    rows = _identities(); rows[0][MESH]["solid_angle_sr"] = rows[0][MESH]["replayed_solid_angle_sr"] = 2.0 * math.pi; bad = [1.0, 2.0]; rows[0][SOLVER]["residual_history"] = rows[0][SOLVER]["replayed_residual_history"] = bad
    assert not all(validate_source_v56_identity(rows).values())


def test_v56_malformed_residuals_reject_without_raising() -> None:
    rows = _identities(); rows[0][SOLVER]["residual_history"] = [[1.0]]
    assert not all(validate_source_v56_identity(rows).values())
