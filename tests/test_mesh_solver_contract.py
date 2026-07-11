import json

from elf_mcp_server.mesh_solver_contract import mesh_solver_pipeline_gate
from elf_mcp_server.server import elf_mesh_solver_pipeline_gate


def _summary():
    return {
        "execution_route": "direct_solver_exe_no_gui",
        "completion_dialog": False,
        "stages": ["mesh750", "magh1600"],
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "mesh_output_suffixes": [".meo", ".meg"],
        "solver_output_suffixes": [".mao", ".mag"],
        "generated_mesh_fresh": True,
        "mesh_log_fresh": True,
        "run_log_fresh": True,
        "field_result_fresh": True,
        "run_log_suffix": ".mao",
        "field_result_suffix": ".mag",
        "field_record_family": "M3GB",
        "field_sample_count": 21,
        "solver_version": "16.0",
        "run_date_utc": "2026-07-11T00:00:00Z",
    }


def test_mesh_solver_pipeline_accepts_complete_cli_sequence():
    result = mesh_solver_pipeline_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert all(result["checks"].values())
    assert json.loads(elf_mesh_solver_pipeline_gate(json.dumps(_summary())))["status"] == "ok"


def test_mesh_solver_pipeline_rejects_solver_before_mesh():
    summary = _summary()
    summary["stages"] = ["magh1600"]
    summary["mesh_exit_code"] = None
    summary["solver_exit_code"] = 28
    summary["generated_mesh_fresh"] = False
    result = mesh_solver_pipeline_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["mesh_runs_before_solver"] is False
    assert result["checks"]["generated_mesh_fresh"] is False
    assert result["checks"]["solver_exit_zero"] is False


def test_mesh_solver_pipeline_rejects_missing_field_records():
    summary = _summary()
    summary["field_sample_count"] = 0
    summary["field_record_family"] = ""
    result = mesh_solver_pipeline_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["field_samples_present"] is False
    assert result["checks"]["field_record_family_recorded"] is False
