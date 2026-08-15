"""Package entry point and compatibility exports for ELF MCP Server."""
from __future__ import annotations

from .handlers import *  # noqa: F401,F403 - stable public import surface
from .handlers import main


if __name__ == "__main__":
    main()
