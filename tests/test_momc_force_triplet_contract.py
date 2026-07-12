from __future__ import annotations

import copy
import json

from elf_mcp_server.momc_force_triplet_contract import (
    momc_force_triplet_contract_gate,
)
from elf_mcp_server.server import elf_momc_force_triplet_contract_gate


def summary() -> dict:
    source_files = [
        {"name": name, "bytes": 100, "sha256": "a" * 64}
        for name in ("MOMCFJ.mai", "MOMCFJ.mei")
    ]
    outputs = [
        {"suffix": suffix, "bytes": 1000, "sha256": "b" * 64, "fresh": True}
        for suffix in (".meg", ".mao", ".mag", ".mat", ".mac")
    ]
    return {
        "source_case": "MOMCFJ",
        "source_kind": "product_installed_official_momc_example",
        "source_files": source_files,
        "source_unchanged": True,
        "temporary_work_copy": True,
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "mesh_version": "7.5.0",
        "solver_version": "16.0.0",
        "block_order": ["MOMC", "FORC", "FORT", "FIXB"],
        "frequency_hz": 1000.0,
        "method_contracts": {
            "FORC": {
                "result_authority": ".mao TOTAL",
                "target_mid": 2,
                "target_role": "conducting_body",
            },
            "FORT": {
                "result_authority": ".mao TOTAL",
                "target_mid": 3,
                "target_role": "closed_stress_surface",
            },
            "FIXB": {
                "result_authority": ".mao ELEMENT TOTAL FORCE",
                "coil_mid": 1,
                "divide": 4,
                "raw_row_count": 96,
                "coil_element_count": 24,
            },
        },
        "outputs": outputs,
        "public_gate": {
            "policy": "harmonic_magnetic_force_triplet_closure_gate_v1",
            "status": "ok",
        },
    }


def test_accepts_documented_force_triplet_metadata():
    payload = summary()
    result = momc_force_triplet_contract_gate(json.dumps(payload))
    assert result["status"] == "ok"
    assert json.loads(elf_momc_force_triplet_contract_gate(json.dumps(payload)))[
        "status"
    ] == "ok"


def test_rejects_mei_as_force_result_authority():
    payload = copy.deepcopy(summary())
    payload["method_contracts"]["FORC"]["result_authority"] = ".mei"
    result = momc_force_triplet_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["forc_material_surface_selection_recorded"] is False


def test_rejects_missing_fixb_decomposition_rows():
    payload = copy.deepcopy(summary())
    payload["method_contracts"]["FIXB"]["raw_row_count"] = 24
    result = momc_force_triplet_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["fixb_coil_decomposition_shape_recorded"] is False


def test_rejects_stale_mao_even_when_public_gate_passed():
    payload = copy.deepcopy(summary())
    next(row for row in payload["outputs"] if row["suffix"] == ".mao")["fresh"] = False
    result = momc_force_triplet_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["fresh_result_package_complete"] is False
