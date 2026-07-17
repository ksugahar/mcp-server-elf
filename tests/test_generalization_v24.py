from __future__ import annotations

import json

from elf_mcp_server.force_method_profile_contract import (
    force_method_profile_contract_gate,
)
from test_generalization_v23 import _summary_v23


_PROMOTED_CASE_IDS = (
    "v24_source_force_method_profile_selection_scope_surface_nodal_result_mismatch",
    "v24_source_headless_completion_dialog_exit_lock_result_finalization_mismatch",
)


def _summary_v24():
    summary = _summary_v23()
    for index, run in enumerate(summary["runs"]):
        terminal = run["output_artifacts"][".mao"]["terminal_record"]
        job_generation = terminal["job_generation"]
        force_generation = f"force-profile-{101 + index}"
        run[
            "force_method_profile_selection_surface_nodal_frame_result_generation_identity"
        ] = {
            "job_generation": job_generation,
            "result_job_generation": job_generation,
            "force_profile_generation": force_generation,
            "method_force_profile_generation": force_generation,
            "selection_force_profile_generation": force_generation,
            "surface_force_profile_generation": force_generation,
            "nodal_force_profile_generation": force_generation,
            "frame_force_profile_generation": force_generation,
            "result_force_profile_generation": force_generation,
            "force_method": "virtual_work",
            "result_force_method": "virtual_work",
            "selection_scope_ids": [10, 11],
            "result_selection_scope_ids": [10, 11],
            "surface_ids": [101, 102, 103],
            "result_surface_ids": [101, 102, 103],
            "nodal_ids": [1001, 1002, 1003, 1004],
            "result_nodal_ids": [1001, 1002, 1003, 1004],
            "component_frame": "global_xyz",
            "result_component_frame": "global_xyz",
            "force_vector_n": [12.0, -0.5, 0.0],
            "result_force_vector_n": [12.0, -0.5, 0.0],
            "force_profile_sha256": "6" * 64,
            "result_force_profile_sha256": "6" * 64,
        }
        headless_generation = f"headless-{101 + index}"
        run[
            "headless_completion_dialog_exit_lock_log_final_artifact_generation_identity"
        ] = {
            "job_generation": job_generation,
            "result_job_generation": job_generation,
            "headless_generation": headless_generation,
            "dialog_headless_generation": headless_generation,
            "process_exit_headless_generation": headless_generation,
            "result_lock_headless_generation": headless_generation,
            "completion_log_headless_generation": headless_generation,
            "final_artifact_headless_generation": headless_generation,
            "headless": True,
            "modal_completion_dialog_shown": False,
            "process_exited": True,
            "process_exit_code": 0,
            "result_lock_present": False,
            "completion_log_marker": "calculation completed",
            "parsed_completion_log_marker": "calculation completed",
            "final_artifact_exists": True,
            "final_artifact_sha256": "7" * 64,
            "accepted_final_artifact_sha256": "7" * 64,
            "owned_process_count_after": 0,
        }
    return summary


def _gate(summary: dict) -> dict:
    return force_method_profile_contract_gate(json.dumps(summary))


def test_v24_source_positive_force_profile_and_headless_finalization_identity() -> None:
    assert _gate(_summary_v24())["status"] == "ok"


def test_v24_source_force_profile_selection_surface_nodal_result_mismatch() -> None:
    summary = _summary_v24()
    summary["runs"][0][
        "force_method_profile_selection_surface_nodal_frame_result_generation_identity"
    ].update(
        {
            "method_force_profile_generation": "force-profile-100",
            "selection_force_profile_generation": "force-profile-99",
            "surface_force_profile_generation": "force-profile-98",
            "nodal_force_profile_generation": "force-profile-97",
            "frame_force_profile_generation": "force-profile-96",
            "result_force_method": "maxwell_stress",
            "result_selection_scope_ids": [12],
            "result_surface_ids": [103, 104],
            "result_nodal_ids": [1003, 1004, 1005],
            "result_component_frame": "local_xyz",
            "result_force_vector_n": [8.0, 1.0, 0.0],
            "result_force_profile_sha256": "d" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "force_profiles_use_current_method_selection_surface_nodal_frame_and_result"
    ]


def test_v24_source_headless_completion_and_finalization_mismatch() -> None:
    summary = _summary_v24()
    summary["runs"][0][
        "headless_completion_dialog_exit_lock_log_final_artifact_generation_identity"
    ].update(
        {
            "dialog_headless_generation": "headless-100",
            "process_exit_headless_generation": "headless-99",
            "result_lock_headless_generation": "headless-98",
            "completion_log_headless_generation": "headless-97",
            "final_artifact_headless_generation": "headless-96",
            "modal_completion_dialog_shown": True,
            "process_exited": False,
            "process_exit_code": 1,
            "result_lock_present": True,
            "parsed_completion_log_marker": "calculation started",
            "final_artifact_exists": False,
            "accepted_final_artifact_sha256": "e" * 64,
            "owned_process_count_after": 1,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "headless_runs_close_dialog_process_lock_log_and_final_artifact_state"
    ]
