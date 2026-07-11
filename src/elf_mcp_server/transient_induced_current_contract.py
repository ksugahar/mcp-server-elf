"""Metadata-only contract for GUI-free transient induced-current runs."""

from __future__ import annotations

import json
import math


_OUTPUT_ROLES = {
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def transient_induced_current_contract_gate(summary_json: str) -> dict:
    """Validate run metadata without opening product files or paths."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    compatibility = summary.get("compatibility_probe")
    run = summary.get("successful_run")
    if not isinstance(compatibility, dict) or not isinstance(run, dict):
        raise ValueError("compatibility_probe and successful_run must be objects")

    try:
        observed_steps = int(run["observed_step_count"])
        expected_steps = int(run["expected_step_count"])
        time_step = float(run["time_step_s"])
        resistance = float(run["secondary_resistance_ohm"])
        turns = float(run["secondary_turns"])
        memory = float(run["memory_factor"])
        coupling = float(run["coupling_gain"])
        residual = float(run["maximum_relative_residual"])
        tolerance = float(run["relative_residual_tolerance"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("successful_run is missing numeric contract fields") from exc

    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
        "source_copy_preserved": summary.get("source_copy_preserved") is True,
        "emfm_means_induced_current": summary.get("emfm_semantics") == "induced_current",
        "compatibility_probe_omitted_emgo": compatibility.get("emgo_enabled") is False,
        "compatibility_probe_stopped": compatibility.get("solver_exit_code") == 13,
        "compatibility_reason_identified": compatibility.get("reason") == "current_driven_emfm_requires_emgo",
        "successful_exit_zero": run.get("solver_exit_code") == 0,
        "emgo_enabled_for_current_drive": run.get("emgo_enabled") is True and run.get("current_driven_secondary") is True,
        "resistance_and_turns_positive": resistance > 0.0 and turns > 0.0,
        "step_count_matches": expected_steps > 0 and observed_steps == expected_steps,
        "uniform_positive_time_grid": run.get("uniform_time_grid") is True and math.isfinite(time_step) and time_step > 0.0,
        "zero_initial_currents": run.get("zero_initial_primary_current") is True and run.get("zero_initial_secondary_current") is True,
        "passive_first_order_memory": math.isfinite(memory) and 0.0 < memory < 1.0,
        "coupling_resolved": math.isfinite(coupling) and abs(coupling) > 0.0,
        "response_residual_within_tolerance": (
            math.isfinite(residual) and math.isfinite(tolerance) and tolerance > 0.0 and residual <= tolerance
        ),
        "moment_solution_completed": run.get("end_of_moment_solution") is True,
        "no_error_markers": run.get("error_marker_count") == 0,
        "output_roles_complete": run.get("output_roles") == _OUTPUT_ROLES,
        "all_outputs_fresh": run.get("all_outputs_fresh") is True,
    }
    return {
        "schema": "elf-transient-induced-current-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "notes": [
            "EMFM denotes induced-current calculation; it is not an electromagnetic-force result.",
            "Current-plus-resistance drive requires EMGO in the transient moment-solution block.",
            "The coupling sign depends on winding orientation, so gate its magnitude and passive memory rather than a fixed sign.",
        ],
    }
