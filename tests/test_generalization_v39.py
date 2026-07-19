from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v38 import _summary_v38


_PROMOTED_CASE_IDS = (
    "v39_source_mao_result_table_variable_unit_step_sort_owner_file_mismatch",
    "v39_source_import_region_material_boundary_remap_mesh_generation_owner_mismatch",
)

_TABLE_KEY = "result_table_variable_unit_step_sort_complex_owner_file_response_identity"
_IMPORT_KEY = (
    "import_region_material_boundary_element_mesh_model_source_result_identity"
)


def _summary_v39() -> dict:
    summary = _summary_v38()
    for index, run in enumerate(summary["runs"]):
        generation = f"result-table-{271 + index}"
        run[_TABLE_KEY] = {
            "table_generation": generation,
            **{
                key: generation
                for key in (
                    "variable_generation",
                    "unit_generation",
                    "step_generation",
                    "sort_generation",
                    "complex_generation",
                    "owner_generation",
                    "file_generation",
                    "response_generation",
                )
            },
            "variable_name": "Torque",
            "resolved_variable_name": "Torque",
            "value_unit": "N*m",
            "resolved_value_unit": "N*m",
            "step_keys": ["angle=0deg", "angle=15deg", "angle=30deg"],
            "resolved_step_keys": ["angle=0deg", "angle=15deg", "angle=30deg"],
            "row_order": [0, 1, 2],
            "resolved_row_order": [0, 1, 2],
            "complex_value_convention": "real_imag_columns",
            "resolved_complex_value_convention": "real_imag_columns",
            "analysis_owner": "analysis:table-271",
            "resolved_analysis_owner": "analysis:table-271",
            "result_file_generation": "result-file-271",
            "resolved_result_file_generation": "result-file-271",
            "table_response_sha256": "3" * 64,
            "accepted_table_response_sha256": "3" * 64,
        }

        generation = f"import-remap-{271 + index}"
        run[_IMPORT_KEY] = {
            "import_generation": generation,
            **{
                key: generation
                for key in (
                    "region_generation",
                    "material_generation",
                    "boundary_generation",
                    "element_generation",
                    "mesh_lineage_generation",
                    "owner_generation",
                    "source_generation",
                    "result_generation",
                )
            },
            "region_ids": [1, 2, 3],
            "resolved_region_ids": [1, 2, 3],
            "material_assignments": {"1": "air", "2": "steel", "3": "magnet"},
            "resolved_material_assignments": {
                "1": "air",
                "2": "steel",
                "3": "magnet",
            },
            "boundary_remap": {"10": "outer", "11": "symmetry"},
            "resolved_boundary_remap": {"10": "outer", "11": "symmetry"},
            "element_order": 2,
            "resolved_element_order": 2,
            "mesh_generation": "mesh-271",
            "resolved_mesh_generation": "mesh-271",
            "model_owner": "model:import-271",
            "resolved_model_owner": "model:import-271",
            "source_sha256": "4" * 64,
            "resolved_source_sha256": "4" * 64,
            "result_sha256": "5" * 64,
            "accepted_result_sha256": "5" * 64,
        }
    return summary


def test_v39_source_positive_result_table_and_import_remap_closure() -> None:
    assert _gate(_summary_v39())["status"] == "ok"


def test_v39_source_mao_result_table_variable_unit_step_sort_owner_file_mismatch() -> None:
    summary = _summary_v39()
    row = summary["runs"][0][_TABLE_KEY]
    row.update(
        {
            "unit_generation": "result-table-270",
            "file_generation": "result-table-269",
            "response_generation": "result-table-268",
            "resolved_variable_name": "Flux",
            "resolved_value_unit": "T",
            "resolved_step_keys": ["old"],
            "resolved_row_order": [2, 1, 0],
            "resolved_complex_value_convention": "magnitude_phase",
            "resolved_analysis_owner": "stale:analysis",
            "resolved_result_file_generation": "result-file-old",
            "accepted_table_response_sha256": "c" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "result_tables_use_current_variable_units_steps_order_complex_convention_owner_file_and_response"
    ]


def test_v39_source_import_region_material_boundary_remap_mesh_generation_owner_mismatch() -> None:
    summary = _summary_v39()
    row = summary["runs"][0][_IMPORT_KEY]
    row.update(
        {
            "region_generation": "import-remap-270",
            "mesh_lineage_generation": "import-remap-269",
            "result_generation": "import-remap-268",
            "resolved_region_ids": [1, 99],
            "resolved_material_assignments": {"1": "wrong"},
            "resolved_boundary_remap": {"10": "old"},
            "resolved_element_order": 1,
            "resolved_mesh_generation": "mesh-old",
            "resolved_model_owner": "stale:model",
            "resolved_source_sha256": "d" * 64,
            "accepted_result_sha256": "e" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "imports_preserve_region_material_boundary_element_mesh_model_source_and_result_lineage"
    ]


def test_v39_source_rejects_self_consistent_wrong_complex_convention() -> None:
    summary = _summary_v39()
    for run in summary["runs"]:
        row = run[_TABLE_KEY]
        row["complex_value_convention"] = "magnitude_phase"
        row["resolved_complex_value_convention"] = "magnitude_phase"
    assert _gate(summary)["status"] == "needs_attention"


def test_v39_source_rejects_self_consistent_incomplete_material_map() -> None:
    summary = _summary_v39()
    for run in summary["runs"]:
        row = run[_IMPORT_KEY]
        row["material_assignments"] = {"1": "air", "2": "steel"}
        row["resolved_material_assignments"] = {"1": "air", "2": "steel"}
    assert _gate(summary)["status"] == "needs_attention"
