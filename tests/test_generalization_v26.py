from __future__ import annotations

from test_generalization_v25 import _gate, _summary_v25


def _summary_v26():
    summary = _summary_v25()
    for index, run in enumerate(summary["runs"]):
        generation = f"doc-index-{301 + index}"
        run["document_index_release_section_anchor_topic_checksum_generation_identity"] = {
            "index_generation": generation, "release_index_generation": generation,
            "section_index_generation": generation, "anchor_index_generation": generation,
            "topic_index_generation": generation, "checksum_index_generation": generation,
            "result_index_generation": generation, "document_release": "6.0",
            "result_document_release": "6.0", "section_ids": ["force", "torque", "maglev"],
            "result_section_ids": ["force", "torque", "maglev"],
            "section_anchors": ["force-methods", "torque-output", "magnetic-levitation"],
            "result_section_anchors": ["force-methods", "torque-output", "magnetic-levitation"],
            "topic_ids": ["weighted-stress", "virtual-work", "cogging-torque"],
            "result_topic_ids": ["weighted-stress", "virtual-work", "cogging-torque"],
            "document_sha256": "5" * 64, "indexed_document_sha256": "5" * 64,
            "index_sha256": "6" * 64, "result_index_sha256": "6" * 64,
        }
        query_generation = f"query-{301 + index}"
        run["query_category_schema_doc_version_observable_redaction_generation_identity"] = {
            "query_generation": query_generation, "category_query_generation": query_generation,
            "schema_query_generation": query_generation, "document_query_generation": query_generation,
            "allowlist_query_generation": query_generation, "redaction_query_generation": query_generation,
            "result_query_generation": query_generation, "category": "force_methods",
            "result_category": "force_methods", "query_schema": "elf-public-query/v1",
            "result_query_schema": "elf-public-query/v1", "document_version": "6.0",
            "result_document_version": "6.0",
            "observable_allowlist": ["force_vector_n", "torque_n_m", "method_name"],
            "returned_observable_keys": ["force_vector_n", "method_name"],
            "redacted_field_names": ["local_path", "license_key", "api_token"],
            "result_redacted_field_names": ["local_path", "license_key", "api_token"],
            "redaction_applied": True, "sensitive_fields_present": [],
            "result_sha256": "7" * 64, "accepted_result_sha256": "7" * 64,
        }
    return summary


def test_v26_source_positive_document_index_and_public_query_identity():
    assert _gate(_summary_v26())["status"] == "ok"


def test_v26_source_document_index_release_section_anchor_topic_checksum_generation_mismatch():
    summary = _summary_v26()
    summary["runs"][0]["document_index_release_section_anchor_topic_checksum_generation_identity"].update({
        "release_index_generation": "doc-index-300", "result_document_release": "5.2",
        "result_section_ids": ["force", "maglev-old"],
        "result_section_anchors": ["force-old", "magnetic-levitation"],
        "result_topic_ids": ["maxwell-contour", "cogging-torque"],
        "indexed_document_sha256": "b" * 64, "result_index_sha256": "c" * 64})
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"]["document_index_uses_current_release_sections_anchors_topics_checksums_and_generation"]


def test_v26_source_query_category_schema_doc_version_observable_redaction_generation_mismatch():
    summary = _summary_v26()
    summary["runs"][0]["query_category_schema_doc_version_observable_redaction_generation_identity"].update({
        "category_query_generation": "query-300", "result_category": "internal_paths",
        "result_query_schema": "unrestricted-json/v1", "result_document_version": "5.2",
        "returned_observable_keys": ["force_vector_n", "api_token", "local_path"],
        "result_redacted_field_names": [], "redaction_applied": False,
        "sensitive_fields_present": ["api_token", "local_path"]})
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"]["public_queries_use_current_category_schema_document_allowlist_redaction_and_result"]
