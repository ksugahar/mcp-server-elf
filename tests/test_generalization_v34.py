from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v33 import _summary_v33


_PROMOTED_CASE_IDS = (
    "v34_source_mao_table_graph_axis_unit_case_solver_version_export_digest_mismatch",
    "v34_source_document_option_enum_default_version_availability_example_hash_mismatch",
)


def _summary_v34():
    summary = _summary_v33()
    for index, run in enumerate(summary["runs"]):
        generation = f"mao-result-view-{381 + index}"
        run[
            "mao_table_graph_axis_unit_case_solver_version_timestamp_export_owner_digest_identity"
        ] = {
            "mao_view_generation": generation,
            **{
                key: generation
                for key in (
                    "table_generation",
                    "graph_generation",
                    "x_axis_generation",
                    "y_axis_generation",
                    "case_generation",
                    "solver_generation",
                    "timestamp_generation",
                    "export_generation",
                    "owner_generation",
                    "digest_generation",
                    "result_generation",
                )
            },
            "table_id": "table-381",
            "parsed_table_id": "table-381",
            "graph_id": "graph-381",
            "parsed_graph_id": "graph-381",
            "x_axis_name": "position",
            "parsed_x_axis_name": "position",
            "x_axis_unit": "mm",
            "parsed_x_axis_unit": "mm",
            "y_axis_name": "force",
            "parsed_y_axis_name": "force",
            "y_axis_unit": "N",
            "parsed_y_axis_unit": "N",
            "case_row": ["case-381", 1.0, 25.0],
            "parsed_case_row": ["case-381", 1.0, 25.0],
            "solver_version": "6.0.0",
            "parsed_solver_version": "6.0.0",
            "exported_at_utc": "2026-07-18T01:02:03Z",
            "parsed_exported_at_utc": "2026-07-18T01:02:03Z",
            "export_generation_id": "export-381",
            "parsed_export_generation_id": "export-381",
            "source_owner": "result/case-381",
            "parsed_source_owner": "result/case-381",
            "artifact_sha256": "6" * 64,
            "parsed_artifact_sha256": "6" * 64,
            "response_sha256": "7" * 64,
            "accepted_response_sha256": "7" * 64,
        }
        generation = f"document-option-{381 + index}"
        run[
            "document_option_enum_default_version_scope_example_revision_boundary_response_identity"
        ] = {
            "document_option_generation": generation,
            **{
                key: generation
                for key in (
                    "option_generation",
                    "enum_generation",
                    "default_generation",
                    "version_generation",
                    "scope_generation",
                    "example_generation",
                    "revision_generation",
                    "boundary_generation",
                    "response_generation",
                )
            },
            "option_name": "force_method",
            "resolved_option_name": "force_method",
            "enum_members": ["maxwell", "virtual_work", "nodal"],
            "resolved_enum_members": ["maxwell", "virtual_work", "nodal"],
            "default_value": "virtual_work",
            "resolved_default_value": "virtual_work",
            "available_since_version": "6.0",
            "resolved_available_since_version": "6.0",
            "argument_scope": "analysis.force",
            "resolved_argument_scope": "analysis.force",
            "documented_example_sha256": "8" * 64,
            "resolved_documented_example_sha256": "8" * 64,
            "documentation_revision": "manual-381",
            "resolved_documentation_revision": "manual-381",
            "public_boundary": "documentation_only",
            "resolved_public_boundary": "documentation_only",
            "response_sha256": "9" * 64,
            "accepted_response_sha256": "9" * 64,
        }
    return summary


def test_v34_source_positive_mao_result_view_and_document_option_closure():
    assert _gate(_summary_v34())["status"] == "ok"


def test_v34_source_mao_table_graph_axis_unit_case_solver_version_export_digest_mismatch():
    summary = _summary_v34()
    record = summary["runs"][0][
        "mao_table_graph_axis_unit_case_solver_version_timestamp_export_owner_digest_identity"
    ]
    record.update(
        {
            "table_generation": "mao-result-view-380",
            "export_generation": "mao-result-view-379",
            "result_generation": "mao-result-view-378",
            "parsed_table_id": "table-old",
            "parsed_graph_id": "graph-old",
            "parsed_x_axis_name": "time",
            "parsed_x_axis_unit": "s",
            "parsed_y_axis_name": "torque",
            "parsed_y_axis_unit": "kg",
            "parsed_case_row": ["case-old", -1.0, -25.0],
            "parsed_solver_version": "5.0.0",
            "parsed_exported_at_utc": "2025-01-01T00:00:00Z",
            "parsed_export_generation_id": "export-old",
            "parsed_source_owner": "result/old",
            "parsed_artifact_sha256": "f" * 64,
            "accepted_response_sha256": "0" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mao_result_views_use_current_table_graph_axes_units_case_solver_timestamp_export_owner_and_digests"
    ]


def test_v34_source_document_option_enum_default_version_availability_example_hash_mismatch():
    summary = _summary_v34()
    record = summary["runs"][0][
        "document_option_enum_default_version_scope_example_revision_boundary_response_identity"
    ]
    record.update(
        {
            "enum_generation": "document-option-380",
            "version_generation": "document-option-379",
            "response_generation": "document-option-378",
            "resolved_option_name": "unknown_option",
            "resolved_enum_members": ["deprecated", "unsafe"],
            "resolved_default_value": "deprecated",
            "resolved_available_since_version": "99.0",
            "resolved_argument_scope": "private.solver",
            "resolved_documented_example_sha256": "1" * 64,
            "resolved_documentation_revision": "manual-old",
            "resolved_public_boundary": "solver_internal",
            "accepted_response_sha256": "2" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "document_options_use_current_enum_default_version_scope_example_revision_public_boundary_and_response"
    ]


def test_v34_source_rejects_self_consistent_force_axis_with_mass_unit():
    summary = _summary_v34()
    for run in summary["runs"]:
        record = run[
            "mao_table_graph_axis_unit_case_solver_version_timestamp_export_owner_digest_identity"
        ]
        record["y_axis_unit"] = "kg"
        record["parsed_y_axis_unit"] = "kg"
    assert _gate(summary)["status"] == "needs_attention"


def test_v34_source_rejects_self_consistent_default_outside_enum():
    summary = _summary_v34()
    for run in summary["runs"]:
        record = run[
            "document_option_enum_default_version_scope_example_revision_boundary_response_identity"
        ]
        record["default_value"] = "unsupported"
        record["resolved_default_value"] = "unsupported"
    assert _gate(summary)["status"] == "needs_attention"
