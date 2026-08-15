"""Small MCP runtime core; domain handlers live in separate modules."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP


SERVER_NAME = "elf-mcp-server"
SERVER_TITLE = "ELF MCP Server"
SERVER_INSTRUCTIONS = (
    "This is a read-only public documentation and input-contract server. "
    "Start with elf_overview, prefer Resources for static guidance, validate "
    "all generated input locally, and keep product execution and raw outputs outside this server."
)


def create_runtime() -> FastMCP:
    return FastMCP(SERVER_NAME, instructions=SERVER_INSTRUCTIONS)


mcp = create_runtime()
