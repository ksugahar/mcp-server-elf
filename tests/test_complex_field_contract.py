import copy
import json

from elf_mcp_server.complex_field_contract import complex_field_run_contract_gate
from elf_mcp_server.server import elf_complex_field_run_contract_gate


OUTPUT_ROLES = {
    ".meg": "geometry",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def good():
    features = {
        "ABCL2": {"ohm2_count": 1, "image_axis": None, "channel_change": False, "lone_boundary": False},
        "ABCLH": {"ohm2_count": 2, "image_axis": None, "channel_change": False, "lone_boundary": False},
        "ABCLHX": {"ohm2_count": 2, "image_axis": "X", "channel_change": True, "lone_boundary": True},
    }
    counts = {
        "ABCL2": (72, 2),
        "ABCLH": (40, 2),
        "ABCLHX": (36, 4),
    }
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "gui_visible": False,
        "completion_dialog": False,
        "solver_version": "product solver version",
        "run_date_utc": "2026-07-12T00:00:00+00:00",
        "result_parser_contract": ["REAL PART", "IMAGINARY PART", "AB8T", "BMAX ELEMENT"],
        "cases": [
            {
                "case_id": case_id,
                "source_file_count": 2,
                "source_digest_count": 2,
                "source_copy_preserved": True,
                "mesh_exit_code": 0,
                "solver_exit_code": 0,
                "output_roles": OUTPUT_ROLES,
                "all_outputs_fresh": True,
                "source_features": features[case_id],
                "field_row_count": counts[case_id][0],
                "maximum_count": counts[case_id][1],
                "frequency_hz": 1000.0,
                "ampere_turns": 100.0,
                "field_unit": "T",
                "public_gate_status": "ok",
            }
            for case_id in ("ABCL2", "ABCLH", "ABCLHX")
        ],
    }


def test_accepts_three_source_runs_and_dispatches():
    payload = good()
    result = complex_field_run_contract_gate(json.dumps(payload))
    assert result["status"] == "ok"
    dispatched = json.loads(elf_complex_field_run_contract_gate(json.dumps(payload)))
    assert dispatched["status"] == "ok"


def test_rejects_missing_image_signature_and_stale_output():
    payload = copy.deepcopy(good())
    payload["cases"][2]["source_features"]["image_axis"] = None
    payload["cases"][2]["all_outputs_fresh"] = False
    result = complex_field_run_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    failed = result["cases"][2]["checks"]
    assert failed["source_feature_signature_matches"] is False
    assert failed["output_roles_complete_and_fresh"] is False
