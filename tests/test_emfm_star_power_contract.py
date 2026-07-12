from __future__ import annotations

import cmath
import json
import math

from elf_mcp_server.emfm_star_power_contract import emfm_star_power_contract_gate
from elf_mcp_server.server import elf_emfm_star_power_balance_gate


def _phasor_map(mids: list[int], magnitude: float) -> dict[str, list[float]]:
    return {
        str(mid): [
            (magnitude * cmath.exp(-1j * 2.0 * math.pi * index / 3.0)).real,
            (magnitude * cmath.exp(-1j * 2.0 * math.pi * index / 3.0)).imag,
        ]
        for index, mid in enumerate(mids)
    }


def _summary() -> dict:
    source_mids = [2, 12, 22]
    passive_mids = [3, 13, 23]
    passive_current = math.sqrt(99.9)
    voltages = _phasor_map(source_mids, 100.0)
    voltages.update({str(mid): [0.0, 0.0] for mid in passive_mids})
    source_currents = _phasor_map(source_mids, -1.0)
    passive_currents = _phasor_map(passive_mids, passive_current)
    source_currents.update(passive_currents)
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "source_file_count": 2,
        "source_digest_count": 2,
        "source_copy_preserved": True,
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "solver_version": "x.y.z",
        "mesh_version": "a.b.c",
        "run_date_utc": "2026-01-01T00:00:00Z",
        "source_contract": {
            "analysis": "MOMC",
            "frequency_hz": 50.0,
            "phasor_convention": "complex_peak_amplitude",
            "emfm_mids": source_mids + passive_mids,
            "star_mids": source_mids,
            "voltage_drive_mids": source_mids + passive_mids,
            "voltage_phasors_by_mid": voltages,
            "resistance_ohm_by_mid": {
                **{str(mid): 0.1 for mid in source_mids},
                **{str(mid): 1.0 for mid in passive_mids},
            },
            "turns_by_mid": {
                **{str(mid): 250.0 for mid in source_mids},
                **{str(mid): 50.0 for mid in passive_mids},
            },
        },
        "result_contract": {
            "current_phasors_by_mid": source_currents,
            "current_orientation": "positive_out_of_voltage_source",
            "neutral_voltage": [0.0, 0.0],
            "mao_real_imag_sections": 2,
            "mao_complete": True,
            "mao_error_count": 0,
            "output_roles": {
                ".meg": "geometry",
                ".meo": "mesh_log",
                ".mao": "run_log",
                ".mag": "field_result",
                ".mat": "matrix_state",
                ".mac": "mark_state",
            },
            "all_outputs_fresh": True,
            "solver_neutral_gate_status": "ok",
        },
    }


def test_emfm_star_power_contract_accepts_balanced_copper_power():
    result = emfm_star_power_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert result["metrics"]["active_power_relative_residual"] < 1.0e-14
    assert result["metrics"]["source_to_passive_turn_ratio"] == 5.0


def test_emfm_star_power_contract_rejects_unpaired_mao_sections():
    summary = _summary()
    summary["result_contract"]["mao_real_imag_sections"] = 1
    result = emfm_star_power_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "mao_real_imag_sections_paired" in result["issues"]


def test_emfm_star_power_contract_rejects_wrong_current_orientation():
    summary = _summary()
    summary["result_contract"]["current_orientation"] = "unspecified"
    result = emfm_star_power_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "emfm_current_orientation_recorded" in result["issues"]


def test_emfm_star_power_contract_is_exposed_over_mcp_wrapper():
    result = json.loads(elf_emfm_star_power_balance_gate(json.dumps(_summary())))
    assert result["status"] == "ok"
