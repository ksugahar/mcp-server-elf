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
                    "solver_completed_at_utc": "2026-07-16T05:10:00Z",
                    "session_identity": {
                        "solver_session_generation": f"session-{role}-{replay}",
                        "result_open_session_generation": f"session-{role}-{replay}",
                        "session_model_generation": f"model-{role}-{replay}",
                        "opened_result_model_generation": f"model-{role}-{replay}",
                    },
                    "material_identity": {
                        "model_generation": f"model-{role}-{replay}",
                        "material_table_generation": f"material-{role}-{replay}",
                        "result_model_generation": f"model-{role}-{replay}",
                        "result_material_table_generation": f"material-{role}-{replay}",
                    },
                    "process_lifecycle": {
                        "seat_released": True,
                        "owned_solver_children_after": [],
                    },
                    "parsed_rows": shapes[role],
                }
            )
            output_artifacts[".mao"]["terminal_record"] = {
                "record_id": f"terminal-{role}-{replay}",
                "durably_flushed": True,
                "flush_completed_at_utc": "2026-07-16T05:11:00Z",
                "convergence_record": {
                    "status": "converged",
                    "solver_exit_code": 0,
                    "iteration_count": 12,
                    "final_residual_norm": 1.0e-9,
                    "terminal_record_id": f"terminal-{role}-{replay}",
                },
                "job_generation": f"job-{role}-{replay}",
                "parsed_terminal_job_generation": f"job-{role}-{replay}",
                "terminal_block_index": 1,
                "selected_terminal_block_index": 1,
            }
            runs[-1]["force_surface_identity"] = {
                "surface_mesh_generation": f"surface-mesh-{role}-{replay}",
                "orientation_sign_generation": f"surface-mesh-{role}-{replay}",
                "force_integration_surface_generation": (
                    f"surface-mesh-{role}-{replay}"
                ),
                "surface_orientation_digest": f"orientation-{role}-{replay}",
                "force_orientation_digest": f"orientation-{role}-{replay}",
                "surface_remeshed": True,
            }
            job_generation = output_artifacts[".mao"]["terminal_record"][
                "job_generation"
            ]
            model_digest = ("c" if len(runs) % 2 else "d") * 64
            runs[-1]["mao_model_identity"] = {
                "job_name": f"force-profile-{len(runs) - 1}",
                "job_generation": job_generation,
                "live_model_sha256": model_digest,
                "mao_embedded_model_sha256": model_digest,
                "mao_job_generation": job_generation,
            }
            runs[-1]["linear_motor_terminal_sequence"] = {
                "job_generation": job_generation,
                "terminal_sequence_job_generation": job_generation,
                "thrust_observable_job_generation": job_generation,
                "terminal_sequence": ["U", "V", "W"],
                "travel_axis": "x",
                "positive_travel_direction": 1,
                "thrust_axis": "x",
                "thrust_positive_direction": 1,
            }
            runs[-1]["mao_subcase_selection_identity"] = {
                "job_generation": job_generation,
                "mao_result_job_generation": job_generation,
                "available_subcase_indices": [0, 1, 2],
                "current_requested_subcase_index": 1,
                "selected_subcase_index": 1,
                "selected_subcase_job_generation": job_generation,
                "selected_subcase_output_sha256": "5" * 64,
            }
            runs[-1]["terminal_convergence_material_identity"] = {
                "job_generation": job_generation,
                "terminal_record_id": f"terminal-{role}-{replay}",
                "terminal_record_job_generation": job_generation,
                "final_material_update_generation": "nonlinear-material-14",
                "terminal_convergence_material_generation": "nonlinear-material-14",
            }
            runs[-1]["mao_record_count_trailer_identity"] = {
                "job_generation": job_generation,
                "mao_body_job_generation": job_generation,
                "mao_trailer_job_generation": job_generation,
                "parsed_body_record_count": 118,
                "declared_trailer_record_count": 118,
                "body_record_digest_sha256": "7" * 64,
                "trailer_body_digest_sha256": "7" * 64,
                "trailer_present": True,
            }
            runs[-1]["nonlinear_residual_scaled_norm_identity"] = {
                "job_generation": job_generation,
                "terminal_iteration_index": 14,
                "residual_iteration_index": 14,
                "scaling_norm_iteration_index": 14,
                "material_state_generation": "nonlinear-material-15",
                "residual_material_state_generation": "nonlinear-material-15",
                "scaling_norm_material_state_generation": "nonlinear-material-15",
                "residual_vector_generation": "residual-vector-15",
                "scaled_norm_residual_generation": "residual-vector-15",
                "scaled_residual_norm": 2.0e-8,
                "terminal_tolerance": 1.0e-6,
            }
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


