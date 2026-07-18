from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v36 import _summary_v36


_PROMOTED_CASE_IDS = (
    "v37_source_output_mao_section_record_count_unit_case_iteration_owner_mismatch",
    "v37_source_document_table_interpolation_axis_unit_release_row_owner_response_mismatch",
)


def _summary_v37():
    summary = _summary_v36()
    for index, run in enumerate(summary["runs"]):
        generation = f"mao-output-{246 + index}"
        run["mao_output_section_record_unit_case_iteration_owner_input_output_digest_identity"] = {
            "mao_generation": generation,
            **{key: generation for key in (
                "section_generation", "record_generation", "unit_generation", "case_generation",
                "iteration_generation", "owner_generation", "input_generation", "output_generation",
                "response_generation")},
            "output_extension": ".mao", "parsed_output_extension": ".mao",
            "section_name": "ForceSummary", "parsed_section_name": "ForceSummary",
            "record_count": 3, "parsed_record_count": 3,
            "unit_convention": ["N", "N*m"], "parsed_unit_convention": ["N", "N*m"],
            "analysis_case": "case:nominal", "parsed_analysis_case": "case:nominal",
            "nonlinear_iteration": 5, "parsed_nonlinear_iteration": 5,
            "run_owner": "run/mao-246", "parsed_run_owner": "run/mao-246",
            "input_sha256": "3" * 64, "parsed_input_sha256": "3" * 64,
            "output_sha256": "4" * 64, "parsed_output_sha256": "4" * 64,
        }
        generation = f"document-table-{246 + index}"
        run["document_table_interpolation_axis_order_row_column_unit_release_selected_row_owner_citation_response_identity"] = {
            "table_generation": generation,
            **{key: generation for key in (
                "axis_generation", "order_generation", "unit_generation", "release_generation",
                "row_generation", "owner_generation", "citation_generation", "response_generation")},
            "interpolation_axis": "frequency_hz", "resolved_interpolation_axis": "frequency_hz",
            "interpolation_order": "linear", "resolved_interpolation_order": "linear",
            "row_unit": "Hz", "resolved_row_unit": "Hz",
            "column_unit": "N/m", "resolved_column_unit": "N/m",
            "document_release": "6.0", "resolved_document_release": "6.0",
            "release_applicability": "6.x", "resolved_release_applicability": "6.x",
            "selected_row": [["frequency_hz", 100.0], ["stiffness_n_m", 10000.0]],
            "resolved_selected_row": [["frequency_hz", 100.0], ["stiffness_n_m", 10000.0]],
            "document_owner": "documentation/table-246", "resolved_document_owner": "documentation/table-246",
            "citation_sha256": "5" * 64, "resolved_citation_sha256": "5" * 64,
            "response_sha256": "6" * 64, "accepted_response_sha256": "6" * 64,
        }
    return summary


def test_v37_source_positive_mao_output_and_document_table_closure():
    assert _gate(_summary_v37())["status"] == "ok"


def test_v37_source_output_mao_section_record_count_unit_case_iteration_owner_mismatch():
    summary = _summary_v37()
    row = summary["runs"][0]["mao_output_section_record_unit_case_iteration_owner_input_output_digest_identity"]
    row.update({"section_generation": "mao-output-245", "case_generation": "mao-output-244",
                "response_generation": "mao-output-243", "parsed_output_extension": ".mei",
                "parsed_section_name": "OldSection", "parsed_record_count": -1,
                "parsed_unit_convention": ["kg", "s"], "parsed_analysis_case": "case:old",
                "parsed_nonlinear_iteration": -1, "parsed_run_owner": "stale/run",
                "parsed_input_sha256": "c" * 64, "parsed_output_sha256": "d" * 64})
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"]["mao_outputs_use_current_section_records_units_case_iteration_owner_input_and_output_digests"]


def test_v37_source_document_table_interpolation_axis_unit_release_row_owner_response_mismatch():
    summary = _summary_v37()
    row = summary["runs"][0]["document_table_interpolation_axis_order_row_column_unit_release_selected_row_owner_citation_response_identity"]
    row.update({"axis_generation": "document-table-245", "release_generation": "document-table-244",
                "response_generation": "document-table-243", "resolved_interpolation_axis": "temperature_c",
                "resolved_interpolation_order": "cubic", "resolved_row_unit": "s",
                "resolved_column_unit": "kg", "resolved_document_release": "99.0",
                "resolved_release_applicability": "internal", "resolved_selected_row": [["old", -1.0]],
                "resolved_document_owner": "private/old", "resolved_citation_sha256": "e" * 64,
                "accepted_response_sha256": "f" * 64})
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"]["document_tables_use_current_axis_order_units_release_row_owner_citation_and_response"]


def test_v37_source_rejects_self_consistent_wrong_output_extension():
    summary = _summary_v37()
    for run in summary["runs"]:
        row = run["mao_output_section_record_unit_case_iteration_owner_input_output_digest_identity"]
        row["output_extension"] = row["parsed_output_extension"] = ".mei"
    assert _gate(summary)["status"] == "needs_attention"


def test_v37_source_rejects_self_consistent_private_document_owner():
    summary = _summary_v37()
    for run in summary["runs"]:
        row = run["document_table_interpolation_axis_order_row_column_unit_release_selected_row_owner_citation_response_identity"]
        row["document_owner"] = row["resolved_document_owner"] = "private/table"
    assert _gate(summary)["status"] == "needs_attention"
