from __future__ import annotations

from test_generalization_v25 import _gate
from test_generalization_v26 import _summary_v26


def _summary_v27():
    summary = _summary_v26()
    for index, run in enumerate(summary["runs"]):
        generation = f"document-evidence-{311 + index}"
        run["document_edition_language_page_figure_table_anchor_checksum_generation_identity"] = {
            "evidence_generation": generation,
            "edition_evidence_generation": generation,
            "language_evidence_generation": generation,
            "page_evidence_generation": generation,
            "figure_evidence_generation": generation,
            "table_evidence_generation": generation,
            "anchor_evidence_generation": generation,
            "checksum_evidence_generation": generation,
            "result_evidence_generation": generation,
            "document_id": "public-manual",
            "result_document_id": "public-manual",
            "edition": "6.0",
            "result_edition": "6.0",
            "language": "en",
            "result_language": "en",
            "page_numbers": [42, 43],
            "result_page_numbers": [42, 43],
            "figure_ids": ["Fig-4.2"],
            "result_figure_ids": ["Fig-4.2"],
            "table_ids": ["Table-4.1"],
            "result_table_ids": ["Table-4.1"],
            "anchors": ["force-methods", "torque-output"],
            "result_anchors": ["force-methods", "torque-output"],
            "document_sha256": "5" * 64,
            "indexed_document_sha256": "5" * 64,
            "evidence_sha256": "6" * 64,
            "accepted_evidence_sha256": "6" * 64,
        }
        query_generation = f"public-query-{311 + index}"
        run["public_query_synonym_topic_category_version_citation_redaction_generation_identity"] = {
            "public_query_generation": query_generation,
            "synonym_public_query_generation": query_generation,
            "topic_public_query_generation": query_generation,
            "category_public_query_generation": query_generation,
            "version_public_query_generation": query_generation,
            "citation_public_query_generation": query_generation,
            "redaction_public_query_generation": query_generation,
            "result_public_query_generation": query_generation,
            "query_term": "demag force",
            "synonym_terms": ["demagnetizing force", "self force"],
            "resolved_query_term": "demag force",
            "canonical_topic": "demagnetization_force",
            "result_canonical_topic": "demagnetization_force",
            "category": "force_methods",
            "result_category": "force_methods",
            "document_version": "6.0",
            "result_document_version": "6.0",
            "citation_allowlist": ["doc-6.0-force-methods", "doc-6.0-torque-output"],
            "returned_citation_ids": ["doc-6.0-force-methods"],
            "redacted_field_names": ["local_path", "license_key", "api_token"],
            "result_redacted_field_names": ["local_path", "license_key", "api_token"],
            "redaction_applied": True,
            "sensitive_fields_present": [],
            "query_sha256": "7" * 64,
            "result_query_sha256": "7" * 64,
        }
    return summary


def test_v27_source_positive_document_evidence_and_public_query_citation_identity():
    assert _gate(_summary_v27())["status"] == "ok"


def test_v27_source_document_edition_language_page_figure_table_anchor_checksum_mismatch():
    summary = _summary_v27()
    summary["runs"][0][
        "document_edition_language_page_figure_table_anchor_checksum_generation_identity"
    ].update({
        "edition_evidence_generation": "document-evidence-310",
        "page_evidence_generation": "document-evidence-309",
        "checksum_evidence_generation": "document-evidence-308",
        "result_document_id": "old-manual",
        "result_edition": "5.2",
        "result_language": "ja",
        "result_page_numbers": [41, 44],
        "result_figure_ids": ["Fig-3.1"],
        "result_table_ids": ["Table-3.2"],
        "result_anchors": ["internal-force"],
        "indexed_document_sha256": "c" * 64,
        "accepted_evidence_sha256": "d" * 64,
    })
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "document_evidence_uses_current_edition_language_pages_figures_tables_anchors_and_checksums"
    ]


def test_v27_source_public_query_synonym_topic_category_version_citation_redaction_mismatch():
    summary = _summary_v27()
    summary["runs"][0][
        "public_query_synonym_topic_category_version_citation_redaction_generation_identity"
    ].update({
        "synonym_public_query_generation": "public-query-310",
        "topic_public_query_generation": "public-query-309",
        "citation_public_query_generation": "public-query-308",
        "resolved_query_term": "license path",
        "result_canonical_topic": "internal_paths",
        "result_category": "private_runtime",
        "result_document_version": "5.2",
        "returned_citation_ids": ["private-run-log"],
        "result_redacted_field_names": [],
        "redaction_applied": False,
        "sensitive_fields_present": ["api_token", "local_path"],
        "result_query_sha256": "e" * 64,
    })
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "public_queries_use_current_synonyms_topics_categories_versions_citations_and_redaction"
    ]
