from __future__ import annotations

import copy
import json

from elf_mcp_server.material_force_contrast_contract import (
    material_force_contrast_contract_gate,
)
from elf_mcp_server.server import elf_material_force_contrast_contract_gate


def _summary() -> dict:
    common = {
        "mesh_exit_code": 0,
        "solver_exit_code": 0,
        "source_copy_preserved": True,
        "solution_complete": True,
        "error_marker_count": 0,
        "total_row_count": 1,
        "force_selection_recorded": True,
        "solution_sequence": ["moment", "field", "force"],
        "fresh_output_suffixes": [".meg", ".mao", ".mag", ".mat", ".mac"],
        "run_log_suffix": ".mao",
        "run_log_fresh": True,
        "field_result_suffix": ".mag",
        "field_result_fresh": True,
        "stored_solver_version": "old",
        "live_solver_version": "new",
        "mesh_hash_changed": True,
        "mesh_size_preserved": True,
    }
    return {
        "execution_route": "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog": False,
        "solver_family": "magnetostatic_bem",
        "result_authority": ".mao TOTAL",
        "total_field_order": ["area_m2", "flux_wb", "force_x_n", "force_y_n", "force_z_n"],
        "version_drift_policy": "record_versions_and_regenerated_mesh_before_applying_role_specific_bands",
        "cases": [
            {**common, "role": "background", "force_regression_relative_error": 7.0e-5},
            {**common, "role": "attractive", "force_regression_relative_error": 5.0e-5},
            {**common, "role": "repulsive_low", "force_regression_relative_error": 3.0e-5},
            {**common, "role": "repulsive_high", "force_regression_relative_error": 0.032},
        ],
        "public_gate": {"policy": "material_contrast_force_gate_v1", "status": "ok"},
    }


def test_material_force_contract_accepts_role_specific_version_bands() -> None:
    result = material_force_contrast_contract_gate(json.dumps(_summary()))
    assert result["status"] == "ok"
    assert json.loads(
        elf_material_force_contrast_contract_gate(json.dumps(_summary()))
    )["status"] == "ok"


def test_material_force_contract_rejects_strong_case_outside_version_band() -> None:
    summary = _summary()
    summary["cases"][-1]["force_regression_relative_error"] = 0.08
    result = material_force_contrast_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["strong_contrast_version_drift_is_bounded"] is False


def test_material_force_contract_rejects_mei_as_result_authority() -> None:
    summary = copy.deepcopy(_summary())
    summary["result_authority"] = ".mei"
    summary["cases"][0]["run_log_suffix"] = ".mei"
    result = material_force_contrast_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["mao_total_field_order_recorded"] is False
    assert result["checks"]["case_outputs_and_selection_complete"] is False


def test_material_force_contract_reports_invalid_regression_as_attention() -> None:
    summary = _summary()
    summary["cases"][0]["force_regression_relative_error"] = "not-a-number"
    result = material_force_contrast_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert result["checks"]["case_outputs_and_selection_complete"] is False
