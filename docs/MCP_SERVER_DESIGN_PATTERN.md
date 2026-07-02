# MCP Server Design Pattern

This MCP server is a public documentation and sample-deck server.  It borrows
maintainability patterns from the official MathWorks MATLAB MCP Server source
without depending on that code.

## Pattern

- Tool handlers stay thin: validate inputs, call a curated data/helper layer,
  return compact public-safe output.
- Product execution is outside this server.  Local solver handoff is described
  as a contract, not performed here.
- Public sample decks, schemas, and validation labels are separated from private
  solver outputs.
- Route/search/read tools share common indexing helpers rather than duplicating
  file traversal logic.
- Heavy validation evidence is summarized through public-safe quality labels.

## Python Mapping

| MathWorks source pattern | This server equivalent |
|---|---|
| `cmd/<server>/main.go` | package entry point |
| `pkg/tools` | public MCP tool families |
| `internal/usecases` | curated knowledge, routing, schemas, public contracts |
| `internal/adaptors` | file/index readers and public deck parsers |
| `guides` | docs and prompt/handoff contracts |
| fake/system tests | fixture decks, schema checks, public-boundary lint |

## Public Boundary

Do not include private converter code, local solver outputs, internal
cross-validation numbers, or machine-local product paths in public tool output
or documentation.
