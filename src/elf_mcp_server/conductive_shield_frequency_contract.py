"""Public-safe contract for paired magnetic/conductive shield sweeps."""

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


def conductive_shield_frequency_contract_gate(summary_json: str) -> dict[str, object]:
    """Gate immutable direct execution and normalized dual-regime evidence."""
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
        or len(replays) != 4
        or any(not isinstance(row, Mapping) for row in replays)
    ):
        raise ValueError("replays must contain four objects")
    frequency_rows = int(summary.get("frequency_row_count", 0))
    if frequency_rows < 4:
        raise ValueError("frequency_row_count must be at least four")
    metrics = summary.get("normalized_metrics")
    if not isinstance(metrics, Mapping):
        raise ValueError("normalized_metrics must be an object")
    faraday_error = _finite(metrics.get("maximum_faraday_relative_error"), "maximum_faraday_relative_error")
    low_ratio = _finite(metrics.get("low_frequency_secondary_coupling_ratio"), "low_frequency_secondary_coupling_ratio")
    high_ratio = _finite(metrics.get("high_frequency_secondary_coupling_ratio"), "high_frequency_secondary_coupling_ratio")
    public_gate = summary.get("public_gate")
    if not isinstance(public_gate, Mapping):
        public_gate = {}
    model_contract = summary.get("model_contract")
    if not isinstance(model_contract, Mapping):
        model_contract = {}

    replay_checks = []
    role_counts = {"baseline": 0, "shielded": 0}
    for replay in replays:
        role = str(replay.get("model_role") or "")
        if role in role_counts:
            role_counts[role] += 1
        markers = replay.get("parser_markers")
        replay_checks.append(
            replay.get("mesh_exit_code") == 0
            and replay.get("solver_exit_code") == 0
            and replay.get("output_roles") == _OUTPUT_ROLES
            and replay.get("all_outputs_fresh") is True
            and replay.get("owned_processes_after") == 0
            and isinstance(markers, Mapping)
            and markers.get("frequency_rows") == frequency_rows
            and markers.get("emfm_complex_rows") == 2 * frequency_rows
            and markers.get("flum_complex_rows") == 2 * frequency_rows
        )

    timing = summary.get("timing_breakdown_s")
    timing_ok = False
    if isinstance(timing, Mapping) and len(timing) == 4:
        try:
            timing_ok = all(
                math.isfinite(float(value)) and float(value) >= 0.0
                for value in timing.values()
            )
        except (TypeError, ValueError):
            timing_ok = False

    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "source_copies_are_immutable": summary.get("source_copy_preserved") is True
        and summary.get("source_file_count_per_model") == 2
        and summary.get("source_digest_count") == 4,
        "paired_model_roles_are_explicit": role_counts == {"baseline": 2, "shielded": 2}
        and model_contract.get("paired_geometry") is True
        and model_contract.get("baseline_has_shield") is False
        and model_contract.get("comparison_has_conductive_magnetic_shield") is True,
        "solver_version_and_run_date_recorded": bool(str(summary.get("solver_version") or "").strip())
        and bool(str(summary.get("run_date_utc") or "").strip()),
        "four_complete_fresh_replays": all(replay_checks),
        "per_role_replay_observables_are_deterministic": summary.get("baseline_replay_rows_identical") is True
        and summary.get("shielded_replay_rows_identical") is True,
        "normalized_faraday_identity_is_closed": faraday_error <= 1.0e-4,
        "normalized_dual_regime_is_present": low_ratio > 1.0 and high_ratio < 1.0,
        "solver_neutral_gate_closed": public_gate.get("policy") == "magnetic_conductive_shield_frequency_gate_v1"
        and public_gate.get("status") == "ok",
        "exactly_four_timing_stages": timing_ok,
    }
    return {
        "schema": "elf-conductive-shield-frequency-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "normalized_metrics": {
            "maximum_faraday_relative_error": faraday_error,
            "low_frequency_secondary_coupling_ratio": low_ratio,
            "high_frequency_secondary_coupling_ratio": high_ratio,
        },
        "notes": [
            "Use direct mesh and solver executables so completion dialogs cannot block automation.",
            "Count EMFM and FLUM complex rows against the declared frequency grid for both model roles.",
            "Keep product paths and solved phasors private; publish only normalized dual-regime diagnostics.",
        ],
    }
