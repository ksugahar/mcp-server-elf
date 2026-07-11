import json

from elf_mcp_server.magnet_model_contract import magnet_model_producer_contract_gate
from elf_mcp_server.server import elf_magnet_model_producer_contract_gate


def _summary():
    return {
        "execution_route": "direct_solver_exe_no_gui",
        "stages": ["field_solve", "magnet_model_extract"],
        "solver_exit_code": 0,
        "extractor_exit_code": 0,
        "source_output_roles": {".mao": "run_log", ".mag": "field_result", ".mac": "mark_file", ".mat": "matrix_file"},
        "handoff_output_roles": {".mai": "magnet_control", ".meg": "magnet_geometry"},
        "field_result_fresh": True,
        "magnet_control_fresh": True,
        "magnet_geometry_fresh": True,
        "magnet_control_digest": "b" * 64,
        "magnet_geometry_digest": "c" * 64,
        "numbering_policy": "preserve",
        "element_id_offset": 0,
        "node_id_offset": 0,
        "material_mapping_count": 4,
        "nonlinear_residual_phases": [[0.31, 0.082, 0.031], [0.040, 0.0061]],
        "nonlinear_tolerance": 0.01,
        "solver_version": "16.0.0",
        "run_date_utc": "2026-07-11T00:00:00Z",
    }


def test_magnet_model_contract_accepts_complete_two_stage_package():
    result = magnet_model_producer_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert result["handoff_ready"] is True
    assert json.loads(elf_magnet_model_producer_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_magnet_model_contract_rejects_mark_file_mislabel_and_numbering_drift():
    summary = _summary()
    summary["handoff_output_roles"] = {".mac": "magnet_state"}
    summary["element_id_offset"] = 7
    summary["nonlinear_residual_phases"][-1][-1] = 0.061
    result = magnet_model_producer_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["handoff_roles_complete"] is False
    assert result["checks"]["numbering_preserved"] is False
