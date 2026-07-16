"""Metadata-only contract for replayed magnetic-force method profiles."""

from __future__ import annotations

import json
import re
from datetime import datetime


_CASE_ROLES = {
    "element_force": "MR02_01",
    "maxwell_stress": "MR02_02",
    "combined_methods": "MR02_03",
}
_EXPECTED_SOURCE_NAMES = {
    f"{case_id}{suffix}"
    for case_id in _CASE_ROLES.values()
    for suffix in (".mai", ".mei")
}
_OUTPUT_ROLES = {
    ".meg": "geometry_mesh",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def _output_artifacts_complete(run: dict) -> bool:
    artifacts = run.get("output_artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(_OUTPUT_ROLES):
        return False
    for suffix, expected_role in _OUTPUT_ROLES.items():
        row = artifacts.get(suffix)
        if not isinstance(row, dict):
            return False
        if not (
            row.get("role") == expected_role
            and row.get("fresh") is True
            and re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256") or ""))
            and bool(str(row.get("modified_at_utc") or "").strip())
        ):
            return False
    return True


def _process_lifecycle_closes(run: dict) -> bool:
    lifecycle = run.get("process_lifecycle")
    if not isinstance(lifecycle, dict):
        return False
    children = lifecycle.get("owned_solver_children_after")
    if not isinstance(children, list):
        return False
    alive = [row for row in children if isinstance(row, dict) and row.get("alive") is True]
    return (
        lifecycle.get("seat_released") is True
        and not alive
        and run.get("owned_process_count_after") == len(alive) == 0
    )


def _mao_terminal_record_flushed(run: dict) -> bool:
    artifacts = run.get("output_artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    mao = artifacts.get(".mao")
    mao = mao if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record")
    if terminal is None:
        return True
    if not isinstance(terminal, dict):
        return False

    def timestamp(value: object) -> float | None:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            return None

    solver_completed = timestamp(run.get("solver_completed_at_utc"))
    flush_completed = timestamp(terminal.get("flush_completed_at_utc"))
    return (
        bool(str(terminal.get("record_id", "")))
        and terminal.get("durably_flushed") is True
        and solver_completed is not None
        and flush_completed is not None
        and flush_completed >= solver_completed
    )


def _opened_result_matches_session_model(run: dict) -> bool:
    identity = run.get("session_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    solver_session = str(identity.get("solver_session_generation", ""))
    result_session = str(identity.get("result_open_session_generation", ""))
    session_model = str(identity.get("session_model_generation", ""))
    result_model = str(identity.get("opened_result_model_generation", ""))
    return (
        bool(solver_session)
        and solver_session == result_session
        and bool(session_model)
        and session_model == result_model
    )


def _source_manifest_complete(source_files: object) -> bool:
    if not isinstance(source_files, list) or len(source_files) != 6:
        return False
    names: set[str] = set()
    for row in source_files:
        if not isinstance(row, dict):
            return False
        name = str(row.get("name", ""))
        digest = str(row.get("sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            return False
        names.add(name)
    return names == _EXPECTED_SOURCE_NAMES


def force_method_profile_contract_gate(summary_json: str) -> dict:
    """Validate deck roles and GUI-free replay metadata without opening files."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    deck_roles = summary.get("deck_roles")
    if not isinstance(deck_roles, list) or len(deck_roles) != 3:
        raise ValueError("deck_roles must contain exactly three records")
    indexed_decks = {
        str(row.get("role", "")): row for row in deck_roles if isinstance(row, dict)
    }
    if set(indexed_decks) != set(_CASE_ROLES):
        raise ValueError(f"deck roles must be exactly {sorted(_CASE_ROLES)}")

    runs = summary.get("runs")
    if not isinstance(runs, list) or len(runs) != 6:
        raise ValueError("runs must contain exactly six records")

    expected_shapes = {
        "element_force": (6, 0),
        "maxwell_stress": (0, 6),
        "combined_methods": (6, 6),
    }
    role_replays: dict[str, set[int]] = {role: set() for role in _CASE_ROLES}
    run_contracts: list[bool] = []
    output_artifact_contracts: list[bool] = []
    process_lifecycle_contracts: list[bool] = []
    mao_flush_contracts: list[bool] = []
    session_model_contracts: list[bool] = []
    for run in runs:
        if not isinstance(run, dict):
            run_contracts.append(False)
            output_artifact_contracts.append(False)
            process_lifecycle_contracts.append(False)
            mao_flush_contracts.append(False)
            session_model_contracts.append(False)
            continue
        role = str(run.get("role", ""))
        parsed_rows = run.get("parsed_rows")
        parsed_rows = parsed_rows if isinstance(parsed_rows, dict) else {}
        output_roles = run.get("output_roles")
        output_roles = output_roles if isinstance(output_roles, dict) else {}
        expected_shape = expected_shapes.get(role)
        try:
            replay_id = int(run.get("replay", -1))
        except (TypeError, ValueError):
            replay_id = -1
        if role in role_replays:
            role_replays[role].add(replay_id)
        output_artifact_contracts.append(_output_artifacts_complete(run))
        process_lifecycle_contracts.append(_process_lifecycle_closes(run))
        mao_flush_contracts.append(_mao_terminal_record_flushed(run))
        session_model_contracts.append(_opened_result_matches_session_model(run))
        run_contracts.append(
            role in _CASE_ROLES
            and run.get("case_id") == _CASE_ROLES[role]
            and run.get("mesh_exit_code") == 0
            and run.get("solver_exit_code") == 0
            and run.get("source_copy_preserved") is True
            and run.get("all_outputs_fresh") is True
            and run.get("owned_process_count_after") == 0
            and output_roles == _OUTPUT_ROLES
            and expected_shape is not None
            and (parsed_rows.get("FORC"), parsed_rows.get("FORT")) == expected_shape
        )

    element_deck = indexed_decks["element_force"]
    stress_deck = indexed_decks["maxwell_stress"]
    combined_deck = indexed_decks["combined_methods"]
    replay = summary.get("replay")
    replay = replay if isinstance(replay, dict) else {}
    public_gate = summary.get("public_gate")
    public_gate = public_gate if isinstance(public_gate, dict) else {}
    source_files = summary.get("source_files")
    source_files = source_files if isinstance(source_files, list) else []
    checks = {
        "direct_mesh_and_solver_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_family_recorded": summary.get("solver_family") == "magnetostatic_bem",
        "mao_total_is_result_authority": summary.get("result_authority") == ".mao TOTAL",
        "source_manifest_names_and_digests_complete": _source_manifest_complete(
            summary.get("source_files")
        ),
        "element_deck_pins_all_body_forc_selection": element_deck.get("case_id")
        == _CASE_ROLES["element_force"]
        and element_deck.get("forc_steps") == 6
        and element_deck.get("fort_steps") == 0
        and element_deck.get("selection_scope") == "all_magnetic_bodies"
        and element_deck.get("stress_surface_recorded") is False,
        "stress_deck_pins_closed_surface_fort_selection": stress_deck.get("case_id")
        == _CASE_ROLES["maxwell_stress"]
        and stress_deck.get("forc_steps") == 0
        and stress_deck.get("fort_steps") == 6
        and stress_deck.get("selection_scope") == "closed_stress_surface"
        and stress_deck.get("stress_surface_recorded") is True,
        "combined_deck_pins_target_body_and_closed_surface": combined_deck.get("case_id")
        == _CASE_ROLES["combined_methods"]
        and combined_deck.get("forc_steps") == 6
        and combined_deck.get("fort_steps") == 6
        and combined_deck.get("selection_scope") == "moving_body_only"
        and combined_deck.get("stress_surface_recorded") is True,
        "six_fresh_headless_runs_are_complete": all(run_contracts),
        "each_output_role_has_fresh_digest_bound_artifact": all(
            output_artifact_contracts
        ),
        "seat_release_and_owned_solver_children_close": all(
            process_lifecycle_contracts
        ),
        "mao_terminal_record_is_durably_flushed": all(mao_flush_contracts),
        "opened_result_matches_current_session_model_generation": all(
            session_model_contracts
        ),
        "two_replays_per_source_role": all(
            replays == {1, 2} for replays in role_replays.values()
        ),
        "parsed_force_rows_replay_exact": replay.get("parsed_force_rows_exact") is True,
        "binary_nonlog_outputs_replay_exact": replay.get(
            "binary_nonlog_outputs_exact"
        )
        is True,
        "public_force_method_gate_passed": public_gate.get("policy")
        == "magnetic_force_method_profile_gate_v1"
        and public_gate.get("status") == "ok",
    }
    return {
        "schema": "elf-force-method-profile-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "metrics": {
            "source_file_count": len(source_files),
            "run_count": len(runs),
            "replay_count_per_role": {
                role: len(replays) for role, replays in role_replays.items()
            },
        },
        "notes": [
            "FORC and FORT profiles are comparable only when body and closed-surface selections are explicit",
            "the .mao TOTAL rows are the result authority; .mei remains an input deck",
            "a complete .mao cannot make a stale .mag fresh; bind every output digest and close owned child processes as well as the seat",
            "this public documentation contract opens no paths and exposes no solved values",
        ],
    }
