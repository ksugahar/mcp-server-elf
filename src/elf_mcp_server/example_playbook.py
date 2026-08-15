"""Public-safe example playbook cards derived from original public patterns.

The cards are summaries: paths, detected SOL blocks, element families,
keywords, and workflow hints. They intentionally avoid solver outputs or
machine-local paths.
"""
from __future__ import annotations

import re
from typing import Any

from .examples_access import load_examples_dump


_SOL_RE = re.compile(r"^\s*SOL\s+([A-Z0-9]+)", re.IGNORECASE | re.MULTILINE)
_NB_NAME_RE = re.compile(r"\bNB\s*\(\s*NAME\s*,\s*([A-Z0-9]+)", re.IGNORECASE)
_ELEMENT_RE = re.compile(
    r"\b(?:"
    r"MGR|MCO|MJH|MCL|MCM|MMB|MMT|MMP|MMS|MWL|MWV|MAB|MAT|MBB|"
    r"EGR|ECO|ESH|ESS|ESN|ESC|EMB|EQL|"
    r"BGR|B[A-Z]{2}"
    r")(?:[0-9]?[TKR]?)?\b",
    re.IGNORECASE,
)
_KEY_RE = re.compile(r"^\s*([A-Z][A-Z0-9]{2,5})\b", re.IGNORECASE | re.MULTILINE)
_TOKEN_STOP = {"END", "PRE", "SOL", "USE", "TIME", "PASS", "NOGO", "LAST", "STOP", "MODEL"}


_FEATURE_RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("pm-magnet", ("MWL", "MWV", "HBRM", "MAGNE"), "permanent magnet or magnetization setup"),
    ("coil-current", ("MCL", "COI1", "AMP1", "AMP1I", "VOL1"), "coil excitation or pickup winding"),
    ("field-map", ("SOL FIEL", "MCO", "MJH", "DMEG"), "field evaluation points or maps"),
    ("flux-linkage", ("SOL FIXA", "FLUM", "EMFM"), "flux linkage, EMF, or inductance extraction"),
    ("maxwell-force", ("SOL FORT", "MCM", "SELM", "SEL1"), "Maxwell-stress force or torque"),
    ("lorentz-force", ("SOL FIXB", "FIXB"), "Lorentz force on current-carrying coils"),
    ("element-force", ("SOL FORC", "FORC"), "surface/element magnetic force"),
    ("soft-iron", ("MMB", "MMP", "MMS", "HBCU", "HBUN"), "magnetic material and B-H curve"),
    ("eddy-current", ("MAB", "MAT", "MBB", "OHM2", "STED"), "conducting body or eddy-current problem"),
    ("sinusoidal-ac", ("SOL MOMC", "FREQ", "CMU1", "CMU1I"), "linear sinusoidal/complex magnetic analysis"),
    ("motion", ("MOV1", "ORI1", "TIME"), "time stepping, motion, or rotor-angle sweep"),
    ("lamination", ("HBA1", "HBA2", "VEC1", "VEC3"), "anisotropy, vector direction, or lamination"),
    ("mesh-script", ("AA(", "ME(", "BE(", "MN(", "RB("), "IEmesh procedural geometry"),
    ("electrostatic", ("USE  ELFIN", "EDCU", "VOL1", "ECO"), "ELFIN electrostatic workflow"),
    ("beam", ("USE  BEAM", "RELA", "BINT", "FILE"), "BEAM particle trajectory workflow"),
]


def _base(path: str) -> str:
    return path.rsplit(".", 1)[0]


def _text_for(path: str, dump: dict[str, dict[str, Any]]) -> str:
    return dump.get(path, {}).get("text", "")


def _companions(path: str, dump: dict[str, dict[str, Any]]) -> list[str]:
    base = _base(path)
    exts = ["mei", "model", "props", "txt"]
    return [f"{base}.{ext}" for ext in exts if f"{base}.{ext}" in dump]


def _detect_features(text: str, solver: str, category: str) -> list[str]:
    hay = text.upper()
    found = []
    for name, needles, _desc in _FEATURE_RULES:
        if any(n.upper() in hay for n in needles):
            found.append(name)
    if category.upper() in {"IPM", "MT"} and "motor" not in found:
        found.append("motor")
    if solver.upper() == "ELFIN" and "electrostatic" not in found:
        found.append("electrostatic")
    if solver.upper() == "BEAM" and "beam" not in found:
        found.append("beam")
    return sorted(found)


