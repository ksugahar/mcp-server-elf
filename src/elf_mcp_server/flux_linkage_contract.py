"""Metadata-only contract for two-winding flux-linkage LIVE runs."""
from __future__ import annotations

import json
import math


_OUTPUT_ROLES = {
    ".meg": "geometry",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}
_PARSER_CONTRACT = [
    "TIME STEP",
    "FLUX MID",
    "FLUX",
    "FLUX = INTEGRAL*TURN1",
]


def flux_linkage_inductance_contract_gate(summary_json: str) -> dict:
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    cases = summary.get("cases")
    if not isinstance(cases, list) or len(cases) < 3:
        raise ValueError("cases must contain at least three source-example runs")

    case_rows = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"case {index} must be an object")
        try:
            matrix = case["matrix_H"]
            l11, m12 = (float(value) for value in matrix[0])
            m21, l22 = (float(value) for value in matrix[1])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError(f"case {index} has an invalid matrix_H") from exc
        mutual = 0.5 * (m12 + m21)
        reciprocity = abs(m12 - m21) / max(abs(m12), abs(m21), 1.0e-300)
        determinant = l11 * l22 - mutual * mutual
        coupling = (
            abs(mutual) / math.sqrt(l11 * l22)
            if l11 > 0.0 and l22 > 0.0
            else math.inf
        )
        checks = {
            "source_mai_mei_digests_recorded": case.get("source_file_count") == 2
            and case.get("source_digest_count") == 2,
            "source_copy_preserved": case.get("source_copy_preserved") is True,
            "mesh_and_solver_exit_zero": case.get("mesh_exit_code") == 0
            and case.get("solver_exit_code") == 0,
            "two_current_basis_steps_recorded": case.get("current_steps_A")
            == {"0": [1.0, 0.0], "1": [0.0, 1.0]},
            "output_roles_complete_and_fresh": case.get("output_roles") == _OUTPUT_ROLES
            and case.get("all_outputs_fresh") is True,
            "self_inductances_positive": l11 > 0.0 and l22 > 0.0,
            "mutual_reciprocity": reciprocity <= 0.02,
            "matrix_positive_semidefinite": determinant >= -1.0e-12 * max(abs(l11 * l22), 1.0e-300),
            "coupling_bounded": coupling <= 1.0 + 1.0e-12,
        }
        case_rows.append({
            "case_id": str(case.get("case_id") or ""),
            "topology_role": case.get("topology_role"),
            "coupling_abs": coupling,
            "reciprocity_relative_error": reciprocity,
            "determinant_H2": determinant,
            "checks": checks,
            "status": "ok" if all(checks.values()) else "needs_attention",
        })

    closed = [row for row in case_rows if row["topology_role"] == "closed_path"]
    open_rows = [row for row in case_rows if row["topology_role"] in {"open_path", "thin_open_path"}]
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_version_recorded": bool(str(summary.get("solver_version") or "").strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc") or "").strip()),
        "result_parser_contract_recorded": summary.get("result_parser_contract")
        == _PARSER_CONTRACT,
        "all_source_cases_valid": all(row["status"] == "ok" for row in case_rows),
        "one_closed_and_two_open_roles": len(closed) == 1 and len(open_rows) >= 2,
        "closed_path_has_strongest_coupling": len(closed) == 1
        and bool(open_rows)
        and closed[0]["coupling_abs"] > max(row["coupling_abs"] for row in open_rows),
    }
    return {
        "schema": "elf-flux-linkage-inductance-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "cases": case_rows,
        "notes": [
            "Excite each winding separately and parse both FLUM rows at both time steps.",
            "FLUX is the linked flux after the reported TURN1 factor; use it directly with the 1 A source basis.",
            "Reciprocity, positive semidefiniteness and |k|<=1 are required before comparing topology roles.",
        ],
    }
