# MCP Server Design Pattern

This MCP server combines public documentation/sample decks with a guarded
user-local product execution adapter. Its runtime uses a small composition
core, separately owned handlers and adaptors, explicit protocol contracts, and
stable Resources without depending on another server.

## Pattern

- Tool handlers stay thin: validate inputs, call a curated data/helper layer,
  return compact public-safe output.
- Product execution uses a fixed MAGIC/ELFIN DLL and function allow-list in an
  isolated Python `ctypes` worker. Arbitrary DLLs, functions, commands, and
  Python code are rejected.
- Public sample decks, schemas, and validation labels are separated from private
  solver outputs.
- Route/search/read tools share common indexing helpers rather than duplicating
  file traversal logic.
- Heavy validation evidence is summarized through public-safe quality labels.

## Python Mapping

| Runtime responsibility | This server module |
|---|---|
| process entry point | `server.py` |
| runtime construction and instructions | `runtime.py` |
| public tool handlers | `handlers.py` |
| explicit safety definitions | `tool_definitions.py` |
| semantic protocol models | `models.py` |
| static guidance | `mcp_resources.py` |
| curated use cases and contracts | domain modules under `elf_mcp_server` |
| public corpus adaptors | `*_access.py` and `sample_decks.py` |
| local product adapter | `product_runner.py` and isolated `_product_worker.py` |
| system verification | protocol tests, schema checks, and public-boundary lint |

## Public Boundary

Do not include private converter code, local solver outputs, internal
cross-validation numbers, or machine-local product paths in public tool output
or documentation. The package may discover and load DLLs already installed on
the commercial user's machine; those DLLs and their raw output files are never
part of the distribution.
