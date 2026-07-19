from __future__ import annotations

import math

from test_generalization_v23 import _gate
from test_generalization_v41 import _summary_v41


_BEM = "bem_panel_normal_solidangle_singularquadrature_region_mesh_result_owner_identity"
_NONLINEAR = (
    "nonlinear_material_iteration_order_relaxation_residual_branch_convergence_"
    "result_owner_identity"
)
_PROMOTED_CASE_IDS = (
    "v42_source_bem_panel_normal_solidangle_singularquadrature_region_result_owner_mismatch",
    "v42_source_nonlinear_material_iteration_relaxation_residual_branch_result_owner_mismatch",
)
_SCALAR = "scalarpotential_gauge_body_topology_region_interface_normal_solution_owner_result_identity"
_VIRTUAL = "virtualdisplacement_force_step_convergence_reference_result_owner_identity"
_PROMOTED_V43_CASE_IDS = (
    "v43_source_scalarpotential_gauge_body_topology_region_interface_result_owner_mismatch",
    "v43_source_virtualdisplacement_force_step_convergence_reference_result_owner_mismatch",
)


def _summary_v42() -> dict:
    summary = _summary_v41()
    for index, run in enumerate(summary["runs"]):
        generation = f"bem-panel-842-{index}"
        values = {
            "panel_ids": [1, 2, 3, 4],
            "panel_normals": [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [-1.0 / math.sqrt(3.0)] * 3,
            ],
            "normal_orientation": "outward",
            "solid_angle_sum_sr": 4.0 * math.pi,
            "singular_quadrature_rule": "duffy_p1",
            "region_ids": [1, 1, 2, 2],
            "mesh_owner": "mesh:bem-panel-842",
            "result_owner": "result:bem-panel-842",
        }
        run[_BEM] = {
            "bem_panel_generation": generation,
            **{
                key: generation
                for key in (
                    "normal_generation", "solidangle_generation",
                    "quadrature_generation", "region_generation", "mesh_generation",
                    "owner_generation", "result_generation",
                )
            },
            **values,
            **{f"resolved_{key}": value for key, value in values.items()},
            "bem_panel_result_sha256": "3" * 64,
            "accepted_bem_panel_result_sha256": "3" * 64,
        }

        generation = f"nonlinear-material-842-{index}"
        values = {
            "iteration_order": [0, 1, 2, 3],
            "relaxation_factors": [0.6, 0.6, 0.5, 0.5],
            "residual_history": [1.0, 0.2, 0.04, 0.008],
            "constitutive_branches": ["initial", "ascending", "ascending", "ascending"],
            "relative_tolerance": 0.01,
            "converged": True,
            "result_owner": "result:nonlinear-material-842",
        }
        run[_NONLINEAR] = {
            "nonlinear_material_generation": generation,
            **{
                key: generation
                for key in (
                    "iteration_generation", "relaxation_generation",
                    "residual_generation", "branch_generation",
                    "convergence_generation", "owner_generation", "result_generation",
                )
            },
            **values,
            **{f"resolved_{key}": value for key, value in values.items()},
            "nonlinear_material_result_sha256": "4" * 64,
            "accepted_nonlinear_material_result_sha256": "4" * 64,
        }
    return summary


def test_v42_source_positive_bem_panel_and_nonlinear_replay() -> None:
    assert _gate(_summary_v42())["status"] == "ok"


def test_v42_source_bem_panel_mismatch() -> None:
    summary = _summary_v42()
    summary["runs"][0][_BEM].update(
        {
            "normal_generation": "bem-panel-841",
            "resolved_panel_normals": [[0.0, 0.0, 0.0]],
            "resolved_solid_angle_sum_sr": 2.0 * math.pi,
            "resolved_singular_quadrature_rule": "centroid",
            "resolved_result_owner": "stale:result",
        }
    )
    assert _gate(summary)["status"] == "needs_attention"


def test_v42_source_nonlinear_material_mismatch() -> None:
    summary = _summary_v42()
    summary["runs"][0][_NONLINEAR].update(
        {
            "iteration_generation": "nonlinear-material-841",
            "resolved_iteration_order": [0, 2, 1],
            "resolved_relaxation_factors": [1.5, -0.1, 0.5],
            "resolved_residual_history": [1.0, 2.0, 0.5],
            "resolved_result_owner": "stale:result",
        }
    )
    assert _gate(summary)["status"] == "needs_attention"


