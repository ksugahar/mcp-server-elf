"""Public-safe contract for a direct-CLI three-phase flux run package."""
from __future__ import annotations

import json


def phase_flux_run_contract_gate(summary_json: str) -> dict:
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    phases = summary.get("phase_ids")
    step_count = summary.get("time_step_count")
    record_count = summary.get("flux_record_count")
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_exit_zero": summary.get("exit_code") == 0,
        "run_log_is_mao": summary.get("run_log_suffix") == ".mao",
        "result_is_mag": summary.get("result_suffix") == ".mag",
        "run_log_fresh": summary.get("run_log_fresh") is True,
        "result_fresh": summary.get("result_fresh") is True,
        "three_phase_ids_recorded": phases == [4, 5, 6],
        "flux_record_family_is_m1mf": summary.get("flux_record_family") == "M1MF",
        "step_count_is_complete": isinstance(step_count, int) and step_count >= 12,
        "three_records_per_step": isinstance(record_count, int)
        and isinstance(step_count, int)
        and record_count == 3 * step_count,
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
    }
    return {
        "schema": "elf-python-phase-flux-run-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "time_step_count": step_count,
        "phase_ids": phases,
        "flux_record_count": record_count,
    }
