"""Metadata-only contract for the documented MOMCFJ force-method example."""

from __future__ import annotations

import json


def momc_force_triplet_contract_gate(summary_json: str) -> dict:
    """Validate source identity, result roles, and public force closure metadata."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    source_files = summary.get("source_files") or []
    outputs = summary.get("outputs") or []
    methods = summary.get("method_contracts") or {}
    source_names = [row.get("name") for row in source_files if isinstance(row, dict)]
    output_by_suffix = {
        row.get("suffix"): row for row in outputs if isinstance(row, dict)
    }

    def valid_digest_row(row: dict) -> bool:
        return (
            isinstance(row.get("bytes"), int)
            and row["bytes"] > 0
            and isinstance(row.get("sha256"), str)
            and len(row["sha256"]) == 64
        )

    required_outputs = {".meg", ".mao", ".mag", ".mat", ".mac"}
    outputs_complete = required_outputs <= set(output_by_suffix) and all(
        valid_digest_row(output_by_suffix[suffix])
        and output_by_suffix[suffix].get("fresh") is True
        for suffix in required_outputs
    )
    forc = methods.get("FORC") or {}
    fort = methods.get("FORT") or {}
    fixb = methods.get("FIXB") or {}
    public_gate = summary.get("public_gate") or {}
    checks = {
        "documented_source_pair_identified": (
            summary.get("source_case") == "MOMCFJ"
            and summary.get("source_kind") == "product_installed_official_momc_example"
            and source_names == ["MOMCFJ.mai", "MOMCFJ.mei"]
            and all(valid_digest_row(row) for row in source_files)
        ),
        "immutable_temporary_copy_used": summary.get("source_unchanged") is True
        and summary.get("temporary_work_copy") is True,
        "direct_cli_pipeline_completed": (
            summary.get("execution_route") == "direct_mesh_and_solver_exe_no_gui"
            and summary.get("completion_dialog") is False
            and summary.get("mesh_exit_code") == 0
            and summary.get("solver_exit_code") == 0
            and summary.get("mesh_version") == "7.5.0"
            and summary.get("solver_version") == "16.0.0"
        ),
        "harmonic_block_order_recorded": summary.get("block_order")
        == ["MOMC", "FORC", "FORT", "FIXB"]
        and summary.get("frequency_hz") == 1000.0,
        "forc_material_surface_selection_recorded": (
            forc.get("result_authority") == ".mao TOTAL"
            and forc.get("target_mid") == 2
            and forc.get("target_role") == "conducting_body"
        ),
        "fort_closed_stress_surface_selection_recorded": (
            fort.get("result_authority") == ".mao TOTAL"
            and fort.get("target_mid") == 3
            and fort.get("target_role") == "closed_stress_surface"
        ),
        "fixb_coil_decomposition_shape_recorded": (
            fixb.get("result_authority") == ".mao ELEMENT TOTAL FORCE"
            and fixb.get("coil_mid") == 1
            and fixb.get("divide") == 4
            and fixb.get("raw_row_count") == 96
            and fixb.get("coil_element_count") == 24
        ),
        "fresh_result_package_complete": outputs_complete,
        "public_force_triplet_gate_passed": (
            public_gate.get("policy")
            == "harmonic_magnetic_force_triplet_closure_gate_v1"
            and public_gate.get("status") == "ok"
        ),
    }
    issues = [name for name, ok in checks.items() if not ok]
    return {
        "schema": "elf-momc-force-triplet-contract/v1",
        "status": "ok" if not issues else "needs_attention",
        "checks": checks,
        "issues": issues,
        "metrics": {
            "source_file_count": len(source_files),
            "fresh_output_count": sum(
                row.get("fresh") is True for row in output_by_suffix.values()
            ),
            "fixb_raw_row_count": fixb.get("raw_row_count"),
            "fixb_coil_element_count": fixb.get("coil_element_count"),
        },
        "notes": [
            "the .mao TOTAL rows are the FORC/FORT force-vector authority",
            "FIXB emits one total plus decomposition rows per coil element when DIVIDE is used",
            "FORC, FORT, and FIXB have different selections and signs; compare them only through an explicit action-reaction contract",
            "keep solved force values and licensed source paths outside this public documentation server",
        ],
    }
