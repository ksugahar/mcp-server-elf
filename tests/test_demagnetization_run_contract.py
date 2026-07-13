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


def _history_family_summary():
    states = [
        {
            "state_id": "initial",
            "step": 0,
            "element_ids": [1, 2],
            "material_ids": [4, 4],
            "remanence_ratio": [1.0, 0.98],
            "flux_density_T": [0.52, 0.49],
        },
        {
            "state_id": "stress",
            "step": 1,
            "element_ids": [1, 2],
            "material_ids": [4, 4],
            "remanence_ratio": [0.82, 0.76],
            "flux_density_T": [0.31, 0.28],
        },
        {
            "state_id": "unloaded",
            "step": 2,
            "element_ids": [1, 2],
            "material_ids": [4, 4],
            "remanence_ratio": [0.82, 0.76],
            "flux_density_T": [0.44, 0.40],
        },
    ]

    def case(case_id):
        return {
            "case_id": case_id,
            "source_file_count": 2,
            "source_digest_count": 2,
            "source_copy_preserved": True,
            "solver_exit_codes": [0, 0],
            "source_commands": {
                "HBRM": [["1", "1.05", "1.2"]],
                "HBCN": [["4", "0", "1"], ["4", "1", "1"], ["4", "2", "1"]],
                "DMEG": [[]],
            },
            "states": [dict(state) for state in states],
            "history_blocks": [
                {
                    "pre_state": "initial",
                    "stress_state": "stress",
                    "unloaded_state": "unloaded",
                    "expect_additional_demagnetization": True,
                }
            ],
            "output_roles": {
                ".meg": "geometry_mesh",
                ".mao": "run_log_and_history_table",
                ".mag": "field_result",
                ".mat": "matrix_state",
                ".mac": "mark_state",
            },
            "all_outputs_fresh": True,
            "replay_count": 2,
            "replay_max_abs": 0.0,
        }

    cases = [case(case_id) for case_id in (
        "external_reverse_field_cycle",
        "coil_reverse_current_cycle",
        "temperature_curve_cycle",
        "precondition_then_temperature_cycle",
    )]
    return {
        "execution_route": "direct_solver_exe_no_gui_using_product_mesh",
        "completion_dialog": False,
        "solver_family": "magnetostatic_bem",
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-13T00:00:00Z",
        "source_copy_preserved": True,
        "expected_case_count": 4,
        "result_authority": ".mao",
        "history_table": "WL8T",
        "state_column": "PERM",
        "field_column": "B",
        "public_gate_status": "ok",
        "cases": cases,
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


def test_demagnetization_history_family_accepts_four_replayed_roles():
    summary = _history_family_summary()
    result = demagnetization_run_contract_gate(json.dumps(summary))
    assert result["status"] == "ok"
    assert result["schema"] == "elf-demagnetization-run-contract/v2"
    assert result["checks"]["four_history_roles_present"] is True
    assert json.loads(elf_demagnetization_run_contract_gate(json.dumps(summary)))["status"] == "ok"


def test_demagnetization_history_family_rejects_missing_dmeg_and_gui_route():
    summary = _history_family_summary()
    summary["execution_route"] = "launcher_gui"
    summary["cases"][0]["source_commands"]["DMEG"] = []
    result = demagnetization_run_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["direct_cli_without_launcher"] is False
    assert result["case_checks"]["external_reverse_field_cycle"][
        "hbrm_hbcn_dmeg_command_family_present"
    ] is False


def test_demagnetization_history_family_rejects_stale_replay():
    summary = _history_family_summary()
    summary["cases"][0]["replay_max_abs"] = 1.0e-4
    result = demagnetization_run_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["case_checks"]["external_reverse_field_cycle"]["two_replays_exact"] is False
