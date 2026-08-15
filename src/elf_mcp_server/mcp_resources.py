"""MCP Resources for static, public-safe guidance."""
from __future__ import annotations

from typing import Any

from .elf_knowledge import get_elf_documentation
from .public_corpus import HELP, PYTHON, WIKI


def _index_text(title: str, entries: dict[str, dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    for identifier, item in sorted(entries.items()):
        lines.append(f"- `{identifier}` — {item['title']}")
    return "\n".join(lines)


def register_resources(mcp: Any) -> None:
    """Register stable Resources once on a FastMCP runtime."""
    if getattr(mcp, "_elf_resources_registered", False):
        return

    @mcp.resource(
        "elf://guides/overview",
        name="elf_public_overview",
        title="ELF Public MCP Overview",
        description="Public server scope, workflow selection, and safety boundary.",
        mime_type="text/markdown",
    )
    def overview_resource() -> str:
        return (
            "# ELF public MCP overview\n\n"
            "This server provides original engineering summaries, public input decks, validation "
            "contracts, and a guarded Python/ctypes bridge to a user-local product installation. "
            "It does not distribute manuals, wiki text, wrapper source, binaries, or solver results; "
            "raw outputs remain in the caller-selected local directory."
        )

    @mcp.resource(
        "elf://guides/public-boundary",
        name="elf_public_boundary",
        title="ELF Public Boundary",
        description="Material that is intentionally included or excluded from the package.",
        mime_type="text/markdown",
    )
    def boundary_resource() -> str:
        return WIKI["public-boundary"]["text"]

    @mcp.resource(
        "elf://corpus/help",
        name="elf_help_summary_index",
        title="ELF Help Summary Index",
        description="Index of original public summaries; not a product-help snapshot.",
        mime_type="text/markdown",
    )
    def help_resource() -> str:
        return _index_text("Public help summaries", HELP)

    @mcp.resource(
        "elf://corpus/python",
        name="elf_python_contract_index",
        title="ELF Python Contract Index",
        description="Public facade schemas without vendor wrapper source.",
        mime_type="text/markdown",
    )
    def python_resource() -> str:
        return _index_text("Public Python facade contracts", PYTHON)

    @mcp.resource(
        "elf://topics/{topic}",
        name="elf_topic",
        title="ELF Engineering Topic",
        description="Curated public engineering topic by identifier.",
        mime_type="text/markdown",
    )
    def topic_resource(topic: str) -> str:
        return get_elf_documentation(topic)

    mcp._elf_resources_registered = True
