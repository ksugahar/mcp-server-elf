"""Public-safe result-package contract for a direct-CLI magnet force pair."""
from __future__ import annotations

import json
import math


def force_pair_run_contract_gate(summary_json: str) -> dict:
    """Validate execution metadata and force-pair semantics without opening files."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    cases = summary.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise ValueError("cases must contain exactly two records")
    indexed = {case.get("pole_relation"): case for case in cases if isinstance(case, dict)}
    if set(indexed) != {"like", "opposite"}:
        raise ValueError("cases must contain pole_relation 'like' and 'opposite'")

    def case_complete(case: dict) -> bool:
        force = case.get("force_N")
        torque = case.get("torque_Nm")
        return (
            case.get("solver_exit_code") == 0
            and case.get("run_log_suffix") == ".mao"
            and case.get("field_result_suffix") == ".mag"
            and case.get("run_log_fresh") is True
            and case.get("field_result_fresh") is True
            and case.get("total_row_count") == 1
            and isinstance(force, list) and len(force) == 3
            and isinstance(torque, list) and len(torque) == 3
            and all(math.isfinite(float(value)) for value in force + torque)
        )

    like = indexed["like"]
    opposite = indexed["opposite"]
    axis = summary.get("interaction_axis")
    axis_index = {"x": 0, "y": 1, "z": 2}.get(axis)
    rows_complete = case_complete(like) and case_complete(opposite)
    axial_like = float(like["force_N"][axis_index]) if rows_complete and axis_index is not None else 0.0
    axial_opposite = float(opposite["force_N"][axis_index]) if rows_complete and axis_index is not None else 0.0
    scale = max(abs(axial_like), abs(axial_opposite), 1.0e-300)
    mismatch = abs(abs(axial_like) - abs(axial_opposite)) / scale

    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_family_recorded": summary.get("solver_family") == "magnetostatic_bem",
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
        "interaction_axis_recorded": axis_index is not None,
        "selected_material_same": like.get("selected_material_id") == opposite.get("selected_material_id"),
        "case_outputs_complete": rows_complete,
        "like_poles_repel": rows_complete and axial_like > 0.0,
        "opposite_poles_attract": rows_complete and axial_opposite < 0.0,
        "axial_magnitudes_close": rows_complete and mismatch <= 2.0e-2,
    }
    return {
        "schema": "elf-force-pair-run-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "axial_magnitude_relative_mismatch": mismatch,
        "notes": [
            "the .mao TOTAL row is the force/torque authority; .mag is the field-result artifact",
            "reusing one selected material id prevents a source/target selection swap from masquerading as polarity physics",
        ],
    }
