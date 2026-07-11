import json

from elf_mcp_server.phase_flux_contract import phase_flux_run_contract_gate
from elf_mcp_server.server import elf_python_phase_flux_run_contract_gate


def _summary():
    return {
        "execution_route": "direct_solver_exe_no_gui",
        "completion_dialog": False,
        "exit_code": 0,
        "run_log_suffix": ".mao",
        "result_suffix": ".mag",
        "run_log_fresh": True,
        "result_fresh": True,
        "phase_ids": [4, 5, 6],
        "flux_record_family": "M1MF",
        "time_step_count": 181,
        "flux_record_count": 543,
        "solver_version": "6.00",
        "run_date_utc": "2026-07-11T00:00:00Z",
    }


def test_phase_flux_run_contract_accepts_complete_direct_cli_package():
    gate = phase_flux_run_contract_gate(json.dumps(_summary()))
    assert gate["status"] == "ok"
    assert all(gate["checks"].values())
    assert json.loads(elf_python_phase_flux_run_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_phase_flux_run_contract_rejects_launcher_and_stale_mao():
    summary = _summary()
    summary["execution_route"] = "Launcher.exe GUI route"
    summary["run_log_fresh"] = False
    gate = phase_flux_run_contract_gate(json.dumps(summary))
    assert gate["status"] == "needs_attention"
    assert gate["checks"]["direct_cli_without_launcher"] is False
    assert gate["checks"]["run_log_fresh"] is False


def test_phase_flux_run_contract_rejects_incomplete_phase_rows():
    summary = _summary()
    summary["flux_record_count"] = 542
    gate = phase_flux_run_contract_gate(json.dumps(summary))
    assert gate["status"] == "needs_attention"
    assert gate["checks"]["three_records_per_step"] is False
