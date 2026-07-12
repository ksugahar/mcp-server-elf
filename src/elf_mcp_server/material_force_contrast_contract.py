"""Metadata-only contract for a direct-CLI material-force contrast run family."""

from __future__ import annotations

import json
import math


def material_force_contrast_contract_gate(summary_json: str) -> dict:
    """Validate output roles, version drift policy, and public force closure."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    cases = summary.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        raise ValueError("cases must contain exactly four records")
    roles = {"background", "attractive", "repulsive_low", "repulsive_high"}
    indexed = {case.get("role"): case for case in cases if isinstance(case, dict)}
    if set(indexed) != roles:
        raise ValueError(f"case roles must be exactly {sorted(roles)}")

    def complete(case: dict) -> bool:
        outputs = case.get("fresh_output_suffixes")
        try:
            regression_error = float(case["force_regression_relative_error"])
        except (KeyError, TypeError, ValueError):
            return False
        return (
            case.get("mesh_exit_code") == 0
            and case.get("solver_exit_code") == 0
            and case.get("source_copy_preserved") is True
            and case.get("solution_complete") is True
            and case.get("error_marker_count") == 0
            and case.get("total_row_count") == 1
            and case.get("force_selection_recorded") is True
            and case.get("solution_sequence") == ["moment", "field", "force"]
            and isinstance(outputs, list)
            and {".meg", ".mao", ".mag", ".mat", ".mac"} <= set(outputs)
            and case.get("run_log_suffix") == ".mao"
            and case.get("run_log_fresh") is True
            and case.get("field_result_suffix") == ".mag"
            and case.get("field_result_fresh") is True
            and case.get("stored_solver_version")
            and case.get("live_solver_version")
            and case.get("stored_solver_version") != case.get("live_solver_version")
            and case.get("mesh_hash_changed") is True
            and case.get("mesh_size_preserved") is True
            and math.isfinite(regression_error)
            and regression_error >= 0.0
        )

    def regression_error(role: str) -> float:
        try:
            value = float(indexed[role]["force_regression_relative_error"])
        except (KeyError, TypeError, ValueError):
            return math.inf
        return value if math.isfinite(value) and value >= 0.0 else math.inf

    complete_cases = all(complete(case) for case in indexed.values())
    weak_errors = [
        regression_error(role)
        for role in ("background", "attractive", "repulsive_low")
    ]
    strong_error = regression_error("repulsive_high")
    public_gate = summary.get("public_gate") or {}
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_family_recorded": summary.get("solver_family") == "magnetostatic_bem",
        "mao_total_field_order_recorded": summary.get("result_authority") == ".mao TOTAL"
        and summary.get("total_field_order")
        == ["area_m2", "flux_wb", "force_x_n", "force_y_n", "force_z_n"],
        "case_outputs_and_selection_complete": complete_cases,
        "weak_contrast_regression_is_tight": complete_cases and max(weak_errors) <= 1.0e-3,
        "strong_contrast_version_drift_is_bounded": complete_cases
        and strong_error <= 0.05,
        "version_and_mesh_migration_not_hidden": summary.get("version_drift_policy")
        == "record_versions_and_regenerated_mesh_before_applying_role_specific_bands",
        "public_material_force_gate_passed": public_gate.get("policy")
        == "material_contrast_force_gate_v1"
        and public_gate.get("status") == "ok",
    }
    return {
        "schema": "elf-material-force-contrast-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "metrics": {
            "max_weak_contrast_regression_relative_error": max(weak_errors),
            "strong_contrast_regression_relative_error": strong_error,
        },
        "notes": [
            "the .mao TOTAL row is the force-vector authority; .mei is input, not result",
            "do not silently widen one global regression tolerance when solver version and regenerated mesh change",
            "keep solved values and private source provenance outside the public documentation server",
        ],
    }
