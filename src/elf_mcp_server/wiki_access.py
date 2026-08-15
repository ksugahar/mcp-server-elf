"""Access original public summaries through the legacy wiki API.

Vendor wiki pages are linked where useful but their text is not bundled.

Functions:
    load_wiki_dump()                  -> dict[str, dict]
    list_wiki_pages()                 -> list of {name, url, char_count, title}
    search_wiki(query, top_k=10)      -> ranked snippet matches
    get_wiki_page(name, max_chars=...) -> full extracted text
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from .guards import bounded_int
from .public_corpus import WIKI


@lru_cache(maxsize=1)
def load_wiki_dump() -> dict[str, dict[str, Any]]:
    return WIKI


def list_wiki_pages() -> list[dict[str, Any]]:
    dump = load_wiki_dump()
    out = []
    for name, meta in sorted(dump.items()):
        out.append({
            "name": name,
            "url": meta.get("url", ""),
            "title": meta.get("title", ""),
            "char_count": meta.get("char_count", 0),
        })
    return out


def search_wiki(query: str, top_k: int = 10) -> list[dict[str, Any]]:
    top_k = bounded_int(top_k, name="top_k", minimum=1, maximum=100)
    dump = load_wiki_dump()
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    hits = []
    for name, meta in dump.items():
        text = meta.get("text", "")
        text_lower = text.lower()
        scores = [text_lower.count(kw.lower()) for kw in keywords]
        if not all(s > 0 for s in scores):
            continue
        score = sum(scores)
        first_pos = text_lower.find(keywords[0].lower())
        snip_start = max(0, first_pos - 80)
        snip_end = min(len(text), first_pos + 220)
        snippet = text[snip_start:snip_end].replace("\n", " ").strip()
        if snip_start > 0:
            snippet = "..." + snippet
        if snip_end < len(text):
            snippet = snippet + "..."
        hits.append({
            "name": name,
            "url": meta.get("url", ""),
            "title": meta.get("title", ""),
            "score": score,
            "snippet": snippet,
        })
    hits.sort(key=lambda h: -h["score"])
    return hits[:top_k]


def get_wiki_page(name: str, max_chars: int = 30000) -> dict[str, Any]:
    max_chars = bounded_int(max_chars, name="max_chars", minimum=256, maximum=60_000)
    dump = load_wiki_dump()
    meta = dump.get(name)
    if not meta:
        candidates = [p for p in dump if name in p]
        if len(candidates) == 1:
            name = candidates[0]
            meta = dump[name]
        else:
            return {
                "name": name,
                "error": f"not found (similar: {candidates[:5]})" if candidates
                         else "not found in the public summary corpus (use elf_wiki_index)",
            }
    text = meta.get("text", "")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[... truncated, full length: {meta.get('char_count', 0)} chars]"
    return {
        "name": name,
        "url": meta.get("url", ""),
        "title": meta.get("title", ""),
        "text": text,
        "char_count": meta.get("char_count", 0),
        "truncated": truncated,
    }
