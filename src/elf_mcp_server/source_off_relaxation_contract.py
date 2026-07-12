"""Metadata-only contract for a GUI-free source-off coil relaxation run."""

from __future__ import annotations

import json


_OUTPUT_ROLES = {
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}
_REQUIRED_HEADERS = {"COI1_V", "VOL1", "OHM1", "EMFM", "TIME"}


def source_off_relaxation_contract_gate(summary_json: str) -> dict:
    """Validate source/result metadata without opening product files or paths."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    transient = summary.get("transient_run")
    companion = summary.get("static_companion")
    public_gate = summary.get("public_gate")
    if not all(isinstance(value, dict) for value in (transient, companion, public_gate)):
        raise ValueError("transient_run, static_companion and public_gate are required objects")

    source_digests = transient.get("source_digests")
    companion_digests = companion.get("source_digests")
    feature_headers = transient.get("feature_headers")
    checks = {
        "direct_mesh_then_solver_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "case_working_directory_contains_input_pair": summary.get(
            "working_directory_contains_input_pair"
        )
        is True,
        "solver_version_recorded": bool(str(summary.get("solver_version") or "").strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc") or "").strip()),
        "source_copy_preserved": summary.get("source_copy_preserved") is True,
        "source_pair_digests_recorded": isinstance(source_digests, dict)
        and set(source_digests) == {"control", "mesh"}
        and all(bool(str(value).strip()) for value in source_digests.values()),
        "mesh_and_solver_exit_zero": transient.get("mesh_exit_code") == 0
        and transient.get("solver_exit_code") == 0,
        "voltage_drive_headers_complete": transient.get("drive_mode") == "voltage"
        and isinstance(feature_headers, list)
        and set(feature_headers) == _REQUIRED_HEADERS,
        "linear_source_off_schedule_recorded": transient.get("material_response")
        == "linear"
        and transient.get("source_schedule") == "initial_voltage_then_zero",
        "emfm_is_induced_current": transient.get("emfm_semantics")
        == "induced_current",
        "total_current_derivation_recorded": transient.get("total_current_derivation")
        == "voltage_over_resistance_plus_induced_current",
        "step_and_emfm_records_complete": isinstance(
            transient.get("expected_step_count"), int
        )
        and transient.get("expected_step_count") >= 3
        and transient.get("observed_step_count")
        == transient.get("expected_step_count")
        and transient.get("emfm_record_count")
        == transient.get("expected_step_count"),
        "moment_solution_completed_without_errors": transient.get(
            "end_of_moment_solution"
        )
        is True
        and transient.get("error_marker_count") == 0,
        "output_roles_complete_and_fresh": transient.get("output_roles")
        == _OUTPUT_ROLES
        and transient.get("all_outputs_fresh") is True,
        "static_companion_is_classification_only": companion.get("role")
        == "nonlinear_current_driven_classification_only"
        and companion.get("material_response") == "nonlinear"
        and companion.get("numerical_cross_comparison") is False
        and companion.get("mesh_exit_code") == 0
        and companion.get("solver_exit_code") == 0
        and isinstance(companion_digests, dict)
        and set(companion_digests) == {"control", "mesh"}
        and all(bool(str(value).strip()) for value in companion_digests.values()),
        "public_physics_gate_passed": public_gate.get("schema")
        == "radia-source-off-linear-relaxation/v1"
        and public_gate.get("status") == "ok"
        and bool(str(public_gate.get("input_digest") or "").strip()),
    }
    return {
        "schema": "elf-source-off-relaxation-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "notes": [
            "Run the mesh and solver executables from the case directory containing the copied input pair.",
            "EMFM is induced current; total voltage-driven coil current is V/R plus that contribution.",
            "A nonlinear current-driven companion classifies another workflow and is not a numerical reference for the linear transient.",
            "The solver-neutral gate owns numerical decay checks; this contract owns input and result-package integrity.",
        ],
    }
