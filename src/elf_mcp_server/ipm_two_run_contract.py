"""Metadata-only contract for an IPM PM-only/current-on run pair."""
from __future__ import annotations

import json


_OUTPUT_ROLES = {
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def ipm_two_run_ldlq_contract_gate(summary_json: str) -> dict:
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    reference = summary.get("pm_only_reference")
    current_on = summary.get("current_on_run")
    derived = summary.get("derived_gate")
    if not isinstance(reference, dict) or not isinstance(current_on, dict) or not isinstance(derived, dict):
        raise ValueError("pm_only_reference, current_on_run and derived_gate are required")
    output_roles = current_on.get("output_roles")
    source_digests = current_on.get("source_digests")
    checks = {
        "direct_cli_without_launcher": current_on.get("execution_route") == "direct_solver_exe_no_gui",
        "completion_dialog_disabled": current_on.get("completion_dialog") is False,
        "solver_exit_zero": current_on.get("exit_code") == 0,
        "source_bundle_digests_recorded": isinstance(source_digests, dict)
        and len(source_digests) >= 4
        and all(bool(str(value).strip()) for value in source_digests.values()),
        "source_copy_preserved": current_on.get("source_copy_preserved") is True,
        "output_roles_complete": output_roles == _OUTPUT_ROLES,
        "all_outputs_fresh": current_on.get("all_outputs_fresh") is True,
        "three_phase_flux_records_complete": current_on.get("phase_ids") == [4, 5, 6]
        and current_on.get("flux_record_family") == "M1MF"
        and isinstance(current_on.get("time_step_count"), int)
        and current_on.get("flux_record_count") == 3 * current_on.get("time_step_count"),
        "pm_only_reference_verified": reference.get("role") == "pm_only"
        and reference.get("verified") is True
        and bool(str(reference.get("artifact_digest") or "").strip())
        and bool(str(reference.get("result_digest") or "").strip()),
        "same_angle_grid_and_phase_order": summary.get("same_angle_grid") is True
        and summary.get("phase_order") == ["A", "B", "C"],
        "pole_pairs_recorded": isinstance(summary.get("pole_pairs"), int)
        and summary.get("pole_pairs") > 0,
        "pm_subtraction_before_park": summary.get("flux_derivation") == "current_on_minus_pm_only_before_park",
        "public_physics_gate_passed": derived.get("schema") == "radia-motor-ipm-two-run-ldlq/v1"
        and derived.get("status") == "ok"
        and bool(str(derived.get("input_digest") or "").strip()),
        "solver_version_recorded": bool(str(current_on.get("solver_version") or "").strip()),
        "run_date_recorded": bool(str(current_on.get("run_date_utc") or "").strip()),
    }
    return {
        "schema": "elf-ipm-two-run-ldlq-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "time_step_count": current_on.get("time_step_count"),
        "notes": [
            "Keep the PM-only and current-on angle grids and phase order identical.",
            "Subtract phase flux before Park projection; total current-on flux is not an inductance numerator.",
            "The public physics gate owns numerical validation; this contract owns source and result-package integrity.",
        ],
    }
