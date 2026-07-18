from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v34 import _summary_v34


_PROMOTED_CASE_IDS = (
    "v35_source_input_section_continuation_encoding_unit_dependent_option_schema_mismatch",
    "v35_source_bilingual_keyword_alias_section_page_release_citation_digest_mismatch",
)


def _summary_v35():
    summary = _summary_v34()
    for index, run in enumerate(summary["runs"]):
        generation = f"input-schema-{401 + index}"
        run[
            "input_section_continuation_encoding_unit_dependency_enum_release_owner_schema_identity"
        ] = {
            "input_schema_generation": generation,
            **{
                key: generation
                for key in (
                    "section_generation", "continuation_generation", "encoding_generation",
                    "unit_generation", "dependency_generation", "enum_generation",
                    "release_generation", "owner_generation", "schema_generation",
                    "response_generation",
                )
            },
            "section_order": ["model", "material", "boundary"],
            "parsed_section_order": ["model", "material", "boundary"],
            "continuation_markers": ["\\", "&"],
            "parsed_continuation_markers": ["\\", "&"],
            "text_encoding": "utf-8", "parsed_text_encoding": "utf-8",
            "length_unit": "mm", "parsed_length_unit": "mm",
            "dependent_option": "mesh_size", "parsed_dependent_option": "mesh_size",
            "dependency_expression": "automatic_mesh == false",
            "parsed_dependency_expression": "automatic_mesh == false",
            "enum_scope": "analysis.mesh", "parsed_enum_scope": "analysis.mesh",
            "available_since_release": "6.0", "parsed_available_since_release": "6.0",
            "document_owner": "input-reference/schema-401",
            "parsed_document_owner": "input-reference/schema-401",
            "schema_sha256": "5" * 64, "parsed_schema_sha256": "5" * 64,
            "public_boundary": "documentation_only",
            "resolved_public_boundary": "documentation_only",
            "response_sha256": "6" * 64, "accepted_response_sha256": "6" * 64,
        }
        generation = f"bilingual-index-{401 + index}"
        run[
            "bilingual_keyword_alias_section_page_release_scope_citation_boundary_owner_response_identity"
        ] = {
            "bilingual_index_generation": generation,
            **{
                key: generation
                for key in (
                    "alias_generation", "section_generation", "page_generation",
                    "release_generation", "scope_generation", "citation_generation",
                    "boundary_generation", "owner_generation", "response_generation",
                )
            },
            "japanese_keyword_alias": "boundary-condition-ja",
            "resolved_japanese_keyword_alias": "boundary-condition-ja",
            "english_keyword_alias": "boundary_condition",
            "resolved_english_keyword_alias": "boundary_condition",
            "document_section": "input-reference/boundary",
            "resolved_document_section": "input-reference/boundary",
            "document_page": 142, "resolved_document_page": 142,
            "document_release": "6.0", "resolved_document_release": "6.0",
            "option_scope": "model.boundary", "resolved_option_scope": "model.boundary",
            "cited_excerpt_sha256": "7" * 64,
            "resolved_cited_excerpt_sha256": "7" * 64,
            "public_boundary": "documentation_only",
            "resolved_public_boundary": "documentation_only",
            "source_owner": "documentation-index/case-401",
            "resolved_source_owner": "documentation-index/case-401",
            "response_sha256": "8" * 64, "accepted_response_sha256": "8" * 64,
        }
    return summary


def test_v35_source_positive_input_schema_and_bilingual_citation_closure():
    assert _gate(_summary_v35())["status"] == "ok"


def test_v35_source_input_section_continuation_encoding_unit_dependent_option_schema_mismatch():
    summary = _summary_v35()
    record = summary["runs"][0][
        "input_section_continuation_encoding_unit_dependency_enum_release_owner_schema_identity"
    ]
    record.update(
        {
            "section_generation": "input-schema-400",
            "encoding_generation": "input-schema-399",
            "response_generation": "input-schema-398",
            "parsed_section_order": ["boundary", "model"],
            "parsed_continuation_markers": ["?"],
            "parsed_text_encoding": "binary",
            "parsed_length_unit": "s",
            "parsed_dependent_option": "unknown_option",
            "parsed_dependency_expression": "always",
            "parsed_enum_scope": "private.solver",
            "parsed_available_since_release": "99.0",
            "parsed_document_owner": "private/old",
            "parsed_schema_sha256": "d" * 64,
            "resolved_public_boundary": "solver_internal",
            "accepted_response_sha256": "e" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "input_descriptions_use_current_sections_continuations_encoding_units_dependencies_enums_release_owner_schema_and_boundary"
    ]


def test_v35_source_bilingual_keyword_alias_section_page_release_citation_digest_mismatch():
    summary = _summary_v35()
    record = summary["runs"][0][
        "bilingual_keyword_alias_section_page_release_scope_citation_boundary_owner_response_identity"
    ]
    record.update(
        {
            "alias_generation": "bilingual-index-400",
            "citation_generation": "bilingual-index-399",
            "response_generation": "bilingual-index-398",
            "resolved_japanese_keyword_alias": "unrelated-ja",
            "resolved_english_keyword_alias": "unrelated_en",
            "resolved_document_section": "private/solver",
            "resolved_document_page": -1,
            "resolved_document_release": "99.0",
            "resolved_option_scope": "private.result",
            "resolved_cited_excerpt_sha256": "f" * 64,
            "resolved_public_boundary": "solver_internal",
            "resolved_source_owner": "private/old",
            "accepted_response_sha256": "0" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "bilingual_documentation_uses_current_aliases_section_page_release_scope_citation_boundary_owner_and_response"
    ]


def test_v35_source_rejects_self_consistent_solver_internal_citation():
    summary = _summary_v35()
    for run in summary["runs"]:
        record = run[
            "bilingual_keyword_alias_section_page_release_scope_citation_boundary_owner_response_identity"
        ]
        record["public_boundary"] = "solver_internal"
        record["resolved_public_boundary"] = "solver_internal"
    assert _gate(summary)["status"] == "needs_attention"
