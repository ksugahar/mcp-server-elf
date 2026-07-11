import json

from elf_mcp_server.demagnetization_run_contract import demagnetization_run_contract_gate
from elf_mcp_server.server import elf_demagnetization_run_contract_gate


def _summary():
    case = {
        "case_id": "history-a",
        "solver_exit_code": 0,
        "dmeg_enabled": True,
        "maximum_nonlinear_iterations": 100,
        "nonlinear_tolerance": 0.01,
        "maximum_final_convergence": 0.009,
        "expected_step_count": 3,
        "observed_step_count": 3,
        "end_of_moment_solution": True,
        "error_marker_count": 0,
        "output_roles": {
            ".mao": "run_log",
            ".mag": "field_result",
            ".mat": "matrix_state",
            ".mac": "mark_state",
        },
        "all_outputs_fresh": True,
        "state_min_history": [0.95, 0.74, 0.74],
    }
    return {
        "execution_route": "direct_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_family": "magnetostatic_bem",
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-11T00:00:00Z",
        "source_copy_preserved": True,
        "expected_case_count": 1,
        "cases": [case],
    }


def test_demagnetization_contract_accepts_fresh_converged_history():
    result = demagnetization_run_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(elf_demagnetization_run_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_demagnetization_contract_rejects_stale_or_incomplete_outputs():
    summary = _summary()
    summary["cases"][0]["all_outputs_fresh"] = False
    summary["cases"][0]["output_roles"].pop(".mao")
    result = demagnetization_run_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["all_case_contracts_pass"] is False


def test_demagnetization_contract_rejects_false_convergence_and_recovery():
    summary = _summary()
    summary["cases"][0]["maximum_final_convergence"] = 0.02
    summary["cases"][0]["state_min_history"][-1] = 0.95
    result = demagnetization_run_contract_gate(json.dumps(summary))
    checks = result["case_checks"]["history-a"]
    assert result["status"] == "needs_attention"
    assert checks["all_steps_converged"] is False
    assert checks["state_does_not_recover"] is False
