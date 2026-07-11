"""Metadata-only contract for GUI-free permanent-magnet demagnetization runs."""
from __future__ import annotations

import json
import math


_OUTPUT_ROLES = {
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def demagnetization_run_contract_gate(summary_json: str) -> dict:
    """Validate a structured run summary without opening product files or paths."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    cases = summary.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")

    case_checks: dict[str, dict[str, bool]] = {}
    for position, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{position}] must be an object")
        case_id = str(case.get("case_id", "")).strip() or f"case-{position}"
        output_roles = case.get("output_roles")
        state_min_history = case.get("state_min_history")
        if not isinstance(state_min_history, list) or len(state_min_history) < 3:
            state_min_history = []
        states = [float(value) for value in state_min_history]
        finite_states = bool(states) and all(math.isfinite(value) for value in states)
        final_convergence = float(case.get("maximum_final_convergence", math.inf))
        tolerance = float(case.get("nonlinear_tolerance", 0.0))
        case_checks[case_id] = {
            "exit_zero": case.get("solver_exit_code") == 0,
            "dmeg_enabled": case.get("dmeg_enabled") is True,
            "nonlinear_limit_recorded": int(case.get("maximum_nonlinear_iterations", 0)) > 0,
            "nonlinear_tolerance_positive": math.isfinite(tolerance) and tolerance > 0.0,
            "all_steps_converged": math.isfinite(final_convergence) and tolerance > 0.0 and final_convergence <= tolerance,
            "step_count_matches": int(case.get("observed_step_count", -1)) == int(case.get("expected_step_count", -2)),
            "moment_solution_completed": case.get("end_of_moment_solution") is True,
            "no_error_markers": case.get("error_marker_count") == 0,
            "output_roles_complete": output_roles == _OUTPUT_ROLES,
            "all_outputs_fresh": case.get("all_outputs_fresh") is True,
            "state_history_bounded": finite_states and all(0.0 <= value <= 1.0 for value in states),
            "irreversible_state_observed": finite_states and min(states[1:]) < states[0],
            "state_does_not_recover": finite_states and all(
                later <= earlier + 1.0e-9 for earlier, later in zip(states, states[1:])
            ),
        }

    flat_checks = [ok for checks in case_checks.values() for ok in checks.values()]
    case_ids = [str(case.get("case_id", "")).strip() for case in cases]
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_family_recorded": summary.get("solver_family") == "magnetostatic_bem",
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
        "source_copy_preserved": summary.get("source_copy_preserved") is True,
        "case_ids_unique": all(case_ids) and len(case_ids) == len(set(case_ids)),
        "case_count_matches": len(cases) == int(summary.get("expected_case_count", -1)),
        "all_case_contracts_pass": bool(flat_checks) and all(flat_checks),
    }
    return {
        "schema": "elf-demagnetization-run-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "case_checks": case_checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "notes": [
            "the run log is the convergence and history authority; field output alone cannot prove irreversible demagnetization",
            "execute a work copy and compare source digests so product examples remain immutable",
        ],
    }
