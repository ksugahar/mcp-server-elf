import json

from elf_mcp_server.force_pair_contract import force_pair_run_contract_gate
from elf_mcp_server.server import elf_force_pair_run_contract_gate


def _summary():
    common = {
        "solver_exit_code": 0,
        "run_log_suffix": ".mao",
        "field_result_suffix": ".mag",
        "run_log_fresh": True,
        "field_result_fresh": True,
        "total_row_count": 1,
        "selected_material_id": 3,
    }
    return {
        "execution_route": "direct_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_family": "magnetostatic_bem",
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-11T00:00:00Z",
        "interaction_axis": "x",
        "cases": [
            {**common, "pole_relation": "like", "force_N": [2.0, 0.0, 0.0], "torque_Nm": [0.0, 0.0, 0.0]},
            {**common, "pole_relation": "opposite", "force_N": [-1.99, 0.0, 0.0], "torque_Nm": [0.0, 0.0, 0.0]},
        ],
    }


def test_force_pair_contract_accepts_fresh_direct_cli_outputs():
    result = force_pair_run_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(elf_force_pair_run_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_force_pair_contract_rejects_stale_or_missing_total_output():
    summary = _summary()
    summary["cases"][1]["run_log_fresh"] = False
    summary["cases"][1]["total_row_count"] = 0
    result = force_pair_run_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["case_outputs_complete"] is False


def test_force_pair_contract_rejects_selection_and_polarity_drift():
    summary = _summary()
    summary["cases"][1]["selected_material_id"] = 4
    summary["cases"][1]["force_N"][0] = 1.99
    result = force_pair_run_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["selected_material_same"] is False
    assert result["checks"]["opposite_poles_attract"] is False
