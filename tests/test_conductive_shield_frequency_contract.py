from __future__ import annotations

import copy
import json

from elf_mcp_server.conductive_shield_frequency_contract import (
    conductive_shield_frequency_contract_gate,
)
from elf_mcp_server.server import elf_conductive_shield_frequency_contract_gate


def _summary() -> dict:
    replay = {
        "model_role": "baseline",
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "output_roles": {
            ".meg": "geometry",
            ".mao": "run_log",
            ".mag": "field_result",
            ".mat": "matrix_state",
            ".mac": "mark_state",
        },
        "all_outputs_fresh": True,
        "owned_processes_after": 0,
        "parser_markers": {"frequency_rows": 4, "emfm_complex_rows": 8, "flum_complex_rows": 8},
    }
    shielded = copy.deepcopy(replay)
    shielded["model_role"] = "shielded"
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "source_copy_preserved": True,
        "source_file_count_per_model": 2,
        "source_digest_count": 4,
        "model_contract": {
            "paired_geometry": True,
            "baseline_has_shield": False,
            "comparison_has_conductive_magnetic_shield": True,
        },
        "solver_version": "recorded",
        "run_date_utc": "recorded",
        "frequency_row_count": 4,
        "replays": [copy.deepcopy(replay), copy.deepcopy(replay), copy.deepcopy(shielded), copy.deepcopy(shielded)],
        "baseline_replay_rows_identical": True,
        "shielded_replay_rows_identical": True,
        "normalized_metrics": {
            "maximum_faraday_relative_error": 4.0e-5,
            "low_frequency_secondary_coupling_ratio": 1.1,
            "high_frequency_secondary_coupling_ratio": 0.5,
        },
        "public_gate": {"policy": "magnetic_conductive_shield_frequency_gate_v1", "status": "ok"},
        "timing_breakdown_s": {"copy": 1.0, "mesh": 2.0, "solve": 3.0, "verify": 1.0},
    }


def test_contract_accepts_four_complete_replays_and_dispatches():
    result = conductive_shield_frequency_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert all(result["checks"].values())
    assert json.loads(elf_conductive_shield_frequency_contract_gate(json.dumps(_summary())))["status"] == "ok"


def test_contract_rejects_parser_role_and_public_gate_drift():
    row = _summary()
    row["replays"][3]["parser_markers"]["flum_complex_rows"] = 6
    row["replays"][3]["model_role"] = "baseline"
    row["public_gate"]["status"] = "needs_attention"
    result = conductive_shield_frequency_contract_gate(json.dumps(row))
    assert result["status"] == "needs_attention"
    assert result["checks"]["four_complete_fresh_replays"] is False
    assert result["checks"]["paired_model_roles_are_explicit"] is False
    assert result["checks"]["solver_neutral_gate_closed"] is False


def test_contract_rejects_missing_dual_regime_and_timing_stage():
    row = _summary()
    row["normalized_metrics"]["high_frequency_secondary_coupling_ratio"] = 1.1
    row["timing_breakdown_s"].pop("verify")
    result = conductive_shield_frequency_contract_gate(json.dumps(row))
    assert result["status"] == "needs_attention"
    assert result["checks"]["normalized_dual_regime_is_present"] is False
    assert result["checks"]["exactly_four_timing_stages"] is False