def test_v42_source_rejects_self_consistent_wrong_solid_angle() -> None:
    summary = _summary_v42()
    for run in summary["runs"]:
        row = run[_BEM]
        row["solid_angle_sum_sr"] = row["resolved_solid_angle_sum_sr"] = 2.0 * math.pi
    assert _gate(summary)["status"] == "needs_attention"


def test_v42_source_rejects_self_consistent_residual_growth() -> None:
    summary = _summary_v42()
    for run in summary["runs"]:
        row = run[_NONLINEAR]
        row["residual_history"] = row["resolved_residual_history"] = [1.0, 0.2, 0.3, 0.008]
    assert _gate(summary)["status"] == "needs_attention"


def _summary_v43() -> dict:
    summary = _summary_v42()
    for index, run in enumerate(summary["runs"]):
        generation = f"scalar-pot-843-{index}"
        run[_SCALAR] = {
            "scalarpotential_generation": generation,
            **{key: generation for key in ("gauge_generation", "topology_generation", "region_generation", "interface_generation", "normal_generation", "solution_generation", "owner_generation", "result_generation")},
            "gauge_reference": 0.0, "replayed_gauge_reference": 0.0,
            "body_topology_ids": [1, 2, 3], "replayed_body_topology_ids": [1, 2, 3],
            "region_interface": "air/steel", "replayed_region_interface": "air/steel",
            "normal_convention": "outward", "replayed_normal_convention": "outward",
            "solution_owner": f"solution:{generation}", "replayed_solution_owner": f"solution:{generation}",
            "model_owner": f"model:{generation}", "replayed_model_owner": f"model:{generation}",
            "scalarpotential_result_sha256": "7" * 64, "accepted_scalarpotential_result_sha256": "7" * 64,
        }
        generation = f"virtual-force-843-{index}"
        run[_VIRTUAL] = {
            "virtualdisplacement_generation": generation,
            **{key: generation for key in ("direction_generation", "step_generation", "energy_generation", "convergence_generation", "reference_generation", "solution_generation", "owner_generation", "result_generation")},
            "displacement_direction": [1.0, 0.0, 0.0], "replayed_displacement_direction": [1.0, 0.0, 0.0],
            "perturbation_steps_m": [1.0e-4, 2.0e-4, 4.0e-4], "replayed_perturbation_steps_m": [1.0e-4, 2.0e-4, 4.0e-4],
            "energy_samples_j": [1.0, 1.1, 1.2], "replayed_energy_samples_j": [1.0, 1.1, 1.2],
            "convergence_residuals": [0.1, 0.01, 0.001], "replayed_convergence_residuals": [0.1, 0.01, 0.001],
            "reference_geometry": f"geometry:{generation}", "replayed_reference_geometry": f"geometry:{generation}",
            "solution_owner": f"solution:{generation}", "replayed_solution_owner": f"solution:{generation}",
            "result_owner": f"result:{generation}", "replayed_result_owner": f"result:{generation}",
            "virtualdisplacement_result_sha256": "8" * 64, "accepted_virtualdisplacement_result_sha256": "8" * 64,
        }
    return summary


def test_v43_source_positive_scalar_potential_and_virtual_displacement() -> None:
    assert _gate(_summary_v43())["status"] == "ok"


def test_v43_source_scalar_potential_mismatch() -> None:
    summary = _summary_v43()
    summary["runs"][0][_SCALAR]["replayed_normal_convention"] = "inward"
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"]["scalar_potential_replays_preserve_gauge_topology_region_interface_normal_solution_owner_and_result"]


def test_v43_source_virtual_displacement_mismatch() -> None:
    summary = _summary_v43()
    summary["runs"][0][_VIRTUAL]["replayed_convergence_residuals"] = [0.1, 0.2, 0.3]
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"]["virtual_displacement_replays_preserve_direction_steps_energy_convergence_reference_solution_owner_and_result"]
