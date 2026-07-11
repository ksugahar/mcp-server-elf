import copy
import json

from elf_mcp_server.flux_linkage_contract import flux_linkage_inductance_contract_gate
from elf_mcp_server.server import elf_flux_linkage_inductance_contract_gate


def _case(case_id, role, matrix):
    return {
        "case_id": case_id,
        "topology_role": role,
        "source_file_count": 2,
        "source_digest_count": 2,
        "source_copy_preserved": True,
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "current_steps_A": {"0": [1.0, 0.0], "1": [0.0, 1.0]},
        "output_roles": {
            ".meg": "geometry",
            ".mao": "run_log",
            ".mag": "field_result",
            ".mat": "matrix_state",
            ".mac": "mark_state",
        },
        "all_outputs_fresh": True,
        "matrix_H": matrix,
    }


def _summary():
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_version": "major.minor",
        "run_date_utc": "2026-07-12T00:00:00Z",
        "result_parser_contract": [
            "TIME STEP",
            "FLUX MID",
            "FLUX",
            "FLUX = INTEGRAL*TURN1",
        ],
        "cases": [
            _case("open-a", "open_path", [[4.0, -1.0], [-1.001, 1.0]]),
            _case("open-b", "thin_open_path", [[4.0, -0.9], [-0.901, 1.0]]),
            _case("closed", "closed_path", [[9.0, -2.7], [-2.699, 1.0]]),
        ],
    }


def test_flux_linkage_contract_accepts_reciprocal_live_family():
    result = flux_linkage_inductance_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(elf_flux_linkage_inductance_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_flux_linkage_contract_rejects_stale_output_and_nonphysical_matrix():
    bad = copy.deepcopy(_summary())
    bad["cases"][2]["all_outputs_fresh"] = False
    bad["cases"][2]["matrix_H"] = [[1.0, 2.0], [2.0, 1.0]]
    result = flux_linkage_inductance_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["all_source_cases_valid"] is False
