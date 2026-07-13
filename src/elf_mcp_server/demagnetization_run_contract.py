"""Metadata-only contract for GUI-free permanent-magnet demagnetization runs."""
from __future__ import annotations

import json
import math


_OUTPUT_ROLES = {
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}

_HISTORY_OUTPUT_ROLES = {
    ".meg": "geometry_mesh",
    ".mao": "run_log_and_history_table",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}

_HISTORY_CASE_ROLES = {
    "external_reverse_field_cycle",
    "coil_reverse_current_cycle",
    "temperature_curve_cycle",
    "precondition_then_temperature_cycle",
}


def _legacy_case_checks(case: dict) -> dict[str, bool]:
    output_roles = case.get("output_roles")
    state_min_history = case.get("state_min_history")
    if not isinstance(state_min_history, list) or len(state_min_history) < 3:
        state_min_history = []
    states = [float(value) for value in state_min_history]
    finite_states = bool(states) and all(math.isfinite(value) for value in states)
    final_convergence = float(case.get("maximum_final_convergence", math.inf))
    tolerance = float(case.get("nonlinear_tolerance", 0.0))
    return {
        "exit_zero": case.get("solver_exit_code") == 0,
        "dmeg_enabled": case.get("dmeg_enabled") is True,
        "nonlinear_limit_recorded": int(case.get("maximum_nonlinear_iterations", 0)) > 0,
        "nonlinear_tolerance_positive": math.isfinite(tolerance) and tolerance > 0.0,
        "all_steps_converged": math.isfinite(final_convergence)
        and tolerance > 0.0
        and final_convergence <= tolerance,
        "step_count_matches": int(case.get("observed_step_count", -1))
        == int(case.get("expected_step_count", -2)),
        "moment_solution_completed": case.get("end_of_moment_solution") is True,
        "no_error_markers": case.get("error_marker_count") == 0,
        "output_roles_complete": output_roles == _OUTPUT_ROLES,
        "all_outputs_fresh": case.get("all_outputs_fresh") is True,
        "state_history_bounded": finite_states and all(0.0 <= value <= 1.0 for value in states),
        "irreversible_state_observed": finite_states and min(states[1:]) < states[0],
        "state_does_not_recover": finite_states
        and all(later <= earlier + 1.0e-9 for earlier, later in zip(states, states[1:])),
    }


def _history_case_checks(case: dict) -> dict[str, bool]:
    states = case.get("states")
    if not isinstance(states, list) or len(states) < 3:
        return {"state_history_has_three_or_more_steps": False}

    state_ids: list[str] = []
    step_ids: list[int] = []
    remanence: dict[str, list[float]] = {}
    field: dict[str, list[float]] = {}
    expected_elements: tuple[int, ...] | None = None
    expected_materials: tuple[int, ...] | None = None
    identity_stable = True
    values_physical = True
    field_physical = True
    for position, state in enumerate(states):
        if not isinstance(state, dict):
            return {"state_records_are_objects": False}
        state_id = str(state.get("state_id", "")).strip()
        raw_elements = state.get("element_ids")
        raw_materials = state.get("material_ids")
        raw_remanence = state.get("remanence_ratio")
        raw_field = state.get("flux_density_T")
        if (
            not state_id
            or not isinstance(raw_elements, list)
            or not raw_elements
            or not isinstance(raw_materials, list)
            or len(raw_materials) != len(raw_elements)
            or not isinstance(raw_remanence, list)
            or len(raw_remanence) != len(raw_elements)
            or not isinstance(raw_field, list)
            or len(raw_field) != len(raw_elements)
        ):
            return {"state_record_shapes_match": False}
        elements = tuple(int(value) for value in raw_elements)
        materials = tuple(int(value) for value in raw_materials)
        values = [float(value) for value in raw_remanence]
        fields = [float(value) for value in raw_field]
        if expected_elements is None:
            expected_elements = elements
            expected_materials = materials
        else:
            identity_stable &= elements == expected_elements and materials == expected_materials
        values_physical &= all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in values)
        field_physical &= all(math.isfinite(value) and value >= 0.0 for value in fields)
        state_ids.append(state_id)
        step_ids.append(int(state.get("step", position)))
        remanence[state_id] = values
        field[state_id] = fields

    state_never_recovers = all(
        later[element] <= earlier[element] + 1.0e-9
        for earlier, later in zip(
            (remanence[state_id] for state_id in state_ids),
            (remanence[state_id] for state_id in state_ids[1:]),
        )
        for element in range(len(earlier))
    )
    blocks = case.get("history_blocks")
    if not isinstance(blocks, list) or not blocks:
        return {"history_blocks_present": False}
    state_order = {state_id: position for position, state_id in enumerate(state_ids)}
    references_ordered = True
    state_memory_respected = True
    block_expectations_explicit = True
    damage_expectation_respected = True
    field_changes_after_stress = True
    for block in blocks:
        if not isinstance(block, dict):
            return {"history_block_records_are_objects": False}
        pre_id = str(block.get("pre_state", ""))
        stress_id = str(block.get("stress_state", ""))
        unload_id = str(block.get("unloaded_state", ""))
        valid = (
            pre_id in remanence
            and stress_id in remanence
            and unload_id in remanence
            and state_order[pre_id] < state_order[stress_id] < state_order[unload_id]
        )
        references_ordered &= valid
        if not valid:
            continue
        pre = remanence[pre_id]
        stressed = remanence[stress_id]
        unloaded = remanence[unload_id]
        damage = [before - after for before, after in zip(pre, stressed)]
        state_memory_respected &= min(damage) >= -1.0e-9
        state_memory_respected &= max(
            abs(after - during) for during, after in zip(stressed, unloaded)
        ) <= 1.0e-9
        expectation = block.get("expect_additional_demagnetization")
        block_expectations_explicit &= isinstance(expectation, bool)
        if expectation is True:
            damage_expectation_respected &= max(damage) > 1.0e-3
        else:
            damage_expectation_respected &= max(abs(value) for value in damage) <= 1.0e-9
        field_changes_after_stress &= max(
            abs(after - during)
            for during, after in zip(field[stress_id], field[unload_id])
        ) > 1.0e-9

    source_commands = case.get("source_commands")
    source_commands = source_commands if isinstance(source_commands, dict) else {}
    hbcn_steps: set[int] = set()
    for row in source_commands.get("HBCN", []):
        if isinstance(row, list) and len(row) >= 2:
            hbcn_steps.add(int(row[1]))
    output_roles = case.get("output_roles")
    output_roles = output_roles if isinstance(output_roles, dict) else {}
    exit_codes = case.get("solver_exit_codes")
    exit_codes = exit_codes if isinstance(exit_codes, list) else []
    replay_max_abs = float(case.get("replay_max_abs", math.inf))
    return {
        "two_direct_solver_runs_exit_zero": len(exit_codes) >= 2
        and all(int(code) == 0 for code in exit_codes),
        "source_copy_preserved": case.get("source_copy_preserved") is True,
        "source_file_digests_complete": int(case.get("source_file_count", 0)) > 0
        and int(case.get("source_file_count", 0)) == int(case.get("source_digest_count", -1)),
        "hbrm_hbcn_dmeg_command_family_present": all(
            bool(source_commands.get(command)) for command in ("HBRM", "HBCN", "DMEG")
        ),
        "hbcn_steps_cover_state_history": hbcn_steps == set(step_ids),
        "state_ids_unique": len(state_ids) == len(set(state_ids)),
        "step_ids_strictly_increase": all(a < b for a, b in zip(step_ids, step_ids[1:])),
        "element_and_material_identity_stable": identity_stable,
        "remanence_ratio_is_physical": values_physical,
        "instantaneous_flux_density_is_physical": field_physical,
        "remanence_state_never_recovers": state_never_recovers,
        "history_block_references_ordered": references_ordered,
        "history_blocks_preserve_irreversible_memory": state_memory_respected,
        "damage_expectation_is_explicit_for_each_block": block_expectations_explicit,
        "damage_expectation_matches_each_block": damage_expectation_respected,
        "field_changes_without_state_healing": field_changes_after_stress,
        "output_roles_include_product_mesh_and_mao_history": all(
            output_roles.get(extension) == role
            for extension, role in _HISTORY_OUTPUT_ROLES.items()
        ),
        "all_outputs_fresh": case.get("all_outputs_fresh") is True,
        "two_replays_exact": int(case.get("replay_count", 0)) >= 2
        and math.isfinite(replay_max_abs)
        and 0.0 <= replay_max_abs <= 1.0e-9,
    }


