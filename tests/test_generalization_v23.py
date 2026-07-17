from __future__ import annotations

import json

from elf_mcp_server.force_method_profile_contract import (
    force_method_profile_contract_gate,
)
from test_force_method_profile_contract import _summary_v22


def _summary_v23():
    summary = _summary_v22()
    for index, run in enumerate(summary["runs"]):
        terminal = run["output_artifacts"][".mao"]["terminal_record"]
        job_generation = terminal["job_generation"]
        case_generation = f"mao-case-{51 + index}"
        run["mao_case_model_version_calculation_revision_generation_identity"] = {
            "job_generation": job_generation,
            "result_job_generation": job_generation,
            "case_generation": case_generation,
            "model_case_generation": case_generation,
            "product_version_case_generation": case_generation,
            "calculation_revision_case_generation": case_generation,
            "completion_case_generation": case_generation,
            "case_model_sha256": "3" * 64,
            "result_case_model_sha256": "3" * 64,
            "product_version": "6.0.0",
            "result_product_version": "6.0.0",
            "calculation_revision": "calc-r51",
            "result_calculation_revision": "calc-r51",
            "result_complete": True,
            "parsed_result_complete": True,
            "mao_case_table_sha256": "4" * 64,
            "parsed_mao_case_table_sha256": "4" * 64,
        }
        solve_generation = f"mesh-result-{51 + index}"
        run["mesh_result_entity_count_material_map_solve_generation_identity"] = {
            "job_generation": job_generation,
            "result_job_generation": job_generation,
            "solve_generation": solve_generation,
            "mesh_entity_solve_generation": solve_generation,
            "result_entity_solve_generation": solve_generation,
            "material_map_solve_generation": solve_generation,
            "coordinate_frame_solve_generation": solve_generation,
            "entity_counts": {"nodes": 1200, "elements": 640, "regions": 3},
            "result_entity_counts": {"nodes": 1200, "elements": 640, "regions": 3},
            "material_region_map": [[1, 101], [2, 102], [3, 103]],
            "result_material_region_map": [[1, 101], [2, 102], [3, 103]],
            "coordinate_frame": "global_xyz",
            "result_coordinate_frame": "global_xyz",
            "mesh_sha256": "5" * 64,
            "result_mesh_sha256": "5" * 64,
            "result_table_sha256": "6" * 64,
            "parsed_result_table_sha256": "6" * 64,
        }
    return summary


def _gate(summary: dict) -> dict:
    return force_method_profile_contract_gate(json.dumps(summary))


def test_v23_source_positive_mao_case_and_mesh_result_identity() -> None:
    assert _gate(_summary_v23())["status"] == "ok"


def test_v23_source_mao_case_model_version_calculation_revision_generation_mismatch() -> None:
    summary = _summary_v23()
    summary["runs"][0][
        "mao_case_model_version_calculation_revision_generation_identity"
    ].update(
        {
            "model_case_generation": "mao-case-50",
            "product_version_case_generation": "mao-case-49",
            "calculation_revision_case_generation": "mao-case-48",
            "completion_case_generation": "mao-case-47",
            "result_case_model_sha256": "c" * 64,
            "result_product_version": "5.9.0",
            "result_calculation_revision": "calc-r47",
            "parsed_result_complete": False,
            "parsed_mao_case_table_sha256": "d" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mao_results_use_current_model_version_revision_and_completion"
    ]


def test_v23_source_mesh_result_entity_count_material_map_solve_generation_mismatch() -> None:
    summary = _summary_v23()
    summary["runs"][0][
        "mesh_result_entity_count_material_map_solve_generation_identity"
    ].update(
        {
            "mesh_entity_solve_generation": "mesh-result-50",
            "result_entity_solve_generation": "mesh-result-49",
            "material_map_solve_generation": "mesh-result-48",
            "coordinate_frame_solve_generation": "mesh-result-47",
            "result_entity_counts": {"nodes": 1198, "elements": 638, "regions": 4},
            "result_material_region_map": [[1, 101], [2, 103], [4, 104]],
            "result_coordinate_frame": "rotor_dq",
            "result_mesh_sha256": "e" * 64,
            "parsed_result_table_sha256": "f" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mesh_results_use_current_entity_counts_material_map_and_frame"
    ]
