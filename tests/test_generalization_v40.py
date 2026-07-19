from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v39 import _summary_v39


_SOLVER = "solver_matrix_reorder_preconditioner_iteration_residual_convergence_analysis_resultfile_identity"
_SYMMETRY = "symmetry_plane_location_normal_parity_sign_region_boundary_mesh_model_result_identity"
_PROMOTED_CASE_IDS = (
    "v40_source_solver_matrix_reorder_preconditioner_iteration_residual_result_owner_mismatch",
    "v40_source_symmetry_plane_boundary_sign_normal_region_mapping_model_owner_mismatch",
)


def _summary_v40() -> dict:
    summary = _summary_v39()
    for index, run in enumerate(summary["runs"]):
        generation = f"solver-matrix-{280 + index}"
        values = {
            "matrix_shape": [1200, 1200], "matrix_nnz": 18300,
            "reordering": "amd", "preconditioner": "ilu0",
            "iteration_count": 4,
            "residual_history": [1.0, 0.1, 0.01, 1.0e-4, 1.0e-8],
            "relative_tolerance": 1.0e-7, "converged": True,
            "analysis_owner": "analysis:solver-matrix-280",
            "result_file_owner": "result-file:solver-matrix-280",
        }
        run[_SOLVER] = {
            "solver_generation": generation,
            **{key: generation for key in ("matrix_generation", "reorder_generation", "preconditioner_generation", "iteration_generation", "residual_generation", "convergence_generation", "analysis_generation", "result_generation")},
            **values,
            **{f"resolved_{key}": value for key, value in values.items()},
            "solver_result_sha256": "3" * 64,
            "accepted_solver_result_sha256": "3" * 64,
        }

        generation = f"symmetry-plane-{280 + index}"
        values = {
            "plane_point_m": [0.0, 0.0, 0.0], "plane_normal": [1.0, 0.0, 0.0],
            "plane_offset_m": 0.0, "symmetry_parity": "even", "field_sign": 1,
            "paired_region_mapping": {"left_core": "right_core", "left_air": "right_air"},
            "boundary_assignment": ["symmetry_x0"],
            "mesh_owner": "mesh:symmetry-plane-280",
            "model_owner": "model:symmetry-plane-280",
        }
        run[_SYMMETRY] = {
            "symmetry_generation": generation,
            **{key: generation for key in ("plane_generation", "normal_generation", "parity_generation", "region_generation", "boundary_generation", "mesh_generation", "model_generation", "result_generation")},
            **values,
            **{f"resolved_{key}": value for key, value in values.items()},
            "symmetry_result_sha256": "4" * 64,
            "accepted_symmetry_result_sha256": "4" * 64,
        }
    return summary


def test_v40_source_positive_solver_and_symmetry_replay() -> None:
    assert _gate(_summary_v40())["status"] == "ok"


def test_v40_source_solver_matrix_reorder_preconditioner_iteration_residual_result_owner_mismatch() -> None:
    summary = _summary_v40()
    summary["runs"][0][_SOLVER].update({"matrix_generation": "solver-matrix-279", "resolved_matrix_shape": [100, 200], "resolved_reordering": "none", "resolved_residual_history": [1.0, 2.0], "resolved_converged": False, "resolved_analysis_owner": "stale:analysis"})
    assert _gate(summary)["status"] == "needs_attention"


def test_v40_source_symmetry_plane_boundary_sign_normal_region_mapping_model_owner_mismatch() -> None:
    summary = _summary_v40()
    summary["runs"][0][_SYMMETRY].update({"plane_generation": "symmetry-plane-279", "resolved_plane_normal": [0.0, 0.0, 0.0], "resolved_symmetry_parity": "odd", "resolved_field_sign": -1, "resolved_paired_region_mapping": {"left_core": "left_core"}, "resolved_model_owner": "stale:model"})
    assert _gate(summary)["status"] == "needs_attention"


def test_v40_source_rejects_self_consistent_nondecreasing_residual() -> None:
    summary = _summary_v40()
    for run in summary["runs"]:
        row = run[_SOLVER]
        row["residual_history"] = row["resolved_residual_history"] = [1.0, 0.1, 0.2, 1.0e-4, 1.0e-8]
    assert _gate(summary)["status"] == "needs_attention"


def test_v40_source_rejects_self_consistent_symmetry_self_mapping() -> None:
    summary = _summary_v40()
    for run in summary["runs"]:
        row = run[_SYMMETRY]
        row["paired_region_mapping"] = row["resolved_paired_region_mapping"] = {"left_core": "left_core"}
    assert _gate(summary)["status"] == "needs_attention"
