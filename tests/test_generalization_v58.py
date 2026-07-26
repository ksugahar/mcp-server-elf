import math
from copy import deepcopy

from elf_mcp_server.v58_identity import MESH, NONLINEAR, validate_source_v58_identity


CASE_IDS = {
    "v58_source_tool_bem_duplicatepanel_nonmanifold_normal_solidangle_meshowner_mismatch",
    "v58_source_tool_nonlinear_bh_relaxation_residual_iteration_material_owner_mismatch",
}


def _fields(generation: str, names: tuple[str, ...]) -> dict[str, str]:
    return {"generation": generation, **{name: generation for name in names}}


def _identities() -> list[dict[str, object]]:
    generation = "elf-source-v58-test"
    incidence = {"boundary": 0, "manifold": 6, "nonmanifold": 0}
    b_values = [0.0, 0.5, 1.0, 1.2]
    h_values = [0.0, 100.0, 300.0, 1000.0]
    residuals = [1.0e-2, 3.0e-3, 8.0e-4, 2.0e-4]
    identity = {
        MESH: {
            **_fields(generation, ("panel_generation", "edge_generation", "normal_generation", "angle_generation", "owner_generation", "result_generation")),
            "panel_count": 4, "replayed_panel_count": 4,
            "unique_panel_count": 4, "replayed_unique_panel_count": 4,
            "duplicate_panel_count": 0, "replayed_duplicate_panel_count": 0,
            "edge_incidence": incidence, "replayed_edge_incidence": incidence,
            "normal_orientation": "outward", "replayed_normal_orientation": "outward",
            "minimum_normal_centroid_dot": 0.25, "replayed_minimum_normal_centroid_dot": 0.25,
            "solid_angle_sum_sr": 4.0 * math.pi, "replayed_solid_angle_sum_sr": 4.0 * math.pi,
            "mesh_revision": "mesh:tetra-surface-v58-r3", "replayed_mesh_revision": "mesh:tetra-surface-v58-r3",
            "mesh_owner": "mesh-owner:bem-v58", "replayed_mesh_owner": "mesh-owner:bem-v58",
            "result_sha256": "8" * 64, "accepted_result_sha256": "8" * 64,
        },
        NONLINEAR: {
            **_fields(generation, ("bh_generation", "relaxation_generation", "residual_generation", "iteration_generation", "material_generation", "owner_generation", "result_generation")),
            "b_t": b_values, "replayed_b_t": b_values,
            "h_a_m": h_values, "replayed_h_a_m": h_values,
            "operating_point": {"b_t": 1.0, "h_a_m": 300.0}, "replayed_operating_point": {"b_t": 1.0, "h_a_m": 300.0},
            "relaxation_factor": 0.5, "replayed_relaxation_factor": 0.5,
            "residual_history": residuals, "replayed_residual_history": residuals,
            "residual_tolerance": 1.0e-3, "replayed_residual_tolerance": 1.0e-3,
            "iteration_count": 4, "replayed_iteration_count": 4,
            "converged": True, "replayed_converged": True,
            "material_revision": "material:nonlinear-v58-r6", "replayed_material_revision": "material:nonlinear-v58-r6",
            "result_owner": "result:nonlinear-v58", "replayed_result_owner": "result:nonlinear-v58",
            "result_sha256": "9" * 64, "accepted_result_sha256": "9" * 64,
        },
    }
    return [deepcopy(identity), deepcopy(identity)]


def test_v58_positive_identity_is_accepted() -> None:
    assert all(validate_source_v58_identity(_identities()).values())


def test_v58_frozen_replay_mutations_are_rejected() -> None:
    identities = _identities()
    identities[0][MESH].update(replayed_duplicate_panel_count=2, replayed_mesh_owner="mesh-owner:stale")
    identities[0][NONLINEAR].update(replayed_relaxation_factor=1.5, replayed_result_owner="result:stale")
    assert not all(validate_source_v58_identity(identities).values())


def test_v58_self_consistent_physics_contradictions_are_rejected() -> None:
    identities = _identities()
    for identity in identities:
        identity[MESH]["edge_incidence"] = identity[MESH]["replayed_edge_incidence"] = {"boundary": 1, "manifold": 5, "nonmanifold": 0}
        identity[NONLINEAR]["residual_history"] = identity[NONLINEAR]["replayed_residual_history"] = [1.0e-2, 2.0e-2, 1.0e-4, 2.0e-4]
    assert not all(validate_source_v58_identity(identities).values())


def test_v58_malformed_series_rejects_without_raising() -> None:
    identities = _identities()
    identities[0][MESH]["edge_incidence"] = []
    identities[1][NONLINEAR]["b_t"] = [0.0, "one"]
    assert not all(validate_source_v58_identity(identities).values())
