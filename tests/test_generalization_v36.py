from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v35 import _summary_v35


_PROMOTED_CASE_IDS = (
    "v36_source_document_equation_symbol_unit_sign_section_release_citation_mismatch",
    "v36_source_input_region_material_source_boundary_numbering_continuation_mismatch",
)


def _summary_v36():
    summary = _summary_v35()
    for index, run in enumerate(summary["runs"]):
        generation = f"equation-doc-{402 + index}"
        run[
            "document_equation_symbol_unit_sign_section_release_citation_owner_response_identity"
        ] = {
            "equation_generation": generation,
            **{
                key: generation
                for key in (
                    "symbol_generation", "unit_generation", "sign_generation",
                    "section_generation", "release_generation", "citation_generation",
                    "owner_generation", "response_generation",
                )
            },
            "equation_id": "magnetostatic-boundary-relation",
            "resolved_equation_id": "magnetostatic-boundary-relation",
            "symbols": ["B", "H", "mu0"],
            "resolved_symbols": ["B", "H", "mu0"],
            "symbol_units": [["B", "T"], ["H", "A/m"], ["mu0", "H/m"]],
            "resolved_symbol_units": [["B", "T"], ["H", "A/m"], ["mu0", "H/m"]],
            "sign_convention": "outward_normal_positive",
            "resolved_sign_convention": "outward_normal_positive",
            "document_section": "theory/magnetostatics",
            "resolved_document_section": "theory/magnetostatics",
            "document_page": 42, "resolved_document_page": 42,
            "document_release": "6.0", "resolved_document_release": "6.0",
            "release_scope": "documentation_only",
            "resolved_release_scope": "documentation_only",
            "citation_sha256": "4" * 64, "resolved_citation_sha256": "4" * 64,
            "document_owner": "documentation/equations-402",
            "resolved_document_owner": "documentation/equations-402",
            "response_sha256": "5" * 64, "accepted_response_sha256": "5" * 64,
        }
        generation = f"input-region-{402 + index}"
        run[
            "input_region_material_source_boundary_numbering_continuation_unit_release_owner_response_identity"
        ] = {
            "input_generation": generation,
            **{
                key: generation
                for key in (
                    "region_generation", "material_generation", "source_generation",
                    "boundary_generation", "continuation_generation", "unit_generation",
                    "release_generation", "owner_generation", "response_generation",
                )
            },
            "region_numbers": [1, 2], "parsed_region_numbers": [1, 2],
            "material_references": [[1, "material:steel"], [2, "material:air"]],
            "parsed_material_references": [[1, "material:steel"], [2, "material:air"]],
            "source_references": [[1, "source:coil"]],
            "parsed_source_references": [[1, "source:coil"]],
            "boundary_references": [[1, "boundary:outer"], [2, "boundary:symmetry"]],
            "parsed_boundary_references": [[1, "boundary:outer"], [2, "boundary:symmetry"]],
            "continuation_markers": ["\\", "&"],
            "parsed_continuation_markers": ["\\", "&"],
            "length_unit": "mm", "parsed_length_unit": "mm",
            "schema_release": "6.0", "parsed_schema_release": "6.0",
            "document_owner": "documentation/input-402",
            "parsed_document_owner": "documentation/input-402",
            "response_sha256": "6" * 64, "accepted_response_sha256": "6" * 64,
        }
    return summary


def test_v36_source_positive_equation_and_input_reference_closure():
    assert _gate(_summary_v36())["status"] == "ok"


def test_v36_source_document_equation_symbol_unit_sign_section_release_citation_mismatch():
    summary = _summary_v36()
    record = summary["runs"][0][
        "document_equation_symbol_unit_sign_section_release_citation_owner_response_identity"
    ]
    record.update(
        {
            "symbol_generation": "equation-doc-401",
            "citation_generation": "equation-doc-400",
            "response_generation": "equation-doc-399",
            "resolved_equation_id": "unrelated",
            "resolved_symbols": ["x"],
            "resolved_symbol_units": [["x", "s"]],
            "resolved_sign_convention": "unknown",
            "resolved_document_section": "private/solver",
            "resolved_document_page": -1,
            "resolved_document_release": "99.0",
            "resolved_release_scope": "solver_internal",
            "resolved_citation_sha256": "d" * 64,
            "resolved_document_owner": "private/old",
            "accepted_response_sha256": "e" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "document_equations_use_current_symbols_units_sign_section_release_citation_owner_and_response"
    ]


def test_v36_source_input_region_material_source_boundary_numbering_continuation_mismatch():
    summary = _summary_v36()
    record = summary["runs"][0][
        "input_region_material_source_boundary_numbering_continuation_unit_release_owner_response_identity"
    ]
    record.update(
        {
            "region_generation": "input-region-401",
            "boundary_generation": "input-region-400",
            "response_generation": "input-region-399",
            "parsed_region_numbers": [2, 2, -1],
            "parsed_material_references": [[3, "material:missing"]],
            "parsed_source_references": [[9, "source:old"]],
            "parsed_boundary_references": [[0, "boundary:none"]],
            "parsed_continuation_markers": ["?"],
            "parsed_length_unit": "s",
            "parsed_schema_release": "99.0",
            "parsed_document_owner": "private/old",
            "accepted_response_sha256": "f" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "input_regions_use_current_numbering_material_source_boundary_continuation_unit_release_owner_and_response"
    ]


def test_v36_source_rejects_self_consistent_private_equation_section():
    summary = _summary_v36()
    for run in summary["runs"]:
        record = run[
            "document_equation_symbol_unit_sign_section_release_citation_owner_response_identity"
        ]
        record["document_section"] = "private/solver"
        record["resolved_document_section"] = "private/solver"
    assert _gate(summary)["status"] == "needs_attention"


def test_v36_source_rejects_self_consistent_dangling_region_reference():
    summary = _summary_v36()
    for run in summary["runs"]:
        record = run[
            "input_region_material_source_boundary_numbering_continuation_unit_release_owner_response_identity"
        ]
        material = [[1, "material:steel"], [3, "material:missing"]]
        record["material_references"] = material
        record["parsed_material_references"] = material
    assert _gate(summary)["status"] == "needs_attention"
