from __future__ import annotations

from elf_mcp_server.v44_identity import validate_source_identity


def _identities():
    generation = "test-846"
    return [{
        "v46_source_tool_licensed_session_attach_timeout_partial_mao_column_mismatch": {
            "generation": generation,
            **{key: generation for key in ("session_generation", "timeout_generation", "partial_generation", "column_generation", "result_generation")},
            "session_attached": True, "result_session_attached": True, "session_identity": "session:test", "result_session_identity": "session:test", "timeout_s": 120.0, "result_timeout_s": 120.0,
            "partial_result": False, "result_partial_result": False, "result_authority": ".mao", "result_result_authority": ".mao", "column_order": ["time_s", "force_n", "torque_nm", "power_w"], "result_column_order": ["time_s", "force_n", "torque_nm", "power_w"],
            "result_owner": "result:test", "result_result_owner": "result:test", "result_sha256": "a" * 64, "accepted_result_sha256": "a" * 64,
        },
        "v46_source_tool_virtual_work_displacement_unit_scale_coordinate_frame_nonfinite_mismatch": {
            "generation": generation,
            **{key: generation for key in ("displacement_generation", "unit_scale_generation", "frame_generation", "finite_generation", "convergence_generation", "result_generation")},
            "displacement_unit": "m", "result_displacement_unit": "m", "displacement_unit_scale_to_si": 1.0, "result_displacement_unit_scale_to_si": 1.0, "coordinate_frame": "global_cartesian", "result_coordinate_frame": "global_cartesian", "nonfinite_value_count": 0, "result_nonfinite_value_count": 0, "converged": True, "result_converged": True, "displacement_direction": [1.0, 0.0, 0.0], "result_displacement_direction": [1.0, 0.0, 0.0],
            "result_owner": "result:test", "result_result_owner": "result:test", "result_sha256": "b" * 64, "accepted_result_sha256": "b" * 64,
        },
    }]


def test_v46_source_identity_accepts_closed_replay():
    checks = validate_source_identity(_identities())
    assert checks and all(checks.values())


def test_v46_source_identity_rejects_stale_mao_and_nonfinite_replay():
    identities = _identities()
    identities[0]["v46_source_tool_licensed_session_attach_timeout_partial_mao_column_mismatch"]["result_authority"] = ".mag"
    identities[0]["v46_source_tool_virtual_work_displacement_unit_scale_coordinate_frame_nonfinite_mismatch"]["result_nonfinite_value_count"] = 1
    checks = validate_source_identity(identities)
    assert checks and not all(checks.values())
