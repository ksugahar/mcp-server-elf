"""Public-safe contract for product leakage-inductance workflows."""
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
    "IMAG",
    "FLUX",
    "FLUX = INTEGRAL*TURN1",
]


def _pair(value, name: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must contain two values")
    pair = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in pair):
        raise ValueError(f"{name} must contain finite values")
    return pair


def leakage_inductance_contract_gate(summary_json: str) -> dict:
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    routes = summary.get("routes")
    if not isinstance(routes, list) or len(routes) != 2:
        raise ValueError("routes must contain compensated_energy and unit_current_basis")
    by_role = {str(row.get("route_role") or ""): row for row in routes if isinstance(row, dict)}
    if set(by_role) != {"compensated_energy", "unit_current_basis"}:
        raise ValueError("routes must have unique compensated_energy and unit_current_basis roles")

    compensated = by_role["compensated_energy"]
    basis = by_role["unit_current_basis"]
    currents = _pair(compensated.get("currents_A"), "currents_A")
    turns = _pair(compensated.get("turns"), "turns")
    flux = _pair(compensated.get("flux_linkage_Wb"), "flux_linkage_Wb")
    matrix = basis.get("matrix_H")
    if not isinstance(matrix, list) or len(matrix) != 2 or any(
        not isinstance(row, list) or len(row) != 2 for row in matrix
    ):
        raise ValueError("matrix_H must be 2x2")
    l11, m12 = (float(value) for value in matrix[0])
    m21, l22 = (float(value) for value in matrix[1])
    if not all(math.isfinite(value) for value in (l11, m12, m21, l22)):
        raise ValueError("matrix_H must contain finite values")
    i1, i2 = currents
    n1, n2 = turns
    if i1 == 0.0 or n1 <= 0.0 or n2 <= 0.0 or l22 == 0.0:
        raise ValueError("I1, turns and L22 must be nonzero and turns positive")

    energy = 0.5 * (i1 * flux[0] + i2 * flux[1])
    direct_leakage = 2.0 * energy / (i1 * i1)
    matrix_leakage = (
        l11 * i1 * i1
        + (m12 + m21) * i1 * i2
        + l22 * i2 * i2
    ) / (i1 * i1)
    closure = abs(direct_leakage - matrix_leakage) / max(
        abs(direct_leakage), abs(matrix_leakage), 1.0e-300
    )
    reciprocity = abs(m12 - m21) / max(abs(m12), abs(m21), 1.0e-300)
    ampere_turn_error = abs(n1 * i1 + n2 * i2) / max(
        abs(n1 * i1), abs(n2 * i2), 1.0e-300
    )
    k2 = m12 * m21 / (l11 * l22) if l11 > 0.0 and l22 > 0.0 else math.inf
    lsc = l11 - m12 * m21 / l22

    route_checks = {}
    for role, row in by_role.items():
        route_checks[role] = {
            "source_mai_mei_digests_recorded": row.get("source_file_count") == 2
            and row.get("source_digest_count") == 2,
            "source_copy_preserved": row.get("source_copy_preserved") is True,
            "two_fresh_replays": row.get("replay_count") == 2
            and float(row.get("replay_max_abs_Wb", math.inf)) <= 1.0e-12,
            "mesh_and_solver_exit_zero": row.get("mesh_exit_codes") == [0, 0]
            and row.get("solver_exit_codes") == [0, 0],
            "output_roles_complete_and_fresh": row.get("output_roles") == _OUTPUT_ROLES
            and row.get("all_outputs_fresh") is True,
        }
    route_status = {
        role: all(checks.values()) for role, checks in route_checks.items()
    }
    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_version_recorded": bool(str(summary.get("solver_version") or "").strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc") or "").strip()),
        "mao_is_result_authority": summary.get("result_authority") == ".mao",
        "parser_applies_reported_symmetry_factor": summary.get("result_parser_contract")
        == _PARSER_CONTRACT,
        "both_routes_replayed_and_fresh": all(route_status.values()),
        "unit_current_basis_recorded": basis.get("current_steps_A")
        == {"0": [1.0, 0.0], "1": [0.0, 1.0]},
        "ampere_turn_compensation_close": ampere_turn_error <= 1.0e-12,
        "mutual_reciprocity_close": reciprocity <= 0.01,
        "direct_and_matrix_leakage_close": closure <= 0.01,
        "positive_leakage_routes": direct_leakage > 0.0 and matrix_leakage > 0.0,
        "physical_coupling_and_short_circuit": 0.0 <= k2 < 1.0 and 0.0 < lsc < l11,
    }
    return {
        "schema": "elf-leakage-inductance-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "route_checks": route_checks,
        "observables": {
            "leakage_inductance_direct_H": direct_leakage,
            "leakage_inductance_matrix_H": matrix_leakage,
            "short_circuit_inductance_H": lsc,
            "coupling_squared": k2,
            "reciprocity_relative_error": reciprocity,
            "ampere_turn_relative_error": ampere_turn_error,
            "direct_matrix_relative_error": closure,
        },
        "notes": [
            "Use the .mao FLUX row as linked flux after TURN1 and multiply by the reported IMAG symmetry factor.",
            "Run the compensated-current energy route and unit-current matrix route independently and replay both.",
            "Leakage inductance from ampere-turn cancellation and Schur-complement short-circuit inductance are related but distinct observables.",
        ],
    }
