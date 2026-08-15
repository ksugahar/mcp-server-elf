"""Access original public summaries through the legacy help API.

Product help pages are intentionally not bundled or redistributed.

Functions:
    load_help_dump()                       -> dict[str, dict]
    list_help_files(prefix=None)           -> list of file metadata
    search_help(query, top_k=10)           -> ranked substring matches
    get_help_file(rel_path, max_chars=...) -> original summary text
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from .guards import bounded_int
from .public_corpus import HELP


@lru_cache(maxsize=1)
def load_help_dump() -> dict[str, dict[str, Any]]:
    """Return the small original-summary corpus."""
    return HELP


def list_help_files(prefix: str | None = None) -> list[dict[str, Any]]:
    """List public summaries, optionally filtered by identifier prefix.

    Args:
        prefix: Restrict to files whose relative path starts with this string
                (e.g. "m_rf1/" for MAGIC reference, "d_ken/" for technical docs).

    Returns:
        List of {"path", "title", "char_count"}. Sorted alphabetically by path.
    """
    dump = load_help_dump()
    out = []
    for path, meta in sorted(dump.items()):
        if prefix and not path.startswith(prefix):
            continue
        out.append({
            "path": path,
            "title": meta.get("title", ""),
            "char_count": meta.get("char_count", 0),
        })
    return out


def search_help(query: str, top_k: int = 10, prefix: str | None = None) -> list[dict[str, Any]]:
    """Search public summary text by substring (case-insensitive).

    Returns ranked matches with snippet around first hit.

    Args:
        query: Search string (substring match, case-insensitive).
               Supports multiple keywords separated by space (AND match).
        top_k: Max number of results to return.
        prefix: Restrict to paths starting with this prefix.

    Returns:
        List of {"path", "title", "score", "snippet"} sorted by score desc.
        Score = sum of keyword match counts.
    """
    top_k = bounded_int(top_k, name="top_k", minimum=1, maximum=100)
    dump = load_help_dump()
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []

    hits = []
    for path, meta in dump.items():
        if prefix and not path.startswith(prefix):
            continue
        text = meta.get("text", "")
        text_lower = text.lower()
        scores = [text_lower.count(kw.lower()) for kw in keywords]
        if not all(s > 0 for s in scores):  # AND requirement
            continue
        score = sum(scores)
        # Snippet around first hit of first keyword
        first_pos = text_lower.find(keywords[0].lower())
        snip_start = max(0, first_pos - 80)
        snip_end = min(len(text), first_pos + 220)
        snippet = text[snip_start:snip_end].replace("\n", " ").strip()
        if snip_start > 0:
            snippet = "..." + snippet
        if snip_end < len(text):
            snippet = snippet + "..."
        hits.append({
            "path": path,
            "title": meta.get("title", ""),
            "score": score,
            "snippet": snippet,
        })

    hits.sort(key=lambda h: -h["score"])
    return hits[:top_k]


def get_help_file(rel_path: str, max_chars: int = 30000) -> dict[str, Any]:
    """Get extracted text of a specific help file.

    Args:
        rel_path: Identifier returned by :func:`list_help_files`.
        max_chars: Truncate output if longer (default 30k chars).

    Returns:
        {"path", "title", "text", "char_count", "truncated"}.
        Empty result if file not found.
    """
    max_chars = bounded_int(max_chars, name="max_chars", minimum=256, maximum=60_000)
    dump = load_help_dump()
    meta = dump.get(rel_path)
    if not meta:
        # Try matching by filename only
        candidates = [p for p in dump if p.endswith("/" + rel_path) or p == rel_path]
        if len(candidates) == 1:
            rel_path = candidates[0]
            meta = dump[rel_path]
        else:
            return {
                "path": rel_path,
                "error": f"not found (try one of: {candidates[:5]})" if candidates
                         else "not found in the public summary corpus (use elf_help_index)",
            }

    text = meta.get("text", "")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + "\n\n[... truncated, full length: %d chars]" % meta.get("char_count", 0)
    return {
        "path": rel_path,
        "title": meta.get("title", ""),
        "text": text,
        "char_count": meta.get("char_count", 0),
        "truncated": truncated,
    }
