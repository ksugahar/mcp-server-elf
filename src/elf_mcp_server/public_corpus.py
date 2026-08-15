"""Original, redistributable summaries used by legacy corpus tools.

No vendor help page, wiki page, example file, wrapper, or error table is copied
into this module.  The entries are short descriptions written for this server.
"""
from __future__ import annotations


def _entry(title: str, text: str, **metadata):
    return {"title": title, "text": text, "char_count": len(text), **metadata}


HELP = {
    "guides/analysis-files": _entry(
        "Analysis input files",
        "An analysis input names the solver family, material and source data, requested solution blocks, and termination marker. Validate required blocks before local execution.",
    ),
    "guides/mesh-files": _entry(
        "Mesh input files",
        "A mesh script describes coordinates, regions, elements, and optional grouping. A compiled mesh is an input artifact, not a solver result.",
    ),
    "guides/magic": _entry(
        "MAGIC workflow",
        "Use MAGIC for magnetic field models, including static and supported conducting-region workflows. Separate geometry preparation, material assignment, excitation, solve intent, and observable requests.",
    ),
    "guides/elfin": _entry(
        "ELFIN workflow",
        "Use ELFIN for electrostatic field models. Define conductor potentials, dielectric regions, boundary conditions, and field-evaluation requests explicitly.",
    ),
    "guides/beam": _entry(
        "BEAM workflow",
        "Use BEAM for charged-particle trajectory studies after the required field data has been prepared. Record charge, mass, initial state, integration settings, and stopping criteria.",
    ),
    "guides/materials": _entry(
        "Magnetic materials",
        "Keep material identifiers stable. For nonlinear magnetic materials, preserve units, monotonic ordering of tabulated points, and a documented extrapolation policy.",
    ),
    "guides/observables": _entry(
        "Observable contracts",
        "Request only observables needed by the engineering decision, such as field probes, flux linkage, force, torque, loss proxy, or trajectory data. Record units and sign conventions.",
    ),
}

EXAMPLES = {
    "public/magic/magnetostatic.mai": _entry(
        "Minimal magnetic-analysis pattern",
        "USE MAGIC\nPRE  # define sources and materials\nSOL MOME\nSOL FIEL\nEND",
        ext="mai", solver="MAGIC", category="PUBLIC_PATTERN",
    ),
    "public/magic/ac_conductor.mai": _entry(
        "Magnetic conducting-region pattern",
        "USE MAGIC\nPRE  # define frequency, excitation, and conducting material\nSOL MOMC\nSOL FIEL\nEND",
        ext="mai", solver="MAGIC", category="PUBLIC_PATTERN",
    ),
    "public/elfin/electrostatic.mai": _entry(
        "Electrostatic pattern",
        "USE ELFIN\nPRE  # define potentials and dielectric data\nSOL MOME\nSOL FIEL\nEND",
        ext="mai", solver="ELFIN", category="PUBLIC_PATTERN",
    ),
    "public/beam/trajectory.mai": _entry(
        "Particle-trajectory pattern",
        "USE BEAM\nPRE  # define particle and field-file contract\nSOL BEAM\nEND",
        ext="mai", solver="BEAM", category="PUBLIC_PATTERN",
    ),
}

WIKI = {
    "public-boundary": _entry(
        "Public boundary",
        "This package contains original summaries and public input decks. Product manuals, vendor wiki text, wrapper source, binaries, solver results, and commercial benchmark values are not bundled.",
        url="https://www.science-solutions.jp/elf/",
    ),
    "workflow-selection": _entry(
        "Workflow selection",
        "Choose the solver family from the physical problem: magnetic field, electrostatic field, or charged-particle trajectory. Do not route unknown solver names silently.",
        url="https://www.science-solutions.jp/elf/",
    ),
}

PYTHON = {
    "facade/MotorSpec": _entry(
        "MotorSpec contract",
        "A public MotorSpec records topology, dimensions, materials, winding intent, operating points, objectives, and constraints without importing a product wrapper.",
        ext="schema",
    ),
    "facade/RunRequest": _entry(
        "RunRequest contract",
        "A RunRequest is a handoff description for a user-local backend. It contains artifact identifiers and requested observables but never launches a solver from this server.",
        ext="schema",
    ),
    "facade/RunResult": _entry(
        "RunResult contract",
        "A RunResult contains normalized observables, units, warnings, and artifact digests. Raw product output text and local paths remain outside public MCP responses.",
        ext="schema",
    ),
}
