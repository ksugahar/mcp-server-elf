from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _probe_stdio() -> dict:
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    source_root = repo / "src"
    if source_root.is_dir():
        env["PYTHONPATH"] = os.pathsep.join(
            [str(source_root), env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "elf_mcp_server.server"],
        cwd=str(repo),
        env=env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            tools = listed.tools
            called = await session.call_tool("elf_overview", {})
            hints = (
                "readOnlyHint",
                "destructiveHint",
                "idempotentHint",
                "openWorldHint",
            )
            return {
                "server_name": initialized.serverInfo.name,
                "server_version": initialized.serverInfo.version,
                "protocol_version": initialized.protocolVersion,
                "instructions": initialized.instructions,
                "tool_count": len(tools),
                "missing_titles": [tool.name for tool in tools if not tool.title],
                "missing_annotations": [
                    tool.name
                    for tool in tools
                    if tool.annotations is None
                    or any(getattr(tool.annotations, hint) is None for hint in hints)
                ],
                "probe_is_error": bool(called.isError),
                "probe_has_content": bool(called.content),
            }


def test_stdio_initialize_list_and_safe_call_contract() -> None:
    result = asyncio.run(asyncio.wait_for(_probe_stdio(), timeout=45))
    assert result["server_name"] == "elf-mcp-server"
    assert result["server_version"]
    assert result["protocol_version"]
    assert result["instructions"]
    assert result["tool_count"] > 0
    assert result["missing_titles"] == []
    assert result["missing_annotations"] == []
    assert result["probe_is_error"] is False
    assert result["probe_has_content"] is True
