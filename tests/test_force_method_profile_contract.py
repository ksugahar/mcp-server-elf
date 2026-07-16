from __future__ import annotations

import copy
import json

import pytest

from elf_mcp_server.force_method_profile_contract import (
    force_method_profile_contract_gate,
)
from elf_mcp_server.server import elf_force_method_profile_contract_gate


def _summary() -> dict:
    case_roles = {
        "element_force": "MR02_01",
        "maxwell_stress": "MR02_02",
        "combined_methods": "MR02_03",
    }
    shapes = {
        "element_force": {"FORC": 6, "FORT": 0},
        "maxwell_stress": {"FORC": 0, "FORT": 6},
        "combined_methods": {"FORC": 6, "FORT": 6},
    }
    output_roles = {
        ".meg": "geometry_mesh",
        ".mao": "run_log",
        ".mag": "field_result",
        ".mat": "matrix_state",
        ".mac": "mark_state",
    }
    runs = []
    for role, case_id in case_roles.items():
        for replay in (1, 2):
            output_artifacts = {
                suffix: {
                    "role": artifact_role,
                    "fresh": True,
                    "sha256": "b" * 64,
                    "modified_at_utc": f"2026-07-15T00:00:0{replay}+00:00",
                }
                for suffix, artifact_role in output_roles.items()
            }
            runs.append(
                {
                    "role": role,
                    "case_id": case_id,
                    "replay": replay,
                    "mesh_exit_code": 0,
                    "solver_exit_code": 0,
                    "source_copy_preserved": True,
                    "all_outputs_fresh": True,
                    "owned_process_count_after": 0,
                    "output_roles": output_roles,
                    "output_artifacts": output_artifacts,
                    "process_lifecycle": {
                        "seat_released": True,
                        "owned_solver_children_after": [],
                    },
                    "parsed_rows": shapes[role],
                }
            )
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_family": "magnetostatic_bem",
        "result_authority": ".mao TOTAL",
        "source_files": [
            {"name": f"{case_id}{suffix}", "sha256": "a" * 64}
            for case_id in case_roles.values()
            for suffix in (".mai", ".mei")
        ],
        "deck_roles": [
            {
                "role": "element_force",
                "case_id": "MR02_01",
                "forc_steps": 6,
                "fort_steps": 0,
                "selection_scope": "all_magnetic_bodies",
                "stress_surface_recorded": False,
            },
            {
                "role": "maxwell_stress",
                "case_id": "MR02_02",
                "forc_steps": 0,
                "fort_steps": 6,
                "selection_scope": "closed_stress_surface",
                "stress_surface_recorded": True,
            },
            {
                "role": "combined_methods",
                "case_id": "MR02_03",
                "forc_steps": 6,
                "fort_steps": 6,
                "selection_scope": "moving_body_only",
                "stress_surface_recorded": True,
            },
        ],
        "runs": runs,
        "replay": {
            "parsed_force_rows_exact": True,
            "binary_nonlog_outputs_exact": True,
        },
        "public_gate": {
            "policy": "magnetic_force_method_profile_gate_v1",
            "status": "ok",
        },
    }


def test_accepts_replayed_force_method_contract() -> None:
    result = force_method_profile_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(
        elf_force_method_profile_contract_gate(json.dumps(_summary()))
    )["status"] == "ok"


def test_rejects_unpinned_combined_body_selection() -> None:
    summary = copy.deepcopy(_summary())
    summary["deck_roles"][2]["selection_scope"] = "all_magnetic_bodies"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["combined_deck_pins_target_body_and_closed_surface"] is False


def test_rejects_stale_output_or_failed_public_gate() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["all_outputs_fresh"] = False
    summary["public_gate"]["status"] = "needs_attention"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["six_fresh_headless_runs_are_complete"] is False
    assert result["checks"]["public_force_method_gate_passed"] is False


def test_reports_malformed_replay_and_manifest_as_attention() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["replay"] = "not-an-integer"
    summary["source_files"] = None
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["source_manifest_names_and_digests_complete"] is False
    assert result["checks"]["two_replays_per_source_role"] is False


def test_rejects_stale_output_and_owned_process_leak_together() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["all_outputs_fresh"] = False
    summary["runs"][0]["owned_process_count_after"] = 1
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["six_fresh_headless_runs_are_complete"] is False


@pytest.mark.parametrize(
    "case_id",
    ["target_scope", "public_handoff", "solver_exit", "source_digest", "result_authority"],
)
def test_counterfactual_curriculum90_source(case_id: str) -> None:
    summary = copy.deepcopy(_summary())
    if case_id == "target_scope":
        summary["deck_roles"][2]["selection_scope"] = "all_magnetic_bodies"
    elif case_id == "public_handoff":
        summary["public_gate"]["status"] = "needs_attention"
    elif case_id == "solver_exit":
        summary["runs"][0]["solver_exit_code"] = 1
    elif case_id == "source_digest":
        summary["source_files"][0]["sha256"] = "0" * 63
    else:
        summary["result_authority"] = ".mag field"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"


def test_generalization_v3s_rejects_completion_dialog() -> None:
    summary = copy.deepcopy(_summary())
    summary["completion_dialog"] = True
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"


@pytest.mark.parametrize(
    "case_id",
    ["v4_execution_route", "v4_solver_family", "v4_parsed_replay", "v4_mesh_exit", "v4_source_copy"],
)
def test_counterfactual_curriculum90_v4_source(case_id: str) -> None:
    summary = copy.deepcopy(_summary())
    if case_id == "v4_execution_route":
        summary["execution_route"] = "interactive_gui"
    elif case_id == "v4_solver_family":
        summary["solver_family"] = "unknown"
    elif case_id == "v4_parsed_replay":
        summary["replay"]["parsed_force_rows_exact"] = False
    elif case_id == "v4_mesh_exit":
        summary["runs"][0]["mesh_exit_code"] = 1
    else:
        summary["runs"][0]["source_copy_preserved"] = False
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"


def test_generalization_v5_rejects_unpinned_source_filename() -> None:
    summary = copy.deepcopy(_summary())
    summary["source_files"][0]["name"] = "wrong.mai"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"


@pytest.mark.parametrize(
    "case_id",
    ["v6_source_parsed_row_count_disagreement", "v6_source_output_role_disagreement"],
)
def test_generalization_v6_source(case_id: str) -> None:
    summary = copy.deepcopy(_summary())
    if case_id == "v6_source_parsed_row_count_disagreement":
        summary["runs"][4]["parsed_rows"]["FORC"] = 5
    else:
        summary["runs"][0]["output_roles"][".mao"] = "field_result"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"


def test_v7_source_mao_complete_mag_stale() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["output_artifacts"][".mag"]["fresh"] = False
    summary["runs"][0]["output_artifacts"][".mag"]["modified_at_utc"] = (
        "2026-07-14T00:00:00+00:00"
    )
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["each_output_role_has_fresh_digest_bound_artifact"] is False


def test_v7_source_solver_child_survives_seat_release() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["process_lifecycle"]["owned_solver_children_after"] = [
        {"pid": 4321, "role": "solver", "alive": True}
    ]
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["seat_release_and_owned_solver_children_close"] is False
