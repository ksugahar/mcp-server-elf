from pathlib import Path

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
    assert mcp._mcp_server.version == "1.61.1"
    assert elf_agentic_profile()["runtime_contract"]["explicit_tool_annotations"] is True


def test_mcp_sdk_dependency_stays_on_the_supported_v1_api() -> None:
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert '"mcp>=1.27,<2"' in pyproject
