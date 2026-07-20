from copy import deepcopy

from elf_mcp_server.v51_identity import MULTIZONE, VECTOR, validate_source_v51_identity


PROMOTED_CASE_IDS = {
    "v51_source_tool_mao_multizone_timeblock_header_timestep_rowcount_result_owner_mismatch",
    "v51_source_tool_mao_vector_component_order_coordinate_frame_unit_result_owner_mismatch",
}


def _identities() -> list[dict[str, object]]:
    generation = "elf-source-v51"
    result = {"result_sha256": "f" * 64, "accepted_result_sha256": "f" * 64}
    zones = ["stator", "rotor"]
    times = [0.0, 0.001]
    headers = [{"zone": zone, "time_s": time} for time in times for zone in zones]
    counts = [{"zone": zone, "time_s": time, "rows": 64} for time in times for zone in zones]
    vectors = [[0.1, 0.2, 0.3], [0.2, 0.1, 0.4]]
    identity = {
        MULTIZONE: {
            "generation": generation, "zone_generation": generation, "header_generation": generation,
            "timestep_generation": generation, "rowcount_generation": generation, "owner_generation": generation,
            "result_generation": generation, "zone_names": zones, "replayed_zone_names": zones,
            "time_block_headers": headers, "replayed_time_block_headers": headers, "timesteps_s": times,
            "replayed_timesteps_s": times, "row_counts": counts, "replayed_row_counts": counts,
            "result_owner": "result:mao-multizone-v51", "replayed_result_owner": "result:mao-multizone-v51", **result,
        },
        VECTOR: {
            "generation": generation, "component_generation": generation, "frame_generation": generation,
            "unit_generation": generation, "value_generation": generation, "owner_generation": generation,
            "result_generation": generation, "component_order": ["x", "y", "z"],
            "replayed_component_order": ["x", "y", "z"], "coordinate_frame": "global_cartesian",
            "replayed_coordinate_frame": "global_cartesian", "vector_unit": "T", "replayed_vector_unit": "T",
            "vector_rows": vectors, "replayed_vector_rows": vectors, "result_owner": "result:mao-vector-v51",
            "replayed_result_owner": "result:mao-vector-v51", **result,
        },
    }
    return [deepcopy(identity), deepcopy(identity)]


def test_v51_positive_source_artifacts_are_accepted() -> None:
    assert all(validate_source_v51_identity(_identities()).values())


def test_v51_frozen_counterfactuals_are_rejected() -> None:
    identities = _identities()
    identities[0][MULTIZONE].update({"replayed_zone_names": ["zone0"], "replayed_result_owner": "result:stale"})
    identities[0][VECTOR].update({"replayed_component_order": ["z", "y", "x"], "replayed_vector_unit": "mT"})
    assert not all(validate_source_v51_identity(identities).values())


def test_v51_self_consistent_invalid_source_semantics_are_rejected() -> None:
    identities = _identities()
    for identity in identities:
        identity[VECTOR]["component_order"] = identity[VECTOR]["replayed_component_order"] = ["z", "y", "x"]
        identity[MULTIZONE]["timesteps_s"] = identity[MULTIZONE]["replayed_timesteps_s"] = [0.001, 0.0]
    assert not all(validate_source_v51_identity(identities).values())
