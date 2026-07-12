"""Public-safe grouped magnetization handoff metadata contract."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence


_PIPELINE = [
    "source_excitation_solve",
    "magnet_submodel_extraction",
    "air_region_geometry_merge",
    "sequential_vector_injection",
    "assembled_field_solve",
]
_OUTPUTS = {".meg", ".mao", ".mag", ".mat", ".mac"}


def magnetization_group_handoff_contract_gate(summary_json: str) -> dict[str, object]:
    """Validate staged source dependencies and scrubbed assembled-run metadata."""

    try:
        summary = json.loads(summary_json)
    except (json.JSONDecodeError, TypeError) as exc:
        return {
            "policy": "elf_magnetization_group_handoff_contract_gate_v1",
            "status": "invalid_input",
            "error": str(exc),
        }
    if not isinstance(summary, Mapping):
        return {
            "policy": "elf_magnetization_group_handoff_contract_gate_v1",
            "status": "invalid_input",
            "error": "summary must be an object",
        }
    runs_value = summary.get("runs")
    runs = (
        list(runs_value)
        if isinstance(runs_value, Sequence) and not isinstance(runs_value, (str, bytes))
        else []
    )
    public_gate = summary.get("public_gate")
    if not isinstance(public_gate, Mapping):
        public_gate = {}
    shortcut = summary.get("invalid_shortcut_probe")
    if not isinstance(shortcut, Mapping):
        shortcut = {}
    timing = summary.get("timing")
    if not isinstance(timing, Mapping):
        timing = {}
    expected_groups = int(summary.get("expected_group_count", -1))
    expected_per_group = int(summary.get("expected_vectors_per_group", -1))

    checks = {
        "direct_preassembled_solver_route_recorded": summary.get("execution_route")
        == "direct_solver_preassembled_mesh_no_gui"
        and summary.get("completion_dialog") is False,
        "source_pipeline_dependencies_are_explicit": summary.get("pipeline_stages")
        == _PIPELINE,
        "source_copy_and_preassembled_mesh_preserved": summary.get(
            "source_copy_preserved"
        )
        is True
        and summary.get("preassembled_mesh_used") is True,
        "group_and_vector_cardinality_are_explicit": expected_groups >= 2
        and expected_per_group > 0
        and summary.get("magnet_submodel_count") == expected_groups
        and summary.get("assembled_group_count") == expected_groups
        and summary.get("assembled_vector_count")
        == expected_groups * expected_per_group,
        "dependency_omission_shortcut_is_rejected": shortcut.get("attempt")
        == "regenerate_assembled_mesh_without_required_magnet_submodels"
        and shortcut.get("mesh_exit_code") != 0
        and shortcut.get("solver_exit_code") != 0
        and shortcut.get("failure_signature")
        == "missing_mesh_book_end_after_dependency_omission"
        and shortcut.get("rejected") is True,
        "two_fresh_assembled_runs_recorded": len(runs) >= 2
        and all(isinstance(run, Mapping) for run in runs),
        "fresh_runs_complete_without_errors": len(runs) >= 2
        and all(
            run.get("solver_exit_code") == 0
            and run.get("solution_complete") is True
            and run.get("error_marker_count") == 0
            and run.get("source_copy_preserved") is True
            for run in runs
            if isinstance(run, Mapping)
        ),
        "fresh_result_roles_are_complete": len(runs) >= 2
        and all(
            set(run.get("fresh_output_suffixes", [])) >= _OUTPUTS
            and run.get("run_log_suffix") == ".mao"
            and run.get("field_result_suffix") == ".mag"
            for run in runs
            if isinstance(run, Mapping)
        ),
        "fresh_group_metadata_are_complete": len(runs) >= 2
        and all(
            run.get("group_ids") == list(range(1, expected_groups + 1))
            and run.get("group_vector_counts")
            == {str(group): expected_per_group for group in range(1, expected_groups + 1)}
            for run in runs
            if isinstance(run, Mapping)
        ),
        "public_physics_gate_passed": public_gate.get("policy")
        == "mirror_symmetric_three_magnet_handoff_gate_v1"
        and public_gate.get("status") == "ok"
        and public_gate.get("handoff_ready") is True,
        "four_dominant_timing_stages_recorded": list(timing)
        == [
            "source_inventory_s",
            "first_solver_s",
            "second_solver_s",
            "mcp_verification_s",
        ]
        and all(isinstance(value, (int, float)) and value >= 0.0 for value in timing.values()),
    }
    issues = [name for name, ok in checks.items() if not ok]
    return {
        "policy": "elf_magnetization_group_handoff_contract_gate_v1",
        "status": "ok" if not issues else "needs_attention",
        "checks": checks,
        "issues": issues,
        "notes": [
            "An assembled permanent-magnet mesh may depend on separately extracted magnet submodels; do not regenerate it from an incomplete script package.",
            "Keep the run log as execution authority and the field file as post-processing data, with both produced by the same fresh direct run.",
            "Publish only scrubbed cardinality, artifact-role, and physics-gate metadata; keep product paths and solved values private.",
        ],
    }