def demagnetization_run_contract_gate(summary_json: str) -> dict:
    """Validate a structured run summary without opening product files or paths."""

    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    cases = summary.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")

    history_family = any(isinstance(case, dict) and "states" in case for case in cases)
    case_checks: dict[str, dict[str, bool]] = {}
    for position, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{position}] must be an object")
        case_id = str(case.get("case_id", "")).strip() or f"case-{position}"
        case_checks[case_id] = (
            _history_case_checks(case) if history_family else _legacy_case_checks(case)
        )

    flat_checks = [ok for checks in case_checks.values() for ok in checks.values()]
    case_ids = [str(case.get("case_id", "")).strip() for case in cases]
    direct_routes = {"direct_solver_exe_no_gui"}
    if history_family:
        direct_routes.add("direct_solver_exe_no_gui_using_product_mesh")
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route") in direct_routes,
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_family_recorded": summary.get("solver_family") == "magnetostatic_bem",
        "solver_version_recorded": bool(str(summary.get("solver_version", "")).strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc", "")).strip()),
        "source_copy_preserved": summary.get("source_copy_preserved") is True,
        "case_ids_unique": all(case_ids) and len(case_ids) == len(set(case_ids)),
        "case_count_matches": len(cases) == int(summary.get("expected_case_count", -1)),
        "all_case_contracts_pass": bool(flat_checks) and all(flat_checks),
    }
    if history_family:
        checks.update(
            {
                "mao_is_history_authority": summary.get("result_authority") == ".mao",
                "wl8t_history_table_recorded": summary.get("history_table") == "WL8T",
                "perm_is_irreversible_state_column": summary.get("state_column") == "PERM",
                "b_is_instantaneous_field_column": summary.get("field_column") == "B",
                "four_history_roles_present": set(case_ids) == _HISTORY_CASE_ROLES,
                "public_history_gate_passed": summary.get("public_gate_status") == "ok",
            }
        )
    return {
        "schema": (
            "elf-demagnetization-run-contract/v2"
            if history_family
            else "elf-demagnetization-run-contract/v1"
        ),
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "case_checks": case_checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "notes": [
            "the run log is the convergence and history authority; field output alone cannot prove irreversible demagnetization",
            "execute a work copy and compare source digests so product examples remain immutable",
            "WL8T B is an instantaneous field observable while PERM is the irreversible elementwise remanence state",
        ],
    }
