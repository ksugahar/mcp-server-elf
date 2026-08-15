# MCP Implementation Checklist

Use this checklist when adding or refactoring tools in this public ELF/MAGIC
MCP server.  It follows the same maintainability pattern described in
`MCP_SERVER_DESIGN_PATTERN.md`.

## Tool Boundary

- Keep the MCP handler thin.
- Put reusable logic in an importable helper.
- Return compact public-safe dictionaries or text summaries.
- Execute product solvers only through the fixed, isolated Python `ctypes`
  adapter after detect, case validation, and explicit confirmation.
- Do not expose arbitrary Python evaluation, DLL paths, native symbols, or
  shell commands.
- Do not expose private solver outputs, local paths, or internal validation
  artifacts.

## Data Boundary

- Public decks, public schemas, and public quality labels may be packaged.
- Private converter code and local cross-validation outputs stay outside the
  package.
- Use manifest-style contracts around local execution state; never bundle a
  DLL, license asset, raw result, or machine-local installation path.
- Prefer stable keys so downstream MCP clients can compare tool output across
  releases.

## Test Boundary

- Add a focused unit test for new parser, router, schema, or contract logic.
- Use small fixture decks or synthetic manifests.
- Keep normal tests solver-free through a mocked worker; run a small licensed
  DLL smoke test separately before release when the product is available.
- Run public-boundary checks before release.

## Release Boundary

Before publishing:

1. Confirm no private converter imports.
2. Confirm no local product install paths.
3. Confirm no solver-output values that are not explicitly public-safe.
4. Confirm README/tool inventory reflects the public tool surface.
5. Run the focused pytest suite.

This keeps the public package useful to MCP clients while preserving the product
and private validation boundary.
