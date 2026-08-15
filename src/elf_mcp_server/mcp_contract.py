"""Explicit MCP metadata and runtime composition contract."""
from __future__ import annotations

from typing import Any, Iterable

from mcp.types import ToolAnnotations

from .tool_definitions import TOOL_CONTRACTS


SCHEMA = "elf.mcp-server-contract.v2"


def apply_tool_contract(
    mcp: Any,
    *,
    server_name: str,
    version: str,
    tool_prefix: str = "",
    set_server_metadata: bool = True,
) -> dict[str, int]:
    """Apply and verify the explicit registry against the runtime surface."""
    tools = getattr(getattr(mcp, "_tool_manager", None), "_tools", {})
    selected = {name: tool for name, tool in tools.items() if not tool_prefix or name.startswith(tool_prefix)}
    contracts = {
        name: contract
        for name, contract in TOOL_CONTRACTS.items()
        if not tool_prefix or name.startswith(tool_prefix)
    }
    missing = sorted(set(selected) - set(contracts))
    stale = sorted(set(contracts) - set(selected))
    if missing or stale:
        raise RuntimeError(
            "explicit tool-contract registry mismatch: "
            f"missing={missing!r}, stale={stale!r}"
        )

    for name, tool in selected.items():
        contract = contracts[name]
        tool.title = contract.title
        tool.annotations = ToolAnnotations(
            readOnlyHint=contract.read_only,
            destructiveHint=contract.destructive,
            idempotentHint=contract.idempotent,
            openWorldHint=contract.open_world,
        )
        meta = dict(getattr(tool, "meta", None) or {})
        meta["elf.contract"] = SCHEMA
        meta["elf.classification"] = (
            "read-only-external" if contract.open_world else "read-only-local"
        )
        tool.meta = meta

    low_level = getattr(mcp, "_mcp_server", None)
    if set_server_metadata and low_level is not None:
        low_level.version = version
        if not getattr(low_level, "instructions", None):
            low_level.instructions = (
                f"Use {server_name} as a read-only public documentation and input-contract server. "
                "Keep product execution and raw results outside the MCP process."
            )
    return {"tools": len(selected), "explicit_contracts": len(contracts)}


def build_runtime_contract(capability_packs: Iterable[str], session_policy: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "runtime_core": "FastMCP over stdio",
        "capability_packs": list(capability_packs),
        "resource_layer": "static guidance exposed through stable MCP Resources",
        "skill_layer": "separate workflow skills",
        "explicit_tool_annotations": True,
        "semantic_output_models": True,
        "session_policy": session_policy,
        "protocol_smoke": "initialize + tools/list + resources/list/read + prompts/list/get + representative calls",
    }
