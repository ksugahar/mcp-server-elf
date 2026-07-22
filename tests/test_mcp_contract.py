from elf_mcp_server.server import elf_agentic_profile, mcp


def test_elf_tools_expose_explicit_runtime_contract() -> None:
    tools = mcp._tool_manager._tools
    assert tools
    assert all(tool.title and tool.annotations for tool in tools.values())
    assert all(
        getattr(tool.annotations, hint) is not None
        for tool in tools.values()
        for hint in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
    )
    assert mcp._mcp_server.instructions
    assert mcp._mcp_server.version == "1.60.0"
    assert elf_agentic_profile()["runtime_contract"]["explicit_tool_annotations"] is True
