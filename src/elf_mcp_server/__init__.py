"""ELF-mcp-server: MCP server providing ELF600 electromagnetic field analysis documentation.

ELF600 (https://www.science-solutions.jp/elf/) is a BEM-based commercial
electromagnetic analysis suite (MAGIC magnetostatic / ELFIN electrostatic /
BEAM particle tracking solvers, with eddy current support in MAGIC via
MAB/MAT/MBB elements).

This server exposes MCP tools plus one prompt: curated documentation,
workflow recipes, public PM/BLDC/SPM/IPM/IM/SynRM/SRM/AFPM/linear/
stepper/wound-field/reluctance/hysteresis motor and WPT/MRI/IH/transformer/
accelerator-electromagnet/actuator/maglev/brake/NDT/magnetic-gear/voice-coil/
relay-solenoid/Hall-sensor/clutch/benchmark/numeric-anchor/FLUM-law/
inductance-energy/Faraday-frequency-sweep/force-torque-gradient/AC-loss/magnetic-circuit/
permanent-magnet/transformer-coupling sample-deck playbooks, public quality
labels, physical-quantity coverage, validation matrices, observable-contract
quality audits, cross-validation audits, duplicate/reuse audits,
motor-readiness audits, ELF/radia/MMM hybrid motor routing,
2D MMM/BEM-like motor quick checks,
local simulation handoff contracts,
RunResult file parsing, numeric efficiency-map grids,
original help/example/link/Python-facade summaries, and compact planning aids for
authoring ELF input files, plus release-readiness gates for MCP maintainers.
"""

__version__ = "1.62.1"
