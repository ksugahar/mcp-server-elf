import copy
import json

from elf_mcp_server.ipm_two_run_contract import ipm_two_run_ldlq_contract_gate
from elf_mcp_server.server import elf_ipm_two_run_ldlq_contract_gate


def _summary():
    return {
        "pole_pairs": 2,
        "phase_order": ["A", "B", "C"],
        "same_angle_grid": True,
        "flux_derivation": "current_on_minus_pm_only_before_park",
        "pm_only_reference": {
            "role": "pm_only",
            "verified": True,
            "artifact_digest": "a" * 64,
            "result_digest": "b" * 64,
        },
        "current_on_run": {
            "execution_route": "direct_solver_exe_no_gui",
            "completion_dialog": False,
            "exit_code": 0,
            "source_digests": {name: str(index) * 64 for index, name in enumerate(("control", "mesh", "model", "properties"), 1)},
            "source_copy_preserved": True,
            "output_roles": {
                ".mao": "run_log",
                ".mag": "field_result",
                ".mat": "matrix_state",
                ".mac": "mark_state",
            },
            "all_outputs_fresh": True,
            "phase_ids": [4, 5, 6],
            "flux_record_family": "M1MF",
            "time_step_count": 181,
            "flux_record_count": 543,
            "solver_version": "major.minor",
            "run_date_utc": "2026-07-12T00:00:00Z",
        },
        "derived_gate": {
            "schema": "radia-motor-ipm-two-run-ldlq/v1",
            "status": "ok",
            "input_digest": "c" * 64,
        },
    }


def test_ipm_two_run_contract_accepts_verified_pair():
    result = ipm_two_run_ldlq_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert all(result["checks"].values())
    assert json.loads(elf_ipm_two_run_ldlq_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_ipm_two_run_contract_rejects_stale_total_flux_shortcut():
    bad = copy.deepcopy(_summary())
    bad["current_on_run"]["all_outputs_fresh"] = False
    bad["flux_derivation"] = "current_on_total_flux"
    result = ipm_two_run_ldlq_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["all_outputs_fresh"] is False
    assert result["checks"]["pm_subtraction_before_park"] is False


def test_ipm_two_run_contract_rejects_unverified_reference():
    bad = copy.deepcopy(_summary())
    bad["pm_only_reference"]["verified"] = False
    result = ipm_two_run_ldlq_contract_gate(json.dumps(bad))
    assert result["status"] == "needs_attention"
    assert result["checks"]["pm_only_reference_verified"] is False
