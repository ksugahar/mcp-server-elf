"""Public-safe contract for the GUI-free mesh-to-solver pipeline."""
from __future__ import annotations

import json


def mesh_solver_pipeline_gate(summary_json: str) -> dict:
    """Validate sequencing and artifacts without opening local product files."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    stages = summary.get("stages")
    mesh_outputs = summary.get("mesh_output_suffixes")
    solver_outputs = summary.get("solver_output_suffixes")
    sample_count = summary.get("field_sample_count")
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "mesh_runs_before_solver": stages == ["mesh750", "magh1600"],
        "mesh_exit_zero": summary.get("mesh_exit_code") == 0,
        "solver_exit_zero": summary.get("solver_exit_code") == 0,
        "mesh_outputs_complete": mesh_outputs == [".meo", ".meg"],
        "solver_outputs_complete": solver_outputs == [".mao", ".mag"],
        "generated_mesh_fresh": summary.get("generated_mesh_fresh") is True,
        "mesh_log_fresh": summary.get("mesh_log_fresh") is True,
        "run_log_fresh": summary.get("run_log_fresh") is True,
        "field_result_fresh": summary.get("field_result_fresh") is True,
        "run_log_is_mao": summary.get("run_log_suffix") == ".mao",
        "field_result_is_mag": summary.get("field_result_suffix") == ".mag",
        "field_record_family_recorded": summary.get("field_record_family") == "M3GB",
        "field_samples_present": isinstance(sample_count, int) and sample_count > 0,
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
    }
    return {
        "schema": "elf-mesh-solver-pipeline-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "stages": stages,
        "field_sample_count": sample_count,
        "notes": [
            "the solver consumes a generated mesh artifact, not only the mesh input deck",
            "the run log and field result have distinct artifact roles",
        ],
    }
