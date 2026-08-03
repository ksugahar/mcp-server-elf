from __future__ import annotations

import asyncio
import copy
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from elf_mcp_server.project_feature_inventory_contract import (
    ARTIFACT_KINDS,
    FEATURE_ROUTES,
    SCHEMA,
    inventory_digest,
    project_feature_inventory_contract_gate,
)


def _summary() -> dict[str, object]:
    features = sorted(FEATURE_ROUTES)
    routes = {name: list(FEATURE_ROUTES[name]) for name in features}
    count = 18
    digest = inventory_digest(features, routes, ARTIFACT_KINDS, count)
    generation = "source-final-feature-inventory-v1"
    return {
        "schema": SCHEMA,
        "created_at_utc": "2026-08-03T00:54:22Z",
        "generation": generation,
        "feature_generation": generation,
        "route_generation": generation,
        "artifact_generation": generation,
        "owner_generation": generation,
        "result_generation": generation,
        "feature_families": features,
        "feature_routes": routes,
        "artifact_kinds": list(ARTIFACT_KINDS),
        "project_family_count": count,
        "inventory_owner": "inventory:product-project-families",
        "inventory_sha256": digest,
        "accepted_inventory_sha256": digest,
        "result_sha256": "a" * 64,
        "accepted_result_sha256": "a" * 64,
    }


def test_accepts_exact_digest_bound_feature_inventory() -> None:
    result = project_feature_inventory_contract_gate(json.dumps(_summary()))
    assert result["status"] == "validated"
    assert result["feature_count"] == len(FEATURE_ROUTES)
    assert result["opens_local_paths"] is False


def test_rejects_missing_route() -> None:
    summary = _summary()
    summary["feature_routes"].pop("harmonic_balance")
    result = project_feature_inventory_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "feature_routes_are_exact" in result["issues"]


def test_rejects_stale_inventory_digest() -> None:
    summary = _summary()
    summary["inventory_sha256"] = "b" * 64
    summary["accepted_inventory_sha256"] = "b" * 64
    result = project_feature_inventory_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "inventory_digest_matches_content" in result["issues"]


def test_rejects_duplicate_or_unsorted_features() -> None:
    summary = _summary()
    summary["feature_families"] = list(reversed(summary["feature_families"]))
    result = project_feature_inventory_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "feature_families_are_exact_sorted_unique" in result["issues"]


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
                "elf_project_feature_inventory_contract_gate",
                {"summary_json": json.dumps(_summary())},
            )
            return {
                "listed": any(
                    tool.name == "elf_project_feature_inventory_contract_gate"
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


def test_rejects_unknown_top_level_fields() -> None:
    summary = copy.deepcopy(_summary())
    summary["local_path"] = "C:/private/result.mao"
    result = project_feature_inventory_contract_gate(json.dumps(summary))
    assert result["status"] == "needs_attention"
    assert "top_level_schema_is_exact" in result["issues"]
