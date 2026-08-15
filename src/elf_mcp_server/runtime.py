"""Small MCP runtime core; domain handlers live in separate modules."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP


SERVER_NAME = "elf-mcp-server"
SERVER_TITLE = "ELF MCP Server"
SERVER_INSTRUCTIONS = (
    "This public server provides documentation, input contracts, and guarded execution of a "
    "user-local product DLL through Python ctypes. Start with elf_overview; call "
    "elf_product_detect and elf_product_case_check before elf_product_run. Product binaries "
    "are never bundled, execution requires explicit confirmation, and raw result files stay local."
)


def create_runtime() -> FastMCP:
    return FastMCP(SERVER_NAME, instructions=SERVER_INSTRUCTIONS)


mcp = create_runtime()
