from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v40 import _summary_v40


_NONLINEAR = "nonlinear_bh_iteration_relaxation_residual_branch_convergence_material_analysis_result_identity"
_MESH = "mesh_region_material_element_orientation_boundary_face_model_owner_result_identity"
_PROMOTED_CASE_IDS = (
    "v41_source_nonlinear_bh_iteration_relaxation_residual_branch_convergence_owner_mismatch",
    "v41_source_mesh_region_material_elementorientation_boundaryface_model_owner_mismatch",
)


def _summary_v41() -> dict:
    summary = _summary_v40()
    for index, run in enumerate(summary["runs"]):
        generation = f"nonlinear-bh-{724 + index}"
        residuals = [1.0, 0.2, 0.05, 0.01, 1.0e-3]
        values = {
            "bh_branch": "ascending",
            "relaxation_factor": 0.7,
            "residual_history": residuals,
            "iteration_count": len(residuals) - 1,
            "relative_tolerance": 2.0e-3,
            "converged": True,
            "material_owner": "material:nonlinear-bh-724",
            "analysis_owner": "analysis:nonlinear-bh-724",
        }
        run[_NONLINEAR] = {
            "nonlinear_generation": generation,
            **{key: generation for key in ("material_generation", "branch_generation", "iteration_generation", "relaxation_generation", "residual_generation", "convergence_generation", "owner_generation", "result_generation")},
            **values,
            **{f"resolved_{key}": value for key, value in values.items()},
            "nonlinear_result_sha256": "7" * 64,
            "accepted_nonlinear_result_sha256": "7" * 64,
        }

        generation = f"mesh-region-material-{724 + index}"
        values = {
            "region_ids": ["core", "air"],
            "region_material_map": {"core": "steel", "air": "air"},
            "element_orientation": {"core": [1.0, 0.0, 0.0], "air": [0.0, 0.0, 1.0]},
            "boundary_face_sets": {"outer": [1, 2, 3, 4], "interface": [5, 6]},
            "element_count": 128,
            "mesh_owner": "mesh:region-material-724",
            "model_owner": "model:region-material-724",
        }
        run[_MESH] = {
            "mesh_region_generation": generation,
            **{key: generation for key in ("region_generation", "material_generation", "orientation_generation", "boundary_generation", "element_generation", "mesh_generation", "model_generation", "result_generation")},
            **values,
            **{f"resolved_{key}": value for key, value in values.items()},
            "mesh_region_result_sha256": "8" * 64,
            "accepted_mesh_region_result_sha256": "8" * 64,
        }
    return summary


def test_v41_source_positive_nonlinear_and_mesh_replay() -> None:
    assert _gate(_summary_v41())["status"] == "ok"


def test_v41_source_nonlinear_bh_iteration_relaxation_residual_branch_convergence_owner_mismatch() -> None:
    summary = _summary_v41()
    summary["runs"][0][_NONLINEAR].update({"iteration_generation": "nonlinear-bh-723", "resolved_bh_branch": "descending", "resolved_relaxation_factor": 1.5, "resolved_residual_history": [1.0, 2.0], "resolved_material_owner": "stale:material"})
    assert _gate(summary)["status"] == "needs_attention"


def test_v41_source_mesh_region_material_elementorientation_boundaryface_model_owner_mismatch() -> None:
    summary = _summary_v41()
    summary["runs"][0][_MESH].update({"material_generation": "mesh-region-material-723", "resolved_region_ids": ["core"], "resolved_region_material_map": {"core": "air"}, "resolved_element_orientation": {"core": [0.0, 0.0, 0.0]}, "resolved_model_owner": "stale:model"})
    assert _gate(summary)["status"] == "needs_attention"


def test_v41_source_rejects_self_consistent_nonlinear_residual_growth() -> None:
    summary = _summary_v41()
    for run in summary["runs"]:
        row = run[_NONLINEAR]
        row["residual_history"] = row["resolved_residual_history"] = [1.0, 0.2, 0.3, 1.0e-3]
        row["iteration_count"] = row["resolved_iteration_count"] = 3
    assert _gate(summary)["status"] == "needs_attention"


def test_v41_source_rejects_self_consistent_duplicate_boundary_faces() -> None:
    summary = _summary_v41()
    for run in summary["runs"]:
        row = run[_MESH]
        row["boundary_face_sets"] = row["resolved_boundary_face_sets"] = {"outer": [1, 2], "interface": [2, 3]}
    assert _gate(summary)["status"] == "needs_attention"