def _hint(features: list[str], solver: str, category: str) -> str:
    feature_set = set(features)
    if "motor" in feature_set or category.upper() == "IPM":
        return "Use as a rotating-machine template: mesh, solve, then post-process field/flux/force over angle."
    if "flux-linkage" in feature_set:
        return "Use when you need coil flux, inductance, mutual inductance, or back-EMF extraction."
    if "maxwell-force" in feature_set:
        return "Use when force or torque should be integrated on a stress surface rather than body elements."
    if "sinusoidal-ac" in feature_set:
        return "Use for linear AC response, complex permeability, and frequency-domain sweeps."
    if "eddy-current" in feature_set:
        return "Use for conductive bodies, transient diffusion, or eddy-current loss studies."
    if solver.upper() == "ELFIN":
        return "Use as an electrostatic field template: potentials/material curves first, field extraction second."
    if solver.upper() == "BEAM":
        return "Use after field generation when particle trajectories or beam optics are the target."
    return "Use as a compact starting template for this solver/category; inspect the paired .mei for geometry."


def _dedupe_sorted(items: list[str], max_items: int) -> list[str]:
    out = []
    seen = set()
    for item in items:
        u = item.upper()
        if u in _TOKEN_STOP:
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= max_items:
            break
    return out


def build_example_cards(
    limit: int = 100,
    solver: str | None = None,
    category: str | None = None,
    feature: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    """Build compact cards from public example-pattern summaries.

    Returns up to ``limit`` original public-pattern cards across MAGIC, ELFIN,
    and BEAM.
    """
    dump = load_examples_dump()
    solver_filter = solver.upper() if solver else None
    category_filter = category.lower() if category else None
    feature_filter = feature.lower() if feature else None
    query_words = [q.lower() for q in (query or "").split() if q.strip()]

    cards: list[dict[str, Any]] = []
    for path, meta in sorted(dump.items()):
        if meta.get("ext") != "mai":
            continue
        solver_name = meta.get("solver", "")
        cat = meta.get("category", "")
        if solver_filter and solver_name.upper() != solver_filter:
            continue
        if category_filter and cat.lower() != category_filter:
            continue

        companions = _companions(path, dump)
        text_parts = [_text_for(path, dump)] + [_text_for(p, dump) for p in companions]
        text = "\n".join(text_parts)
        features = _detect_features(text, solver_name, cat)
        if feature_filter and not any(feature_filter in f.lower() for f in features):
            continue
        if query_words:
            hay = " ".join([path, solver_name, cat, " ".join(features), text]).lower()
            if not all(q in hay for q in query_words):
                continue

        sol_blocks = _dedupe_sorted(_SOL_RE.findall(meta.get("text", "")), 8)
        elements = _dedupe_sorted(_NB_NAME_RE.findall(text) + _ELEMENT_RE.findall(text), 10)
        keywords = _dedupe_sorted(_KEY_RE.findall(meta.get("text", "")), 12)
        cards.append({
            "path": path,
            "solver": solver_name,
            "category": cat,
            "companions": companions,
            "sol_blocks": sol_blocks,
            "elements": elements,
            "keywords": keywords,
            "features": features,
            "hint": _hint(features, solver_name, cat),
        })

    def sort_key(card: dict[str, Any]) -> tuple[int, str, str]:
        solver_rank = {"MAGIC": 0, "ELFIN": 1, "BEAM": 2}.get(card["solver"], 9)
        return solver_rank, card["category"], card["path"]

    cards.sort(key=sort_key)
    return cards[:max(1, min(limit, 200))]


def format_example_cards(cards: list[dict[str, Any]]) -> str:
    """Format cards for MCP text output."""
    if not cards:
        return "No example cards match the requested filters."
    lines = [f"# ELF example playbook ({len(cards)} cards)", ""]
    for i, card in enumerate(cards, 1):
        companions = ", ".join(card["companions"]) if card["companions"] else "-"
        lines.append(f"## {i:03d}. {card['path']}")
        lines.append(f"- solver/category: {card['solver']} / {card['category']}")
        lines.append(f"- companion files: {companions}")
        lines.append(f"- SOL: {', '.join(card['sol_blocks']) or '-'}")
        lines.append(f"- elements: {', '.join(card['elements']) or '-'}")
        lines.append(f"- features: {', '.join(card['features']) or '-'}")
        lines.append(f"- use when: {card['hint']}")
        lines.append(f"- drilldown: elf_examples_get(\"{card['path']}\")")
        lines.append("")
    return "\n".join(lines).rstrip()
