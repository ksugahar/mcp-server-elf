from __future__ import annotations

from elf_mcp_server.v44_identity import validate_source_identity


_TABLE = "mao_result_table_release_units_column_order_model_owner_digest_identity"
_FORCE = "mao_force_virtualwork_displacement_energyfit_reference_owner_identity"
_PROMOTED_CASE_IDS = (
    "v44_source_mao_result_table_release_units_column_order_model_owner_digest_mismatch",
    "v44_source_force_virtualwork_displacement_direction_energyfit_reference_owner_mismatch",
)


def _rows() -> list[dict]:
    rows = []
    for index in range(2):
        table = f"mao-table-844-{index}"
        force = f"mao-force-844-{index}"
        rows.append({
            _TABLE: {
                "mao_table_generation": table,
                **{key: table for key in ("release_generation", "units_generation", "column_order_generation", "model_generation", "owner_generation", "result_generation")},
                "release": "product-release-844", "result_release": "product-release-844",
                "units": {"force": "N", "torque": "N*m", "power": "W"}, "result_units": {"force": "N", "torque": "N*m", "power": "W"},
                "column_order": ["time_s", "force_n", "torque_nm", "power_w"], "result_column_order": ["time_s", "force_n", "torque_nm", "power_w"],
                "model_owner": f"model:{table}", "result_model_owner": f"model:{table}",
                "result_owner": f"result:{table}", "result_result_owner": f"result:{table}",
                "mao_result_sha256": "b" * 64, "accepted_mao_result_sha256": "b" * 64,
            },
            _FORCE: {
                "mao_force_generation": force,
                **{key: force for key in ("displacement_generation", "direction_generation", "energyfit_generation", "reference_generation", "convergence_generation", "result_generation", "owner_generation")},
                "displacement_direction": [1.0, 0.0, 0.0], "result_displacement_direction": [1.0, 0.0, 0.0],
                "displacement_steps_m": [1.0e-4, 2.0e-4, 4.0e-4], "result_displacement_steps_m": [1.0e-4, 2.0e-4, 4.0e-4],
                "energy_samples_j": [1.0, 1.1, 1.2], "result_energy_samples_j": [1.0, 1.1, 1.2],
                "energy_fit_order": 2, "result_energy_fit_order": 2,
                "force_n": 100.0, "result_force_n": 100.0,
                "reference_geometry": f"geometry:{force}", "result_reference_geometry": f"geometry:{force}",
                "result_owner": f"result:{force}", "result_result_owner": f"result:{force}",
                "mao_force_result_sha256": "c" * 64, "accepted_mao_force_result_sha256": "c" * 64,
            },
        })
    return rows


def test_v44_source_table_and_virtualwork_identity_positive() -> None:
    result = validate_source_identity(_rows())
    assert result == {
        "source_v44_mao_table_release_units_identity": True,
        "source_v44_virtualwork_force_identity": True,
    }


def test_v44_source_identity_rejects_units_and_direction_mutations() -> None:
    rows = _rows()
    rows[0][_TABLE]["result_units"] = {"force": "kN", "torque": "N*m", "power": "W"}
    rows[0][_FORCE]["result_displacement_direction"] = [0.0, 1.0, 0.0]
    result = validate_source_identity(rows)
    assert result["source_v44_mao_table_release_units_identity"] is False
    assert result["source_v44_virtualwork_force_identity"] is False
