"""Metadata-only contract for ABCL complex field output examples."""

from __future__ import annotations

import json


_OUTPUT_ROLES = {
    ".meg": "geometry",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}
_PARSER_CONTRACT = ["REAL PART", "IMAGINARY PART", "AB8T", "BMAX ELEMENT"]
_SOURCE_FEATURES = {
    "ABCL2": {
        "ohm2_count": 1,
        "image_axis": None,
        "channel_change": False,
        "lone_boundary": False,
    },
    "ABCLH": {
        "ohm2_count": 2,
        "image_axis": None,
        "channel_change": False,
        "lone_boundary": False,
    },
    "ABCLHX": {
        "ohm2_count": 2,
        "image_axis": "X",
        "channel_change": True,
        "lone_boundary": True,
    },
}
_STRUCTURAL_COUNTS = {
    "ABCL2": {"field_row_count": 72, "maximum_count": 2},
    "ABCLH": {"field_row_count": 40, "maximum_count": 2},
    "ABCLHX": {"field_row_count": 36, "maximum_count": 4},
}


def complex_field_run_contract_gate(summary_json: str) -> dict:
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    cases = summary.get("cases")
    if not isinstance(cases, list) or len(cases) != 3:
        raise ValueError("cases must contain the three ABCL source-example runs")

    case_rows = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"case {index} must be an object")
        case_id = str(case.get("case_id") or "")
        expected_features = _SOURCE_FEATURES.get(case_id)
        expected_counts = _STRUCTURAL_COUNTS.get(case_id, {})
        checks = {
            "known_source_case": expected_features is not None,
            "source_mai_mei_digests_recorded": case.get("source_file_count") == 2
            and case.get("source_digest_count") == 2,
            "source_copy_preserved": case.get("source_copy_preserved") is True,
            "mesh_and_solver_exit_zero": case.get("mesh_exit_code") == 0
            and case.get("solver_exit_code") == 0,
            "output_roles_complete_and_fresh": case.get("output_roles") == _OUTPUT_ROLES
            and case.get("all_outputs_fresh") is True,
            "source_feature_signature_matches": expected_features is not None
            and case.get("source_features") == expected_features,
            "complex_field_structure_matches": bool(expected_counts)
            and case.get("field_row_count") == expected_counts.get("field_row_count")
            and case.get("maximum_count") == expected_counts.get("maximum_count"),
            "common_frequency_excitation_unit": case.get("frequency_hz") == 1000.0
            and case.get("ampere_turns") == 100.0
            and case.get("field_unit") == "T",
            "public_complex_field_gate_passed": case.get("public_gate_status") == "ok",
        }
        case_rows.append(
            {
                "case_id": case_id,
                "checks": checks,
                "status": "ok" if all(checks.values()) else "needs_attention",
            }
        )

    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "gui_and_completion_dialog_disabled": summary.get("gui_visible") is False
        and summary.get("completion_dialog") is False,
        "solver_version_and_run_date_recorded": bool(
            str(summary.get("solver_version") or "").strip()
        )
        and bool(str(summary.get("run_date_utc") or "").strip()),
        "result_parser_contract_recorded": summary.get("result_parser_contract")
        == _PARSER_CONTRACT,
        "all_source_cases_valid": all(row["status"] == "ok" for row in case_rows),
        "three_distinct_case_ids": {row["case_id"] for row in case_rows}
        == set(_SOURCE_FEATURES),
    }
    return {
        "schema": "elf-complex-field-run-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "cases": case_rows,
        "notes": [
            "Parse REAL and IMAGINARY AB8T rows separately, then bind each BMAX to its part and material id.",
            "ABCLHX carries the X-image/channel/lone-boundary source signature; do not infer it from output magnitude alone.",
            "The primary execution record is .mao; require fresh .mag/.mat/.mac/.meg companions from the same direct run.",
        ],
    }
