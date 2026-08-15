"""Access public Python-facade summaries through the legacy API.

Vendor wrappers, configuration files, error tables, and binaries are not
bundled or redistributed.

Functions:
    load_python_dump()              -> dict[str, dict]
    list_python_files(ext=None)     -> list of file metadata
    search_python(query, top_k=10)  -> ranked snippets
    get_python_file(rel_path, ...)  -> full text
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from .guards import bounded_int
from .public_corpus import PYTHON


@lru_cache(maxsize=1)
def load_python_dump() -> dict[str, dict[str, Any]]:
    return PYTHON


def list_python_files(ext: str | None = None) -> list[dict[str, Any]]:
    dump = load_python_dump()
    out = []
    for path, meta in sorted(dump.items()):
        if ext and meta.get("ext", "") != ext.lower().lstrip("."):
            continue
        out.append({
            "path": path,
            "ext": meta.get("ext", ""),
            "char_count": meta.get("char_count", 0),
        })
    return out


def search_python(query: str, top_k: int = 10, ext: str | None = None) -> list[dict[str, Any]]:
    top_k = bounded_int(top_k, name="top_k", minimum=1, maximum=100)
    dump = load_python_dump()
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    e = ext.lower().lstrip(".") if ext else None

    hits = []
    for path, meta in dump.items():
        if e and meta.get("ext", "") != e:
            continue
        text = meta.get("text", "")
        text_lower = text.lower()
        scores = [text_lower.count(kw.lower()) for kw in keywords]
        if not all(s > 0 for s in scores):
            continue
        score = sum(scores)
        first_pos = text_lower.find(keywords[0].lower())
        snip_start = max(0, first_pos - 100)
        snip_end = min(len(text), first_pos + 250)
        snippet = text[snip_start:snip_end].replace("\n", " | ").strip()
        if snip_start > 0:
            snippet = "..." + snippet
        if snip_end < len(text):
            snippet = snippet + "..."
        hits.append({
            "path": path,
            "ext": meta.get("ext", ""),
            "score": score,
            "snippet": snippet,
        })
    hits.sort(key=lambda h: -h["score"])
    return hits[:top_k]


def get_python_file(rel_path: str, max_chars: int = 30000) -> dict[str, Any]:
    max_chars = bounded_int(max_chars, name="max_chars", minimum=256, maximum=60_000)
    dump = load_python_dump()
    meta = dump.get(rel_path)
    if not meta:
        candidates = [p for p in dump if p.endswith(rel_path) or rel_path in p]
        if len(candidates) == 1:
            rel_path = candidates[0]
            meta = dump[rel_path]
        else:
            return {
                "path": rel_path,
                "error": f"not found (similar: {candidates[:5]})" if candidates
                         else "not found in the public facade corpus (use elf_python_index)",
            }
    text = meta.get("text", "")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[... truncated, full length: {meta.get('char_count', 0)} chars]"
    return {
        "path": rel_path,
        "ext": meta.get("ext", ""),
        "text": text,
        "char_count": meta.get("char_count", 0),
        "truncated": truncated,
    }
