import copy
import json

from elf_mcp_server.rotating_conductor_contract import rotating_conductor_periodic_contract_gate
from elf_mcp_server.server import elf_rotating_conductor_periodic_contract_gate


def _summary():
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "source_copy_preserved": True,
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "fresh_output_suffixes": [".meg", ".mao", ".mag", ".mat", ".mac", ".mas"],
        "run_log_suffix": ".mao",
        "field_result_suffix": ".mag",
        "solution_complete": True,
        "error_marker_count": 0,
        "time_step_count": 180,
        "time_sample_count": 181,
        "steps_per_period": 36,
        "period_count": 5,
        "source_material_sample_count": 181,
        "conductor_material_sample_count": 180,
        "period_relative_l2": [0.2, 0.04, 0.008, 0.0018],
        "stored_solver_version": "old",
        "live_solver_version": "new",
        "stored_replay_relative_l2": 0.0,
        "public_gate": {
            "policy": "rotating_conductor_periodic_settling_gate_v1",
            "status": "ok",
        },
    }


def test_rotating_conductor_contract_accepts_complete_periodic_run():
    summary = _summary()
    result = rotating_conductor_periodic_contract_gate(json.dumps(summary))
    assert result["status"] == "ok"
    assert json.loads(
        elf_rotating_conductor_periodic_contract_gate(json.dumps(summary))
    )["status"] == "ok"


def test_rotating_conductor_contract_rejects_stale_field_and_unsettled_periods():
    summary = copy.deepcopy(_summary())
    summary["fresh_output_suffixes"].remove(".mag")
    summary["period_relative_l2"][-1] = 0.02
    result = rotating_conductor_periodic_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["fresh_result_roles_complete"] is False
    assert result["checks"]["period_errors_recorded_and_decrease"] is False
