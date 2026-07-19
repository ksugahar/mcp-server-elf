from __future__ import annotations

from elf_mcp_server.v44_identity import validate_source_identity


_PROMOTED_CASE_IDS = (
    "v45_source_mao_result_release_units_column_order_model_generation_owner_digest_mismatch",
    "v45_source_virtual_work_displacement_direction_energy_fit_reference_geometry_owner_mismatch",
)


def _identity():
    generation = "test-845"
    return [{
        "v45_source_mao_result_release_units_column_order_model_generation_owner_digest_mismatch": {
            "generation": generation, **{key: generation for key in ("release_generation", "units_generation", "column_order_generation", "model_generation", "owner_generation", "result_generation")}, "release": "product-release-845", "result_release": "product-release-845", "units": {"force": "N", "torque": "N*m", "power": "W"}, "result_units": {"force": "N", "torque": "N*m", "power": "W"}, "column_order": ["time_s", "force_n", "torque_nm", "power_w"], "result_column_order": ["time_s", "force_n", "torque_nm", "power_w"], "model_owner": "model:test", "result_model_owner": "model:test", "result_owner": "result:test", "result_result_owner": "result:test", "result_sha256": "a" * 64, "accepted_result_sha256": "a" * 64,
        },
        "v45_source_virtual_work_displacement_direction_energy_fit_reference_geometry_owner_mismatch": {
            "generation": generation, **{key: generation for key in ("displacement_generation", "direction_generation", "energy_fit_generation", "reference_geometry_generation", "convergence_generation", "result_generation", "owner_generation")}, "displacement_direction": [1.0, 0.0, 0.0], "result_displacement_direction": [1.0, 0.0, 0.0], "displacement_steps_m": [1e-4, 2e-4, 4e-4], "result_displacement_steps_m": [1e-4, 2e-4, 4e-4], "energy_samples_j": [1.0, 1.1, 1.2], "result_energy_samples_j": [1.0, 1.1, 1.2], "energy_fit_order": 2, "result_energy_fit_order": 2, "force_n": 100.0, "result_force_n": 100.0, "reference_geometry": "geometry:test", "result_reference_geometry": "geometry:test", "result_owner": "result:test", "result_result_owner": "result:test", "result_sha256": "b" * 64, "accepted_result_sha256": "b" * 64,
        },
    }]


def test_v45_elf_source_identity_accepts_closed_replay():
    checks = validate_source_identity(_identity())
    assert checks and all(checks.values())


def test_v45_elf_source_identity_rejects_units_mutation():
    identity = _identity()
    identity[0]["v45_source_mao_result_release_units_column_order_model_generation_owner_digest_mismatch"]["result_units"] = {"force": "kN", "torque": "N*m", "power": "W"}
    checks = validate_source_identity(identity)
    assert checks and not all(checks.values())