def test_v8_source_mao_tail_not_fully_flushed() -> None:
    summary = copy.deepcopy(_summary())
    terminal = summary["runs"][0]["output_artifacts"][".mao"]["terminal_record"]
    terminal.update({"record_id": "", "durably_flushed": False})
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["mao_terminal_record_is_durably_flushed"] is False


def test_v8_source_result_opened_after_session_reuse() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["session_identity"]["opened_result_model_generation"] = (
        "model-previous"
    )
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["opened_result_matches_current_session_model_generation"]
        is False
    )


def test_v9_source_result_material_table_generation_mismatch() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["material_identity"][
        "result_material_table_generation"
    ] = "material-previous"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["result_material_table_matches_current_model_generation"]
        is False
    )


def test_v9_source_terminal_success_without_convergence_record() -> None:
    summary = copy.deepcopy(_summary())
    del summary["runs"][0]["output_artifacts"][".mao"]["terminal_record"][
        "convergence_record"
    ]
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["terminal_success_includes_solver_convergence_record"]
        is False
    )


def test_v10_source_mao_terminal_block_previous_job() -> None:
    summary = copy.deepcopy(_summary())
    terminal = summary["runs"][0]["output_artifacts"][".mao"][
        "terminal_record"
    ]
    terminal["parsed_terminal_job_generation"] = "job-previous"
    terminal["selected_terminal_block_index"] = 0
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["mao_terminal_block_matches_current_job_generation"]
        is False
    )


def test_v10_source_force_surface_orientation_sign_stale() -> None:
    summary = copy.deepcopy(_summary())
    surface = summary["runs"][0]["force_surface_identity"]
    surface["orientation_sign_generation"] = "surface-mesh-previous"
    surface["force_orientation_digest"] = "orientation-previous"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["force_surface_orientation_matches_current_remesh"]
        is False
    )


def test_v11_source_mao_result_live_model_digest_mismatch() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["mao_model_identity"][
        "mao_embedded_model_sha256"
    ] = "e" * 64
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["mao_result_model_digest_matches_current_live_model"]
        is False
    )


def test_v11_source_linear_motor_terminal_sequence_previous_job() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["linear_motor_terminal_sequence"].update(
        {
            "terminal_sequence_job_generation": "job-previous",
            "terminal_sequence": ["U", "W", "V"],
            "positive_travel_direction": -1,
        }
    )
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["linear_motor_terminal_sequence_matches_current_job"]
        is False
    )


def test_v12_source_mao_selected_subcase_index_previous_run() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["mao_subcase_selection_identity"].update(
        {
            "selected_subcase_index": 0,
            "selected_subcase_job_generation": "job-previous",
        }
    )
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"]["mao_selected_subcase_matches_current_run_generation"]
        is False
    )


def test_v12_source_terminal_convergence_material_update_generation_mismatch() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["terminal_convergence_material_identity"][
        "terminal_convergence_material_generation"
    ] = "nonlinear-material-13"
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"][
            "terminal_convergence_matches_final_material_update_generation"
        ]
        is False
    )


def test_v13_source_mao_record_count_trailer_generation_mismatch() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["mao_record_count_trailer_identity"].update(
        {
            "mao_trailer_job_generation": "job-previous",
            "declared_trailer_record_count": 117,
            "trailer_body_digest_sha256": "8" * 64,
        }
    )
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"][
            "mao_record_count_and_trailer_match_current_body_generation"
        ]
        is False
    )


def test_v13_source_nonlinear_residual_scaled_norm_generation_mismatch() -> None:
    summary = copy.deepcopy(_summary())
    summary["runs"][0]["nonlinear_residual_scaled_norm_identity"].update(
        {
            "scaling_norm_iteration_index": 13,
            "scaling_norm_material_state_generation": "nonlinear-material-14",
            "scaled_norm_residual_generation": "residual-vector-14",
        }
    )
    result = force_method_profile_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert (
        result["checks"][
            "nonlinear_scaled_residual_uses_current_material_iteration"
        ]
        is False
    )
