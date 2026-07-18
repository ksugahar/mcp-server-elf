from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v28 import _summary_v28


_PROMOTED_CASE_IDS = (
    "v29_source_command_option_schema_default_enum_unit_document_anchor_version_mismatch",
    "v29_source_mao_section_header_column_unit_locale_row_count_checksum_mismatch",
)


def _summary_v29():
    summary = _summary_v28()
    for index, run in enumerate(summary["runs"]):
        command_generation = f"command-schema-{331 + index}"
        run["command_option_schema_document_generation_identity"] = {
            "command_generation": command_generation,
            "option_command_generation": command_generation,
            "default_command_generation": command_generation,
            "enum_command_generation": command_generation,
            "unit_command_generation": command_generation,
            "document_command_generation": command_generation,
            "anchor_command_generation": command_generation,
            "result_command_generation": command_generation,
            "command_name": "force-report",
            "result_command_name": "force-report",
            "option_names": ["method", "axis", "scale"],
            "result_option_names": ["method", "axis", "scale"],
            "default_values": {"method": "virtual-work", "axis": "z", "scale": 1.0},
            "result_default_values": {"method": "virtual-work", "axis": "z", "scale": 1.0},
            "enum_values": {"method": ["virtual-work", "stress"], "axis": ["x", "y", "z"]},
            "result_enum_values": {"method": ["virtual-work", "stress"], "axis": ["x", "y", "z"]},
            "unit_symbols": {"scale": "1"},
            "result_unit_symbols": {"scale": "1"},
            "document_version": "6.0",
            "result_document_version": "6.0",
            "section_anchor": "force-report-options",
            "result_section_anchor": "force-report-options",
            "document_sha256": "5" * 64,
            "indexed_document_sha256": "5" * 64,
            "response_sha256": "6" * 64,
            "accepted_response_sha256": "6" * 64,
        }
        mao_generation = f"mao-section-{331 + index}"
        run["mao_section_header_column_unit_locale_row_owner_generation_identity"] = {
            "mao_generation": mao_generation,
            "header_mao_generation": mao_generation,
            "column_mao_generation": mao_generation,
            "unit_mao_generation": mao_generation,
            "locale_mao_generation": mao_generation,
            "row_mao_generation": mao_generation,
            "owner_mao_generation": mao_generation,
            "result_mao_generation": mao_generation,
            "section_header": "Force Result",
            "parsed_section_header": "Force Result",
            "column_names": ["position_m", "force_x_n", "force_y_n", "force_z_n"],
            "parsed_column_names": ["position_m", "force_x_n", "force_y_n", "force_z_n"],
            "unit_symbols": ["m", "N", "N", "N"],
            "parsed_unit_symbols": ["m", "N", "N", "N"],
            "numeric_locale": "C-dot",
            "parsed_numeric_locale": "C-dot",
            "row_count": 3,
            "parsed_row_count": 3,
            "rows": [[0.0, 0.0, 0.0, 10.0], [0.001, 0.0, 0.0, 9.0], [0.002, 0.0, 0.0, 8.0]],
            "parsed_rows": [[0.0, 0.0, 0.0, 10.0], [0.001, 0.0, 0.0, 9.0], [0.002, 0.0, 0.0, 8.0]],
            "section_owner_id": "result-set-331:force-result",
            "parsed_section_owner_id": "result-set-331:force-result",
            "section_sha256": "7" * 64,
            "parsed_section_sha256": "7" * 64,
            "result_sha256": "8" * 64,
            "accepted_result_sha256": "8" * 64,
        }
    return summary


def test_v29_source_positive_command_schema_and_mao_section_identities():
    assert _gate(_summary_v29())["status"] == "ok"


def test_v29_source_command_option_schema_default_enum_unit_document_anchor_version_mismatch():
    summary = _summary_v29()
    identity = summary["runs"][0]["command_option_schema_document_generation_identity"]
    identity.update({
        "option_command_generation": "command-schema-330",
        "document_command_generation": "command-schema-329",
        "result_option_names": ["mode", "secret"],
        "result_default_values": {"mode": "unsafe"},
        "result_enum_values": {"mode": ["unsafe"]},
        "result_unit_symbols": {"scale": "mm"},
        "result_document_version": "5.2",
        "result_section_anchor": "internal-options",
        "indexed_document_sha256": "d" * 64,
        "accepted_response_sha256": "e" * 64,
    })
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "command_guidance_uses_current_option_schema_defaults_enums_units_document_and_anchor"
    ]


def test_v29_source_mao_section_header_column_unit_locale_row_count_checksum_mismatch():
    summary = _summary_v29()
    identity = summary["runs"][0]["mao_section_header_column_unit_locale_row_owner_generation_identity"]
    identity.update({
        "header_mao_generation": "mao-section-330",
        "owner_mao_generation": "mao-section-329",
        "parsed_section_header": "Old Result",
        "parsed_column_names": ["force_z", "position_mm"],
        "parsed_unit_symbols": ["mN", "mm"],
        "parsed_numeric_locale": "comma",
        "parsed_row_count": 2,
        "parsed_rows": [[10.0, 0.0], [9.0, 1.0]],
        "parsed_section_owner_id": "old-result:force",
        "parsed_section_sha256": "f" * 64,
        "accepted_result_sha256": "a" * 64,
    })
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mao_sections_use_current_header_columns_units_locale_rows_owner_and_checksums"
    ]
