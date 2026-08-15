"""Access original public patterns through the legacy examples API.

Product example files are intentionally not bundled or redistributed.

Functions:
    load_examples_dump()                                 -> dict[str, dict]
    list_examples(solver=None, category=None, ext=None)  -> file metadata
    search_examples(query, top_k=10, ...)                -> ranked matches
    get_example(rel_path, max_chars=...)                 -> raw input file text
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from .guards import bounded_int
from .public_corpus import EXAMPLES


@lru_cache(maxsize=1)
def load_examples_dump() -> dict[str, dict[str, Any]]:
    """Return the small original-pattern corpus."""
    return EXAMPLES


def list_examples(
    solver: str | None = None,
    category: str | None = None,
    ext: str | None = None,
) -> list[dict[str, Any]]:
    """List public example-pattern summaries, optionally filtered.

    Args:
        solver: "MAGIC" / "ELFIN" / "BEAM" (case-insensitive).
        category: Subcategory like "BASIC", "IPM", "MOMC", "LscLl", etc.
        ext: File extension without dot — "mai", "mei", "txt", etc.

    Returns:
        List of {"path", "ext", "solver", "category", "char_count"}.
    """
    dump = load_examples_dump()
    s = solver.upper() if solver else None
    out = []
    for path, meta in sorted(dump.items()):
        if s and meta.get("solver", "") != s:
            continue
        if category and meta.get("category", "") != category:
            continue
        if ext and meta.get("ext", "") != ext.lower().lstrip("."):
            continue
        out.append({
            "path": path,
            "ext": meta.get("ext", ""),
            "solver": meta.get("solver", ""),
            "category": meta.get("category", ""),
            "char_count": meta.get("char_count", 0),
        })
    return out


def search_examples(
    query: str,
    top_k: int = 10,
    solver: str | None = None,
    ext: str | None = None,
) -> list[dict[str, Any]]:
    """Substring-search across all example file text (case-insensitive).

    Multiple keywords (space-separated) require ALL to match (AND).

    Args:
        query: Search keywords (e.g. "MOMC FREQ", "OHM2 MAB", "HBA1").
        top_k: Max results.
        solver: Restrict to "MAGIC" / "ELFIN" / "BEAM".
        ext: Restrict to "mai" / "mei" / "txt" etc.

    Returns:
        List of {"path", "solver", "category", "ext", "score", "snippet"}.
    """
    top_k = bounded_int(top_k, name="top_k", minimum=1, maximum=100)
    dump = load_examples_dump()
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    s = solver.upper() if solver else None
    e = ext.lower().lstrip(".") if ext else None

    hits = []
    for path, meta in dump.items():
        if s and meta.get("solver", "") != s:
            continue
        if e and meta.get("ext", "") != e:
            continue
        text = meta.get("text", "")
        text_lower = text.lower()
        scores = [text_lower.count(kw.lower()) for kw in keywords]
        if not all(sc > 0 for sc in scores):
            continue
        score = sum(scores)
        first_pos = text_lower.find(keywords[0].lower())
        snip_start = max(0, first_pos - 80)
        snip_end = min(len(text), first_pos + 220)
        snippet = text[snip_start:snip_end].replace("\n", " | ").strip()
        if snip_start > 0:
            snippet = "..." + snippet
        if snip_end < len(text):
            snippet = snippet + "..."
        hits.append({
            "path": path,
            "solver": meta.get("solver", ""),
            "category": meta.get("category", ""),
            "ext": meta.get("ext", ""),
            "score": score,
            "snippet": snippet,
        })

    hits.sort(key=lambda h: -h["score"])
    return hits[:top_k]


def get_example(rel_path: str, max_chars: int = 30000) -> dict[str, Any]:
    """Get full text of a specific example file.

    Args:
        rel_path: e.g. "magic/BASIC/ABCL2.mai", "elfin/MOMC/cap1.mei".
                 Filename-only also works if unambiguous.
        max_chars: Truncate output if longer (default 30k).

    Returns:
        {"path", "solver", "category", "ext", "text", "char_count", "truncated"}.
    """
    max_chars = bounded_int(max_chars, name="max_chars", minimum=256, maximum=60_000)
    dump = load_examples_dump()
    meta = dump.get(rel_path)
    if not meta:
        candidates = [p for p in dump if p.endswith("/" + rel_path) or p == rel_path]
        if len(candidates) == 1:
            rel_path = candidates[0]
            meta = dump[rel_path]
        else:
            return {
                "path": rel_path,
                "error": f"not found (try one of: {candidates[:5]})" if candidates
                         else "not found in the public pattern corpus (use elf_examples_index)",
            }

    text = meta.get("text", "")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[... truncated, full length: {meta.get('char_count', 0)} chars]"
    return {
        "path": rel_path,
        "solver": meta.get("solver", ""),
        "category": meta.get("category", ""),
        "ext": meta.get("ext", ""),
        "text": text,
        "char_count": meta.get("char_count", 0),
        "truncated": truncated,
    }
