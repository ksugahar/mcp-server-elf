from copy import deepcopy

from elf_mcp_server.v53_identity import CURVE, SEAM, validate_source_v53_identity


PROMOTED_CASE_IDS = {
    "v53_source_tool_magnetization_curve_interpolation_extrapolation_branch_material_owner_mismatch",
    "v53_source_tool_cad_surface_seam_duplicate_panel_normal_mesh_owner_mismatch",
}


def _generations(generation: str, fields: tuple[str, ...]) -> dict[str, str]:
    return {"generation": generation, **{field: generation for field in fields}}


def _identity():
    points = [{"h_a_per_m": -900000.0, "b_t": 0.0}, {"h_a_per_m": -450000.0, "b_t": 0.62}, {"h_a_per_m": 0.0, "b_t": 1.18}]
    curve = {**_generations("curve-v53", ("point_generation", "interpolation_generation", "extrapolation_generation", "branch_generation", "owner_generation", "result_generation")), "curve_points": points, "replayed_curve_points": points, "interpolation": "monotone_cubic", "replayed_interpolation": "monotone_cubic", "extrapolation": "linear_recoil", "replayed_extrapolation": "linear_recoil", "branch_id": "branch:descending", "replayed_branch_id": "branch:descending", "material_owner": "material:v53", "replayed_material_owner": "material:v53", "result_sha256": "3" * 64, "accepted_result_sha256": "3" * 64}
    seams = [{"left_panel": 11, "right_panel": 12, "left_edge": 2, "right_edge": 1}]; normals = {"11": [0.0, 0.0, 1.0], "12": [0.0, 0.0, 1.0]}
    seam = {**_generations("seam-v53", ("seam_generation", "duplicate_generation", "normal_generation", "owner_generation", "result_generation")), "seam_pairs": seams, "replayed_seam_pairs": seams, "duplicate_panel_ids": [], "replayed_duplicate_panel_ids": [], "panel_normals": normals, "replayed_panel_normals": normals, "mesh_owner": "mesh:v53", "replayed_mesh_owner": "mesh:v53", "result_sha256": "4" * 64, "accepted_result_sha256": "4" * 64}
    return {CURVE: curve, SEAM: seam}


def _identities():
    return [deepcopy(_identity()), deepcopy(_identity())]


def test_v53_positive_source_artifacts_are_accepted():
    assert all(validate_source_v53_identity(_identities()).values())


def test_v53_frozen_counterfactuals_are_rejected():
    identities = _identities()
    identities[0][CURVE]["replayed_branch_id"] = "branch:stale"
    identities[0][SEAM]["replayed_duplicate_panel_ids"] = [12]
    assert not all(validate_source_v53_identity(identities).values())


def test_v53_self_consistent_invalid_semantics_are_rejected():
    identities = _identities()
    for identity in identities:
        identity[CURVE]["curve_points"][1]["b_t"] = identity[CURVE]["replayed_curve_points"][1]["b_t"] = -0.1
        identity[SEAM]["duplicate_panel_ids"] = identity[SEAM]["replayed_duplicate_panel_ids"] = [12]
    assert not all(validate_source_v53_identity(identities).values())
