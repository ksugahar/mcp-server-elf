import json

from elf_mcp_server.server import elf_transient_induced_current_contract_gate
from elf_mcp_server.transient_induced_current_contract import transient_induced_current_contract_gate


def _summary():
    return {
        "execution_route": "direct_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-11T00:00:00Z",
        "source_copy_preserved": True,
        "emfm_semantics": "induced_current",
        "compatibility_probe": {
            "emgo_enabled": False,
            "solver_exit_code": 13,
            "reason": "current_driven_emfm_requires_emgo",
        },
        "successful_run": {
            "solver_exit_code": 0,
            "emgo_enabled": True,
            "current_driven_secondary": True,
            "observed_step_count": 21,
            "expected_step_count": 21,
            "time_step_s": 0.001,
            "uniform_time_grid": True,
            "zero_initial_primary_current": True,
            "zero_initial_secondary_current": True,
            "secondary_resistance_ohm": 0.4,
            "secondary_turns": 80,
            "memory_factor": 0.8,
            "coupling_gain": -0.3,
            "maximum_relative_residual": 1.0e-6,
            "relative_residual_tolerance": 1.0e-3,
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
    }


def test_transient_induced_current_contract_accepts_compatible_fresh_run():
    result = transient_induced_current_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(elf_transient_induced_current_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_transient_induced_current_contract_rejects_force_mislabel_and_missing_override():
    summary = _summary()
    summary["emfm_semantics"] = "electromagnetic_force"
    summary["successful_run"]["emgo_enabled"] = False
    summary["successful_run"]["all_outputs_fresh"] = False
    result = transient_induced_current_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["emfm_means_induced_current"] is False
    assert result["checks"]["emgo_enabled_for_current_drive"] is False
    assert result["checks"]["all_outputs_fresh"] is False
