import copy
import json

from elf_mcp_server.server import elf_source_off_relaxation_contract_gate
from elf_mcp_server.source_off_relaxation_contract import (
    source_off_relaxation_contract_gate,
)


def _summary():
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "working_directory_contains_input_pair": True,
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-12T00:00:00Z",
        "source_copy_preserved": True,
        "transient_run": {
            "source_digests": {"control": "a" * 64, "mesh": "b" * 64},
            "mesh_exit_code": 0,
            "solver_exit_code": 0,
            "drive_mode": "voltage",
            "feature_headers": ["COI1_V", "VOL1", "OHM1", "EMFM", "TIME"],
            "material_response": "linear",
            "source_schedule": "initial_voltage_then_zero",
            "emfm_semantics": "induced_current",
            "total_current_derivation": "voltage_over_resistance_plus_induced_current",
            "expected_step_count": 3,
            "observed_step_count": 3,
            "emfm_record_count": 3,
            "end_of_moment_solution": True,
            "error_marker_count": 0,
            "output_roles": {
                ".mao": "run_log",
                ".mag": "field_result",
                ".mat": "matrix_state",
                ".mac": "mark_state",
            },
            "all_outputs_fresh": True,
        },
        "static_companion": {
            "role": "nonlinear_current_driven_classification_only",
            "material_response": "nonlinear",
            "numerical_cross_comparison": False,
            "mesh_exit_code": 0,
            "solver_exit_code": 0,
            "source_digests": {"control": "c" * 64, "mesh": "d" * 64},
        },
        "public_gate": {
            "schema": "radia-source-off-linear-relaxation/v1",
            "status": "ok",
            "input_digest": "e" * 64,
        },
    }


def test_source_off_contract_accepts_fresh_direct_run_and_dispatches():
    result = source_off_relaxation_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert all(result["checks"].values())
    dispatched = json.loads(elf_source_off_relaxation_contract_gate(json.dumps(_summary())))
    assert dispatched["status"] == "ok"


def test_source_off_contract_rejects_wrong_cwd_and_induced_only_derivation():
    bad = copy.deepcopy(_summary())
    bad["working_directory_contains_input_pair"] = False
    bad["transient_run"]["total_current_derivation"] = "induced_current_only"
    bad["transient_run"]["all_outputs_fresh"] = False
    result = source_off_relaxation_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["case_working_directory_contains_input_pair"] is False
    assert result["checks"]["total_current_derivation_recorded"] is False
    assert result["checks"]["output_roles_complete_and_fresh"] is False


def test_source_off_contract_rejects_false_static_cross_comparison():
    bad = _summary()
    bad["static_companion"]["numerical_cross_comparison"] = True
    result = source_off_relaxation_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["static_companion_is_classification_only"] is False
