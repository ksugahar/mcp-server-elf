from copy import deepcopy

from elf_mcp_server.v52_identity import LINEAR_SYSTEM, SURFACE, validate_source_v52_identity


PROMOTED_CASE_IDS = {
    "v52_source_tool_matrix_preconditioner_ordering_tolerance_residual_owner_mismatch",
    "v52_source_tool_surface_component_closedness_genus_orientation_owner_mismatch",
}


def _generations(generation: str, fields: tuple[str, ...]) -> dict[str, str]:
    return {"generation": generation, **{field: generation for field in fields}}


def _identities() -> list[dict[str, object]]:
    result = {"result_sha256": "f" * 64, "accepted_result_sha256": "f" * 64}
    residuals = [1.0, 0.08, 0.003, 1.0e-5, 4.0e-11]
    identity = {
        LINEAR_SYSTEM: {
            **_generations("linear-system-v52", ("preconditioner_generation", "ordering_generation", "tolerance_generation", "residual_generation", "owner_generation", "result_generation")),
            "preconditioner": "ilu0", "replayed_preconditioner": "ilu0",
            "matrix_ordering": "reverse_cuthill_mckee", "replayed_matrix_ordering": "reverse_cuthill_mckee",
            "relative_tolerance": 1.0e-10, "replayed_relative_tolerance": 1.0e-10,
            "residual_history": residuals, "replayed_residual_history": residuals,
            "matrix_owner": "matrix:linear-system-v52", "replayed_matrix_owner": "matrix:linear-system-v52", **result,
        },
        SURFACE: {
            **_generations("surface-v52", ("component_generation", "closedness_generation", "genus_generation", "orientation_generation", "owner_generation", "result_generation")),
            "component_count": 2, "replayed_component_count": 2,
            "component_closedness": [True, True], "replayed_component_closedness": [True, True],
            "component_genus": [0, 1], "replayed_component_genus": [0, 1],
            "component_orientation": ["outward", "outward"], "replayed_component_orientation": ["outward", "outward"],
            "mesh_owner": "mesh:surface-v52", "replayed_mesh_owner": "mesh:surface-v52", **result,
        },
    }
    return [deepcopy(identity), deepcopy(identity)]


def test_v52_positive_source_artifacts_are_accepted() -> None:
    assert all(validate_source_v52_identity(_identities()).values())


def test_v52_frozen_counterfactuals_are_rejected() -> None:
    identities = _identities()
    identities[0][LINEAR_SYSTEM]["replayed_residual_history"] = [1.0, 2.0]
    identities[0][SURFACE]["replayed_component_orientation"] = ["inward", "outward"]
    assert not all(validate_source_v52_identity(identities).values())


def test_v52_self_consistent_invalid_source_semantics_are_rejected() -> None:
    identities = _identities()
    for identity in identities:
        identity[LINEAR_SYSTEM]["residual_history"] = identity[LINEAR_SYSTEM]["replayed_residual_history"] = [1.0, 2.0]
        identity[SURFACE]["component_closedness"] = identity[SURFACE]["replayed_component_closedness"] = [False, True]
    assert not all(validate_source_v52_identity(identities).values())
