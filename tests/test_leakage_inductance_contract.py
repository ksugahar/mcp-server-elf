import copy
import json

from elf_mcp_server.leakage_inductance_contract import (
    leakage_inductance_contract_gate,
)
from elf_mcp_server.server import elf_leakage_inductance_contract_gate


def _route(role):
    row = {
        "route_role": role,
        "source_file_count": 2,
        "source_digest_count": 2,
        "source_copy_preserved": True,
        "replay_count": 2,
        "replay_max_abs_Wb": 0.0,
        "mesh_exit_codes": [0, 0],
        "solver_exit_codes": [0, 0],
        "output_roles": {
            ".meg": "geometry",
            ".mao": "run_log",
            ".mag": "field_result",
            ".mat": "matrix_state",
            ".mac": "mark_state",
        },
        "all_outputs_fresh": True,
    }
    if role == "compensated_energy":
        row.update(
            {
                "turns": [2.0, 1.0],
                "currents_A": [1.0, -2.0],
                "flux_linkage_Wb": [2.0, -0.11],
            }
        )
    else:
        row.update(
            {
                "current_steps_A": {"0": [1.0, 0.0], "1": [0.0, 1.0]},
                "matrix_H": [[5.0, 1.5], [1.49, 0.8]],
            }
        )
    return row


def _summary():
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-13T00:00:00Z",
        "result_authority": ".mao",
        "result_parser_contract": [
            "TIME STEP",
            "FLUX MID",
            "IMAG",
            "FLUX",
            "FLUX = INTEGRAL*TURN1",
        ],
        "routes": [_route("compensated_energy"), _route("unit_current_basis")],
    }


def test_leakage_contract_accepts_independent_live_routes():
    result = leakage_inductance_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(
        elf_leakage_inductance_contract_gate(json.dumps(_summary()))
    )["status"] == "ok"


def test_leakage_contract_rejects_stale_and_uncompensated_route():
    bad = copy.deepcopy(_summary())
    bad["routes"][0]["currents_A"][1] = -1.5
    bad["routes"][1]["all_outputs_fresh"] = False
    result = leakage_inductance_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["ampere_turn_compensation_close"] is False
    assert result["checks"]["both_routes_replayed_and_fresh"] is False
