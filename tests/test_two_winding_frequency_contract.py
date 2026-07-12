from __future__ import annotations

import copy
import json

from elf_mcp_server.server import elf_two_winding_frequency_contract_gate
from elf_mcp_server.two_winding_frequency_contract import (
    two_winding_frequency_contract_gate,
)


def _summary() -> dict:
    replay = {
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
        "parser_markers": {
            "frequency_rows": 7,
            "emfm_complex_rows": 14,
            "flum_complex_rows": 14,
        },
    }
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "source_copy_preserved": True,
        "source_file_count": 2,
        "source_digest_count": 2,
        "solver_version": "recorded",
        "run_date_utc": "recorded",
        "replays": [copy.deepcopy(replay), copy.deepcopy(replay)],
        "replay_rows_identical": True,
        "normalized_metrics": {
            "maximum_faraday_relative_error": 3.4e-5,
            "maximum_linkage_per_turn_relative_gap": 0.051,
        },
        "public_gate": {
            "policy": "two_winding_frequency_faraday_gate_v1",
            "status": "ok",
        },
    }


def test_contract_accepts_two_complete_replays() -> None:
    result = two_winding_frequency_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert all(result["checks"].values())
    dispatched = json.loads(elf_two_winding_frequency_contract_gate(json.dumps(_summary())))
    assert dispatched["status"] == "ok"


def test_contract_rejects_parser_and_public_gate_drift() -> None:
    summary = _summary()
    summary["replays"][1]["parser_markers"]["flum_complex_rows"] = 12
    summary["public_gate"]["status"] = "needs_attention"
    result = two_winding_frequency_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "two_complete_fresh_replays" in result["issues"]
    assert "solver_neutral_gate_closed" in result["issues"]


def test_contract_requires_exactly_two_replays() -> None:
    summary = _summary()
    summary["replays"] = summary["replays"][:1]
    try:
        two_winding_frequency_contract_gate(json.dumps(summary))
    except ValueError as exc:
        assert "exactly two" in str(exc)
    else:
        raise AssertionError("missing replay must be rejected")
