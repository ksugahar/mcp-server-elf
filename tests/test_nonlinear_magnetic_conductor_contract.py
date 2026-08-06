from __future__ import annotations

import asyncio
import copy
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from elf_mcp_server.nonlinear_magnetic_conductor_contract import (
    SCHEMA,
    nonlinear_magnetic_conductor_validation_gate,
)
from elf_mcp_server.server import elf_nonlinear_magnetic_conductor_validation_gate


def _summary() -> dict[str, object]:
    errors = {
        "source_mean_b_mesh_relative": 0.01,
        "source_joule_mesh_relative": 0.02,
        "independent_mean_b_relative": 0.03,
        "independent_joule_relative": 0.01,
        "reduced_parent_joule_relative": 0.04,
        "response_order_saturation_relative": 0.001,
        "energy_balance_mixed_norm": 0.0001,
    }
    tolerances = {
        "source_mean_b_mesh_relative": 0.05,
        "source_joule_mesh_relative": 0.05,
        "independent_mean_b_relative": 0.05,
        "independent_joule_relative": 0.05,
        "reduced_parent_joule_relative": 0.07,
        "response_order_saturation_relative": 0.005,
        "energy_balance_mixed_norm": 0.001,
    }
    return {
        "schema": SCHEMA,
        "created_at_utc": "2026-08-06T00:00:00Z",
        "generation": "public-safe-nonlinear-magnetic-conductor-v1",
        "material_scope": "same_region_nonlinear_magnetic_conductor",
        "transient_step_count": 11,
        "model_identity_sha256": "a" * 64,
        "accepted_model_identity_sha256": "a" * 64,
        "result_sha256": "b" * 64,
        "accepted_result_sha256": "b" * 64,
        "evidence_checks": {
            "same_geometry_material_source_time_identity": True,
            "nonlinear_iterations_converged": True,
            "source_mean_b_mesh_converged": True,
            "source_joule_mesh_converged": True,
            "independent_mean_b_checked": True,
            "independent_joule_checked": True,
            "reduced_parent_joule_checked": True,
            "response_order_saturation_checked": True,
            "joule_nonnegative": True,
            "energy_balance_closed": True,
        },
        "normalized_errors": errors,
        "tolerances": tolerances,
    }


def test_accepts_observable_specific_convergence_and_dispatches() -> None:
    direct = nonlinear_magnetic_conductor_validation_gate(json.dumps(_summary()))
    dispatched = json.loads(
        elf_nonlinear_magnetic_conductor_validation_gate(json.dumps(_summary()))
    )

    assert direct["status"] == "validated"
    assert direct["observable_status"] == {
        "mean_b": "validated",
        "joule_loss": "validated",
    }
    assert dispatched["status"] == "validated"
    assert direct["opens_local_paths"] is False
    assert direct["exposes_solved_values"] is False


def test_mean_b_can_pass_while_unconverged_source_joule_is_rejected() -> None:
    summary = copy.deepcopy(_summary())
    summary["evidence_checks"]["source_joule_mesh_converged"] = False
    summary["normalized_errors"]["source_joule_mesh_relative"] = 0.2

    result = nonlinear_magnetic_conductor_validation_gate(json.dumps(summary))

    assert result["status"] == "needs_attention"
    assert result["observable_status"] == {
        "mean_b": "validated",
        "joule_loss": "needs_attention",
    }
    assert result["checks"]["mean_b_observable_is_validated"] is True
    assert result["checks"]["joule_observable_is_validated"] is False


def test_rejects_unknown_local_path_and_stale_result_identity() -> None:
    summary = copy.deepcopy(_summary())
    summary["local_path"] = "C:/private/result.mao"
    summary["accepted_result_sha256"] = "c" * 64

    result = nonlinear_magnetic_conductor_validation_gate(json.dumps(summary))

    assert result["status"] == "needs_attention"
    assert result["checks"]["top_level_schema_is_exact"] is False
    assert result["checks"]["result_identity_is_bound"] is False


async def _stdio_probe() -> dict[str, object]:
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo / "src"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "elf_mcp_server.server"],
        cwd=str(repo),
        env=env,
    )
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            listed = await session.list_tools()
            called = await session.call_tool(
                "elf_nonlinear_magnetic_conductor_validation_gate",
                {"summary_json": json.dumps(_summary())},
            )
            return {
                "listed": any(
                    tool.name
                    == "elf_nonlinear_magnetic_conductor_validation_gate"
                    for tool in listed.tools
                ),
                "is_error": bool(called.isError),
                "status": json.loads(called.content[0].text)["status"],
            }


def test_changed_tool_passes_real_stdio_protocol() -> None:
    assert asyncio.run(asyncio.wait_for(_stdio_probe(), timeout=45)) == {
        "listed": True,
        "is_error": False,
        "status": "validated",
    }
