from __future__ import annotations

from test_generalization_v25 import _gate
from test_generalization_v27 import _summary_v27


def _summary_v28():
    summary = _summary_v27()
    for index, run in enumerate(summary["runs"]):
        glossary_generation = f"glossary-evidence-{321 + index}"
        run[
            "document_glossary_alias_command_category_version_anchor_redaction_digest_generation_identity"
        ] = {
            "glossary_generation": glossary_generation,
            "alias_glossary_generation": glossary_generation,
            "category_glossary_generation": glossary_generation,
            "version_glossary_generation": glossary_generation,
            "anchor_glossary_generation": glossary_generation,
            "redaction_glossary_generation": glossary_generation,
            "document_glossary_generation": glossary_generation,
            "result_glossary_generation": glossary_generation,
            "glossary_term": "force calculation",
            "result_glossary_term": "force calculation",
            "alias_terms": ["force method", "virtual work"],
            "resolved_alias_terms": ["force method", "virtual work"],
            "command_category": "postprocessing-force",
            "result_command_category": "postprocessing-force",
            "document_version": "6.0",
            "result_document_version": "6.0",
            "section_anchor": "force-methods",
            "result_section_anchor": "force-methods",
            "redacted_field_names": ["local_path", "license_key", "api_token"],
            "result_redacted_field_names": ["local_path", "license_key", "api_token"],
            "redaction_applied": True,
            "sensitive_fields_present": [],
            "document_sha256": "6" * 64,
            "indexed_document_sha256": "6" * 64,
            "response_sha256": "7" * 64,
            "accepted_response_sha256": "7" * 64,
        }
        bibliography_generation = f"bibliography-evidence-{321 + index}"
        run[
            "bibliography_citation_doi_edition_page_figure_allowlist_checksum_generation_identity"
        ] = {
            "bibliography_generation": bibliography_generation,
            "citation_bibliography_generation": bibliography_generation,
            "doi_bibliography_generation": bibliography_generation,
            "edition_bibliography_generation": bibliography_generation,
            "page_bibliography_generation": bibliography_generation,
            "figure_bibliography_generation": bibliography_generation,
            "allowlist_bibliography_generation": bibliography_generation,
            "checksum_bibliography_generation": bibliography_generation,
            "result_bibliography_generation": bibliography_generation,
            "bibliography_id": "public-reference-321",
            "result_bibliography_id": "public-reference-321",
            "citation_text": "Public force-method reference, second edition",
            "result_citation_text": "Public force-method reference, second edition",
            "doi": "10.1000/example.321",
            "result_doi": "10.1000/example.321",
            "edition": "2",
            "result_edition": "2",
            "page_numbers": [100, 101],
            "result_page_numbers": [100, 101],
            "figure_ids": ["Fig-5"],
            "result_figure_ids": ["Fig-5"],
            "citation_allowlist": ["public-reference-321"],
            "returned_citation_ids": ["public-reference-321"],
            "source_sha256": "8" * 64,
            "indexed_source_sha256": "8" * 64,
            "evidence_sha256": "9" * 64,
            "accepted_evidence_sha256": "9" * 64,
        }
    return summary


def test_v28_source_positive_glossary_and_bibliography_identities():
    assert _gate(_summary_v28())["status"] == "ok"


def test_v28_source_document_glossary_alias_command_category_version_anchor_redaction_digest_mismatch():
    summary = _summary_v28()
    identity = summary["runs"][0][
        "document_glossary_alias_command_category_version_anchor_redaction_digest_generation_identity"
    ]
    identity.update(
        {
            "alias_glossary_generation": "glossary-evidence-320",
            "version_glossary_generation": "glossary-evidence-319",
            "resolved_alias_terms": ["license command"],
            "result_command_category": "private-runtime",
            "result_document_version": "5.2",
            "result_section_anchor": "internal-license-path",
            "result_redacted_field_names": [],
            "redaction_applied": False,
            "sensitive_fields_present": ["api_token", "local_path"],
            "indexed_document_sha256": "f" * 64,
            "accepted_response_sha256": "a" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "document_glossary_uses_current_aliases_categories_versions_anchors_redaction_and_digests"
    ]


def test_v28_source_bibliography_citation_doi_edition_page_figure_allowlist_checksum_mismatch():
    summary = _summary_v28()
    identity = summary["runs"][0][
        "bibliography_citation_doi_edition_page_figure_allowlist_checksum_generation_identity"
    ]
    identity.update(
        {
            "doi_bibliography_generation": "bibliography-evidence-320",
            "allowlist_bibliography_generation": "bibliography-evidence-319",
            "result_bibliography_id": "private-reference",
            "result_citation_text": "Unlisted internal note",
            "result_doi": "10.1000/old",
            "result_edition": "1",
            "result_page_numbers": [99],
            "result_figure_ids": ["Fig-private"],
            "returned_citation_ids": ["private-reference"],
            "indexed_source_sha256": "b" * 64,
            "accepted_evidence_sha256": "c" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "bibliography_evidence_uses_current_citation_doi_edition_pages_figures_allowlist_and_checksums"
    ]
