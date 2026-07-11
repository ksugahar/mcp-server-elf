"""Public-safe contract for a magnet-model extraction pipeline."""
from __future__ import annotations

import json
import re


_SHA256 = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")


def magnet_model_producer_contract_gate(summary_json: str) -> dict:
    """Validate metadata only; never opens local product paths or result files."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    phases = summary.get("nonlinear_residual_phases")
    phases_ok = isinstance(phases, list) and bool(phases) and all(isinstance(phase, list) and bool(phase) for phase in phases)
    decreasing = phases_ok and all(all(float(right) < float(left) for left, right in zip(phase, phase[1:])) for phase in phases)
    terminal = float(phases[-1][-1]) if phases_ok else float("inf")
    tolerance = float(summary.get("nonlinear_tolerance", 0.0))
    source_roles = summary.get("source_output_roles")
    handoff_roles = summary.get("handoff_output_roles")
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_solver_exe_no_gui",
        "pipeline_order_recorded": summary.get("stages") == ["field_solve", "magnet_model_extract"],
        "solver_exit_zero": summary.get("solver_exit_code") == 0,
        "extractor_exit_zero": summary.get("extractor_exit_code") == 0,
        "source_roles_complete": source_roles == {".mao": "run_log", ".mag": "field_result", ".mac": "mark_file", ".mat": "matrix_file"},
        "handoff_roles_complete": handoff_roles == {".mai": "magnet_control", ".meg": "magnet_geometry"},
        "field_result_fresh": summary.get("field_result_fresh") is True,
        "magnet_control_fresh": summary.get("magnet_control_fresh") is True,
        "magnet_geometry_fresh": summary.get("magnet_geometry_fresh") is True,
        "magnet_control_digest_is_sha256": bool(_SHA256.fullmatch(str(summary.get("magnet_control_digest", "")).strip())),
        "magnet_geometry_digest_is_sha256": bool(_SHA256.fullmatch(str(summary.get("magnet_geometry_digest", "")).strip())),
        "numbering_preserved": summary.get("numbering_policy") == "preserve" and summary.get("element_id_offset") == 0 and summary.get("node_id_offset") == 0,
        "material_mapping_present": isinstance(summary.get("material_mapping_count"), int) and summary["material_mapping_count"] > 0,
        "nonlinear_phases_recorded": phases_ok,
        "residual_decreases_within_phases": decreasing,
        "terminal_residual_meets_tolerance": tolerance > 0.0 and terminal <= tolerance,
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
    }
    return {
        "schema": "elf-magnet-model-producer-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "handoff_ready": all(checks.values()),
        "terminal_residual": terminal,
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "notes": [
            "the mark file is not the magnet model handoff",
            "the downstream model consists of separate control/material and geometry artifacts",
        ],
    }
