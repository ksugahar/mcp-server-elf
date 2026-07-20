from copy import deepcopy
import math

from elf_mcp_server.v57_identity import MULTIPOLE, SINGULAR, validate_source_v57_identity


CASE_IDS = {
    "v57_source_tool_bem_singularquadrature_panelorientation_solidangle_collocation_owner_mismatch",
    "v57_source_tool_multipole_tree_order_translation_error_blockowner_mismatch",
}


def _identities() -> list[dict[str, object]]:
    generation = "elf-source-v57-test"
    fields = lambda names: {name: generation for name in names}
    ownership = {"block:0": "rank:0", "block:1": "rank:1", "block:2": "rank:1"}
    row = {
        SINGULAR: {"generation": generation, **fields(("quadrature_generation", "orientation_generation", "angle_generation", "collocation_generation", "owner_generation", "result_generation")), "singular_quadrature": "duffy", "replayed_singular_quadrature": "duffy", "quadrature_order": 8, "replayed_quadrature_order": 8, "panel_orientation": "outward", "replayed_panel_orientation": "outward", "solid_angle_sr": 2.0 * math.pi, "replayed_solid_angle_sr": 2.0 * math.pi, "collocation_identity": "collocation:panel-42", "replayed_collocation_identity": "collocation:panel-42", "panel_owner": "panel-owner:surface-v57", "replayed_panel_owner": "panel-owner:surface-v57", "result_sha256": "4" * 64, "accepted_result_sha256": "4" * 64},
        MULTIPOLE: {"generation": generation, **fields(("tree_generation", "order_generation", "translation_generation", "error_generation", "block_generation", "owner_generation", "result_generation")), "tree_depth": 4, "replayed_tree_depth": 4, "multipole_order": 6, "replayed_multipole_order": 6, "translation_operator": "m2l", "replayed_translation_operator": "m2l", "relative_error_estimate": 1.0e-6, "replayed_relative_error_estimate": 1.0e-6, "relative_error_tolerance": 1.0e-5, "replayed_relative_error_tolerance": 1.0e-5, "block_ownership": ownership, "replayed_block_ownership": ownership, "result_owner": "result:multipole-v57", "replayed_result_owner": "result:multipole-v57", "result_sha256": "5" * 64, "accepted_result_sha256": "5" * 64},
    }
    return [deepcopy(row), deepcopy(row)]


def test_v57_positive_identity_is_accepted() -> None:
    assert all(validate_source_v57_identity(_identities()).values())


def test_v57_frozen_replay_mutations_are_rejected() -> None:
    rows = _identities()
    rows[0][SINGULAR]["replayed_panel_orientation"] = "inward"
    rows[0][MULTIPOLE]["replayed_translation_operator"] = "p2m"
    assert not all(validate_source_v57_identity(rows).values())


def test_v57_self_consistent_physics_contradictions_are_rejected() -> None:
    rows = _identities()
    rows[0][SINGULAR]["solid_angle_sr"] = rows[0][SINGULAR]["replayed_solid_angle_sr"] = 4.0 * math.pi
    rows[0][MULTIPOLE]["relative_error_estimate"] = rows[0][MULTIPOLE]["replayed_relative_error_estimate"] = 1.0
    assert not all(validate_source_v57_identity(rows).values())


def test_v57_malformed_ownership_rejects_without_raising() -> None:
    rows = _identities()
    rows[0][MULTIPOLE]["block_ownership"] = []
    assert not all(validate_source_v57_identity(rows).values())
