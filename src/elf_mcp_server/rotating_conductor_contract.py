"""Metadata-only contract for rotating-conductor periodic-settling runs."""

from __future__ import annotations

import json
import math


def rotating_conductor_periodic_contract_gate(summary_json: str) -> dict:
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    try:
        errors = [float(value) for value in summary.get("period_relative_l2", [])]
        replay_error = float(summary["stored_replay_relative_l2"])
    except (KeyError, TypeError, ValueError):
        errors = []
        replay_error = math.inf
    outputs = summary.get("fresh_output_suffixes") or []
    public_gate = summary.get("public_gate") or {}
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "source_copy_preserved": summary.get("source_copy_preserved") is True,
        "mesh_and_solver_exit_zero": summary.get("mesh_exit_code") == 0
        and summary.get("solver_exit_code") == 0,
        "fresh_result_roles_complete": {".meg", ".mao", ".mag", ".mat", ".mac", ".mas"}
        <= set(outputs)
        and summary.get("run_log_suffix") == ".mao"
        and summary.get("field_result_suffix") == ".mag",
        "moment_solution_complete": summary.get("solution_complete") is True
        and summary.get("error_marker_count") == 0,
        "five_turn_time_axis_complete": summary.get("time_step_count") == 180
        and summary.get("time_sample_count") == 181
        and summary.get("steps_per_period") == 36
        and summary.get("period_count") == 5,
        "both_material_result_series_complete": summary.get("source_material_sample_count") == 181
        and summary.get("conductor_material_sample_count") == 180,
        "period_errors_recorded_and_decrease": len(errors) == 4
        and all(math.isfinite(value) and value >= 0.0 for value in errors)
        and all(right < left for left, right in zip(errors, errors[1:])),
        "stored_version_replay_is_explicit": bool(summary.get("stored_solver_version"))
        and bool(summary.get("live_solver_version"))
        and summary.get("stored_solver_version") != summary.get("live_solver_version")
        and math.isfinite(replay_error)
        and replay_error <= 1.0e-8,
        "public_periodic_gate_passed": public_gate.get("policy")
        == "rotating_conductor_periodic_settling_gate_v1"
        and public_gate.get("status") == "ok",
    }
    return {
        "schema": "elf-rotating-conductor-periodic-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "metrics": {
            "period_count": summary.get("period_count"),
            "final_period_relative_l2": errors[-1] if errors else None,
            "stored_replay_relative_l2": replay_error,
        },
        "notes": [
            "treat .mao as the run-log authority and .mag as the field-result artifact",
            "require several full rotations before calling a moving-conductor response periodic-steady",
            "keep solved values and private source provenance outside the public documentation server",
        ],
    }
