from __future__ import annotations

from elf_mcp_server.force_method_profile_contract import force_method_profile_contract_gate
from test_generalization_v29 import _summary_v29

_PROMOTED_CASE_IDS = (
    "v30_source_command_alias_platform_option_version_anchor_document_digest_mismatch",
    "v30_source_mao_vector_component_coordinate_frame_unit_point_order_digest_mismatch",
)

def _summary_v30():
    summary = _summary_v29()
    for index, run in enumerate(summary["runs"]):
        generation = f"command-alias-{341 + index}"
        run["command_alias_platform_option_version_anchor_document_digest_identity"] = {
            "command_generation": generation, "alias_command_generation": generation,
            "platform_command_generation": generation, "option_command_generation": generation,
            "version_command_generation": generation, "anchor_command_generation": generation,
            "document_command_generation": generation, "result_command_generation": generation,
            "canonical_command": "force-report", "resolved_canonical_command": "force-report",
            "command_aliases": ["force", "frpt"], "resolved_command_aliases": ["force", "frpt"],
            "platform": "windows-x64", "resolved_platform": "windows-x64",
            "available_options": ["method", "axis"], "resolved_available_options": ["method", "axis"],
            "product_version": "6.0", "resolved_product_version": "6.0",
            "section_anchor": "force-report-options", "resolved_section_anchor": "force-report-options",
            "document_owner": "command-reference-6.0", "resolved_document_owner": "command-reference-6.0",
            "document_sha256": "5" * 64, "indexed_document_sha256": "5" * 64,
        }
        generation = f"mao-vector-{341 + index}"
        run["mao_vector_component_frame_unit_point_owner_digest_identity"] = {
            "mao_generation": generation, "component_mao_generation": generation,
            "frame_mao_generation": generation, "unit_mao_generation": generation,
            "point_mao_generation": generation, "owner_mao_generation": generation,
            "digest_mao_generation": generation, "result_mao_generation": generation,
            "component_order": ["x", "y", "z"], "parsed_component_order": ["x", "y", "z"],
            "coordinate_frame": "global_cartesian", "parsed_coordinate_frame": "global_cartesian",
            "unit_symbols": ["N", "N", "N"], "parsed_unit_symbols": ["N", "N", "N"],
            "point_ids": [101, 102, 103], "parsed_point_ids": [101, 102, 103],
            "vectors": [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]],
            "parsed_vectors": [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]],
            "section_owner_id": "result-set-341:force-vector", "parsed_section_owner_id": "result-set-341:force-vector",
            "section_sha256": "6" * 64, "parsed_section_sha256": "6" * 64,
        }
    return summary

def _gate(summary):
    import json
    return force_method_profile_contract_gate(json.dumps(summary))

def test_v30_source_positive_command_alias_and_mao_vector_identities():
    assert _gate(_summary_v30())["status"] == "ok"

def test_v30_source_command_alias_platform_option_version_anchor_document_digest_mismatch():
    summary = _summary_v30(); identity = summary["runs"][0]["command_alias_platform_option_version_anchor_document_digest_identity"]
    identity.update({
        "alias_command_generation": "command-alias-340", "version_command_generation": "command-alias-339",
        "resolved_canonical_command": "internal-force", "resolved_command_aliases": ["unsafe"],
        "resolved_platform": "linux-x64", "resolved_available_options": ["secret"],
        "resolved_product_version": "5.2", "resolved_section_anchor": "internal",
        "resolved_document_owner": "old-doc", "indexed_document_sha256": "b" * 64,
    })
    result = _gate(summary); assert result["status"] == "needs_attention"
    assert not result["checks"]["command_guidance_uses_current_alias_platform_options_version_anchor_document_and_digest"]

def test_v30_source_mao_vector_component_coordinate_frame_unit_point_order_digest_mismatch():
    summary = _summary_v30(); identity = summary["runs"][0]["mao_vector_component_frame_unit_point_owner_digest_identity"]
    identity.update({
        "component_mao_generation": "mao-vector-340", "point_mao_generation": "mao-vector-339",
        "parsed_component_order": ["z", "x", "y"], "parsed_coordinate_frame": "local_cylindrical",
        "parsed_unit_symbols": ["mN", "mN", "mN"], "parsed_point_ids": [103, 101, 102],
        "parsed_vectors": [[3.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
        "parsed_section_owner_id": "old-result", "parsed_section_sha256": "c" * 64,
    })
    result = _gate(summary); assert result["status"] == "needs_attention"
    assert not result["checks"]["mao_vectors_use_current_components_frame_units_point_order_owner_and_digest"]
