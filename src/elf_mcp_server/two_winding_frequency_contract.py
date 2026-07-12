"""Public-safe run contract for two-winding harmonic frequency sweeps."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence


_OUTPUT_ROLES = {
    ".meg": "geometry",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def _finite(value: object, name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(parsed) or parsed < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return parsed


def two_winding_frequency_contract_gate(summary_json: str) -> dict[str, object]:
    """Gate immutable direct execution and normalized Faraday diagnostics."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, Mapping):
        raise ValueError("summary_json must decode to an object")
    replays = summary.get("replays")
    if (
        not isinstance(replays, Sequence)
        or isinstance(replays, (str, bytes))
        or len(replays) != 2
        or any(not isinstance(row, Mapping) for row in replays)
    ):
        raise ValueError("replays must contain exactly two objects")
    metrics = summary.get("normalized_metrics")
    if not isinstance(metrics, Mapping):
        raise ValueError("normalized_metrics must be an object")
    faraday_error = _finite(
        metrics.get("maximum_faraday_relative_error"),
        "normalized_metrics.maximum_faraday_relative_error",
    )
    linkage_gap = _finite(
        metrics.get("maximum_linkage_per_turn_relative_gap"),
        "normalized_metrics.maximum_linkage_per_turn_relative_gap",
    )
    public_gate = summary.get("public_gate")
    if not isinstance(public_gate, Mapping):
        public_gate = {}

    replay_checks = []
    for replay in replays:
        markers = replay.get("parser_markers")
        replay_checks.append(
            replay.get("mesh_exit_code") == 0
            and replay.get("solver_exit_code") == 0
            and replay.get("output_roles") == _OUTPUT_ROLES
            and replay.get("all_outputs_fresh") is True
            and replay.get("owned_processes_after") == 0
            and isinstance(markers, Mapping)
            and markers.get("frequency_rows") == 7
            and markers.get("emfm_complex_rows") == 14
            and markers.get("flum_complex_rows") == 14
        )

    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "source_copy_is_immutable": summary.get("source_copy_preserved") is True
        and summary.get("source_file_count") == 2
        and summary.get("source_digest_count") == 2,
        "solver_version_and_run_date_recorded": bool(
            str(summary.get("solver_version") or "").strip()
        )
        and bool(str(summary.get("run_date_utc") or "").strip()),
        "two_complete_fresh_replays": all(replay_checks),
        "replay_observables_are_deterministic": summary.get("replay_rows_identical")
        is True,
        "faraday_identity_is_below_1e_4": faraday_error <= 1.0e-4,
        "two_winding_linkage_per_turn_gap_is_bounded": linkage_gap <= 0.15,
        "solver_neutral_gate_closed": public_gate.get("policy")
        == "two_winding_frequency_faraday_gate_v1"
        and public_gate.get("status") == "ok",
    }
    return {
        "schema": "elf-two-winding-frequency-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "normalized_metrics": {
            "maximum_faraday_relative_error": faraday_error,
            "maximum_linkage_per_turn_relative_gap": linkage_gap,
        },
        "notes": [
            "Use direct mesh and solver executables so completion dialogs cannot block automation.",
            "Parse both real and imaginary EMFM and FLUM records for each winding and frequency.",
            "Keep product paths and solved phasors private; publish only normalized diagnostics.",
        ],
    }
