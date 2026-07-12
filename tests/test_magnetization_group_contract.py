import copy
import json

from elf_mcp_server.magnetization_group_contract import (
    magnetization_group_handoff_contract_gate,
)
from elf_mcp_server.server import elf_magnetization_group_handoff_contract_gate


def summary() -> dict:
    run = {
        "solver_exit_code": 0,
        "solution_complete": True,
        "error_marker_count": 0,
        "source_copy_preserved": True,
        "fresh_output_suffixes": [".meg", ".mao", ".mag", ".mat", ".mac"],
        "run_log_suffix": ".mao",
        "field_result_suffix": ".mag",
        "group_ids": [1, 2, 3],
        "group_vector_counts": {"1": 16, "2": 16, "3": 16},
    }
    return {
        "execution_route": "direct_solver_preassembled_mesh_no_gui",
        "completion_dialog": False,
        "pipeline_stages": [
            "source_excitation_solve",
            "magnet_submodel_extraction",
            "air_region_geometry_merge",
            "sequential_vector_injection",
            "assembled_field_solve",
        ],
        "source_copy_preserved": True,
        "preassembled_mesh_used": True,
        "expected_group_count": 3,
        "expected_vectors_per_group": 16,
        "magnet_submodel_count": 3,
        "assembled_group_count": 3,
        "assembled_vector_count": 48,
        "invalid_shortcut_probe": {
            "attempt": "regenerate_assembled_mesh_without_required_magnet_submodels",
            "mesh_exit_code": 13,
            "solver_exit_code": 13,
            "failure_signature": "missing_mesh_book_end_after_dependency_omission",
            "rejected": True,
        },
        "runs": [run, copy.deepcopy(run)],
        "public_gate": {
            "policy": "mirror_symmetric_three_magnet_handoff_gate_v1",
            "status": "ok",
            "handoff_ready": True,
        },
        "timing": {
            "source_inventory_s": 0.02,
            "first_solver_s": 0.13,
            "second_solver_s": 0.12,
            "mcp_verification_s": 5.0,
        },
    }


def test_accepts_staged_preassembled_magnetization_handoff():
    result = magnetization_group_handoff_contract_gate(json.dumps(summary()))
    assert result["status"] == "ok"
    assert json.loads(
        elf_magnetization_group_handoff_contract_gate(json.dumps(summary()))
    )["status"] == "ok"


def test_rejects_dependency_shortcut_and_missing_field_result():
    bad = copy.deepcopy(summary())
    bad["invalid_shortcut_probe"]["rejected"] = False
    bad["runs"][1]["fresh_output_suffixes"].remove(".mag")
    result = magnetization_group_handoff_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["dependency_omission_shortcut_is_rejected"] is False
    assert result["checks"]["fresh_result_roles_are_complete"] is False


def test_rejects_group_cardinality_and_public_gate_drift():
    bad = copy.deepcopy(summary())
    bad["assembled_vector_count"] = 47
    bad["runs"][0]["group_vector_counts"]["3"] = 15
    bad["public_gate"]["status"] = "needs_attention"
    result = magnetization_group_handoff_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["group_and_vector_cardinality_are_explicit"] is False
    assert result["checks"]["fresh_group_metadata_are_complete"] is False
    assert result["checks"]["public_physics_gate_passed"] is False
