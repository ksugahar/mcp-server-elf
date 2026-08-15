# ELF-mcp-server

[![PyPI](https://img.shields.io/pypi/v/ELF-mcp-server.svg)](https://pypi.org/project/ELF-mcp-server/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**MCP server providing ELF600 electromagnetic field analysis documentation** — file formats, solver options, element types, workflow recipes, and ELF-runnable public input decks for the [ELF600](https://www.science-solutions.jp/elf/) BEM-based electromagnetic analysis suite (MAGIC magnetostatic, ELFIN electrostatic, BEAM particle tracking).

This server does **not** execute ELF600 simulations — it provides curated documentation and public `.mai`/`.meg` input decks that AI coding assistants (Claude Code, Cursor, etc.) can consult while authoring ELF input files.

---

## Features

**100+ compatibility tools, four canonical typed tools, five Resources/resource templates, and one prompt** provide curated engineering guidance, public sample decks, workflow contracts, motor-design plans, metadata gates, and user-local handoff schemas. Product documentation snapshots and wrapper source are not bundled. The authoritative runtime counts are returned by `elf_overview()`:

| Tool family | Purpose | Files |
|---|---|---|
| `elf_usage(topic)` | 32 curated topics — high-level recipes | (knowledge.py) |
| `elf_catalog_page / elf_search / elf_read / elf_contract_gate` | Canonical typed MCP interface | bounded structured responses |
| `elf://guides/* / elf://corpus/* / elf://topics/{topic}` | Stable MCP Resources | original public summaries |
| `elf_help_*(...)` | Compatibility access to original summaries | no product-help snapshot |
| `elf_examples_*(...)` | Compatibility access to original example patterns | no product examples |
| `elf_sample_decks_*(...)` | Lab-authored ELF-runnable public `.mai`/`.meg` sample decks | 1600 cases, 3200 input files |
| `elf_recipe_*(...)` | Workflow decision cards for elements, PRE/SOL blocks, outputs, checks, and pitfalls | public-safe recipes |
| `elf_wiki_*(...)` | Compatibility access to public link summaries | no vendor-wiki text |
| `elf_python_*(...)` | Compatibility access to public facade contracts | no vendor wrappers/configs |
| `elf_python_interface_design(topic)` | Public facade/API design above a user-local product backend | policy, schema, backend, validation |
| `elf_python_api_manual(topic)` | LLM-oriented Python facade manual | call order, lint rules, examples |
| `elf_python_api_schema / motor_spec_lint / deck_lint / run_contract / meg_generation_plan / 2d_motor_template` | Concrete public Python facade contracts | MotorSpec, DeckBundle, RunRequest, MEG backend routing |
| `elf_python_motor_design_plan / motor_sweep_matrix / motor_observable_contract` | Motor design API layer | variables, objectives, DOE rows, parser keys, validation |
| `elf_python_motor_dq_axis_map_plan / motor_mtpa_search_plan / reluctance_motor_design_plan` | DQ and reluctance motor API layer | Id/Iq maps, PM-vs-reluctance torque, MTPA, SynRM/SRM saliency |
| `elf_python_motor_winding_layout_plan / motor_topology_parameter_plan / motor_demag_margin_plan / motor_drive_cycle_plan / motor_optimization_study_plan` | Motor design-suite API layer | winding layout, geometry variables, demag screening, duty points, constrained ranking |
| `elf_python_motor_voltage_field_weakening_plan / motor_cogging_ripple_plan / motor_airgap_harmonics_nvh_plan / motor_thermal_network_plan / motor_manufacturing_tolerance_plan / motor_material_variation_plan / motor_feasibility_study` | Production-style motor design gates | voltage limits, ripple, NVH orders, thermal screening, tolerance, materials, feasibility |
| `elf_python_motor_operating_point_run_queue / motor_inverter_pwm_harmonic_plan / motor_saturation_inductance_map_plan` | Motor execution-planning API layer | operating-point rows, PWM sidebands, saturated Ld/Lq current maps |
| `elf_python_run_result_parse / run_result_parse_path / motor_efficiency_map_from_results / motor_optimization_loop / motor_ngsolve_result_crosscheck / motor_drawing_bom_handoff / motor_rotor_stress_retention_plan / motor_validation_scorecard` | Closed-loop motor design workflow | parsed observables, completed-result file scanning, numeric eta grids, candidate ranking, NGSolve reconciliation, rotor stress screening, drawing/BOM handoff, scorecards |
| `elf_python_motor_efficiency_map_plan / motor_loss_model_contract / motor_torque_speed_envelope / induction_slip_sweep_plan` | Motor map API layer | efficiency maps, loss terms, torque-speed clipping, IM slip |
| `elf_python_motor_market_brief / motor_design_agent_handoff` | Spec-to-design-agent workflow | robot/drone SPM, GUI-free backend handoff, drawings/BOM/prototype gates |
| `elf_python_ngsolve_validation_plan / ngsolve_validation_script` | Executable open multiphysics validation | NGSolve thermal, NVH, and stress script generation |
| `elf_public_promotion(...)` | Public-safe promotion copy for the 1600-case corpus | Japanese/English drafts |

Legacy `_*` index/search/get tools remain for compatibility. New clients should
prefer Resources plus `elf_catalog_page`, `elf_search`, `elf_read`, and
`elf_contract_gate`, whose input limits and semantic output schemas are explicit.
The recipe family also has `elf_plan_workflow(goal)`, which chooses a short
public-safe recipe sequence from a natural-language analysis goal.
The sample deck family has `elf_sample_decks_index/search/route/handoff/validation/readiness/motor_readiness/motor_hybrid_router/motor_mmm_quick_check/validation_matrix/observable_contracts/cross_validation/duplicates/quality/physics/representatives/get/playbook`
for ELF-runnable public `.mai`/`.meg` decks. `elf_sample_decks_route(goal)`
maps a user prompt such as "IPM hairpin motor flux linkage" or
"WPT misalignment" to the most relevant public deck families, follow-up MCP
calls, validation levels, and representative `.mai` files.
`elf_sample_decks_validation()` summarizes the validation level and public
limitations for the corpus before an agent claims a deck is validated.
`elf_sample_decks_representatives()` gives a curated first-stop tour through
the 1600-case corpus. `elf_sample_decks_quality()` summarizes the public
quality labels: 674 `gold_numeric_invariant` cases, 500
`silver_observable_contract` cases, and 426 `silver_proxy_energy` cases, and reports publication quality gates for pairing,
manifest coverage, public-boundary hygiene, solver-output exclusion, and the
`application/motor` hierarchy. `elf_sample_decks_physics()` maps the corpus to
physical quantities such as flux linkage, inductance/co-energy, force/torque,
AC loss, permanent-magnet flux, transformer coupling, WPT coupling, and MRI
shield response. `elf_sample_decks_validation_matrix()` joins quantities,
quality labels, validation methods, representative decks, and next MCP calls
into a prompt-routing audit table. `elf_sample_decks_observable_contracts()`
audits the 500-case quality upgrade where public `.mai` decks expose the
expected FLUM/OHM2/FREQ/HBRM/HBCU markers for their mapped physical quantities.
`elf_sample_decks_cross_validation()` audits whether every
family has an independent NGSolve cross-check, separates gold dual-invariant
families from silver proxy-energy families, and lists silver-to-gold upgrade
candidates. `elf_sample_decks_duplicates()` audits exact duplicate `.mai` +
`.meg` pairs and separates those deletion candidates from intentional `.mai`
or `.meg` reuse that MCP clients should collapse or summarize rather than
delete. `elf_local_simulation_handoff(goal)` turns a prompt into a public-safe
handoff contract for a user-local ELF/MAGIC runner: selected deck families,
physical quantities, runner input fields, parser output fields, and the motor
iteration loop. It does not execute ELF/MAGIC or publish solver outputs.
`elf_mcp_readiness()` aggregates public quality gates, cross-validation gates,
duplicate checks, local-runner handoff boundary checks, and key route checks
into a release-readiness report for maintainers. `elf_motor_readiness()`
audits the 652-case motor subset across 37 motor families, separates breadth
from validation-depth gaps, and lists radia-motor / radia-ngsolve targets such
as back-EMF, cogging torque, Ld/Lq, MTPA, induction slip loss, and reluctance
torque. `elf_motor_hybrid_router(goal)` dispatches motor prompts across public
ELF deck routes, radia-motor 2D MMM/BEM-like quick checks, the canonical
`ngsolve_age` and `hdiv_mmm_hcurl_eddy_bubble` validation lanes, and the
user-local ELF/MAGIC runner contract.
`elf_motor_mmm_quick_check()` provides the public-safe first-order magnetic
circuit / MMM-like sign-and-scale check directly in this MCP server.
`elf_public_promotion()` returns public-safe Japanese/English
promotion copy for the corpus.
The Python family also has
`elf_python_team28()`: a compact 28-case seed manifest from the public motor
cases for ELF Python-interface orchestration. `team28` is not a normal
ELF GUI/CLI deck-execution workflow. Solver outputs, comparison metrics,
executable orchestration state, and Python-interface runtime state are not
bundled.
`elf_python_interface_design(topic)` defines the public Python facade policy:
the product-side Python implementation is reference material rather than a
required dependency, the vendor DLL is an immutable product boundary, and the
public MCP/Python layer may add typed schemas, deck builders, validators,
routers, and result contracts above that boundary.
The concrete facade tools add `MotorSpec` / `DeckBundle` / `RunRequest` /
`RunResult` vocabulary, dry-run `.mai` lint for requested observables, and
`.meg` generation routing. Recommended `.meg` paths are Cubit mesh export for
3D or CAD-like geometry, Netgen for deterministic 2D motor cross-sections, and
constrained LLM-authored 2D templates for simple prompt-to-deck prototypes
that still must pass lint and validation gates.
`elf_python_2d_motor_template()` returns a bounded radial-layer / angular-feature
schema for LLM-assisted 2D drafting before deterministic remeshing.
The motor-design tools add explicit design variables, objective-specific
observables, sweep/DOE rows, parser keys, and validation gates so an LLM can
iterate a motor design without inventing hidden parameters.
The map-oriented tools add motor-design deliverables that users naturally ask
for: efficiency-map torque/speed grids, loss-term contracts, torque-speed
envelope clipping, and induction-motor slip sweeps with synchronous speed,
slip frequency, rotor-speed, and rotor-copper-loss relations.
The dq/reluctance tools add Id/Iq maps, PM-vs-reluctance torque decomposition,
MTPA current-angle scans, SynRM saliency planning, and SRM aligned/unaligned
inductance checks.
The design-suite tools add phase-belt winding layouts, topology-specific
geometry variables, PM demagnetization screening, weighted drive-cycle points,
and constrained optimization-study plans so an LLM can move from user specs to
ranked candidates without hiding assumptions.
The production-style design gates add voltage/current limit and field-weakening
plans, cogging/ripple reduction contracts, air-gap harmonic force-order routing
for NVH, reduced thermal-network screening, manufacturing tolerance DOE,
material variation sweeps, and feasibility gates that state what MCP can and
cannot claim before prototype handoff.
The closed-loop tools normalize user-local RunResult payloads into parsed
observables, rank candidates, reconcile NGSolve runtime JSON with validation
labels, and prepare drawing/BOM handoff content while keeping raw outputs and
private run directories outside the public package.
`elf_python_run_result_parse_path()` is disabled by default. To opt in, set
`ELF_MCP_RUN_ROOT` to a dedicated result-artifact directory before starting the
server. The tool rejects paths outside that root; payload-only parsing through
`elf_python_run_result_parse()` never reads local files.
The design-agent handoff tools target workflows such as robotics/drone
outer-rotor or inner-rotor SPM/PMSM: users provide specifications, the agent
routes ELF/radia/MMM validation, and downstream teams receive drawing/BOM and
prototype-gate intent without requiring the user to operate analysis software.
`elf_python_ngsolve_validation_plan()` and
`elf_python_ngsolve_validation_script()` implement the required open
multiphysics validation lane: after local electromagnetic observables are
parsed, the MCP can generate NGSolve jobs/scripts for thermal rise, NVH modal
order separation, and mechanical stress margin checks.

### MCP quick start

For MCP clients, start with `elf_overview()` to discover the server surface and
public boundary. The most useful calls while authoring ELF/MAGIC inputs are:

- `elf_python_api_manual("quickstart")` to load the LLM-oriented Python facade
  manual: policy, object vocabulary, call order, deck lint, `.meg` generation,
  local backend contract, validation rules, and examples
- `elf_sample_decks_route("IPM hairpin motor flux linkage")` to map a user
  prompt to the right sample family, playbook call, recipe, and representative
  `.mai` decks
- `elf_mcp_readiness()` to check release-quality gates before tag push
- `elf_motor_readiness()` to inspect motor-specific breadth, validation-depth
  gaps, and radia-motor strengthening targets
- `elf_motor_hybrid_router("IPM hairpin motor flux linkage and MTPA")` to
  route a motor prompt across ELF deck authoring, radia-motor MMM quick checks,
  the `ngsolve_age` and `hdiv_mmm_hcurl_eddy_bubble` validation lanes, and a
  user-local ELF/MAGIC product run
- `elf_nonlinear_magnetic_conductor_validation_gate(summary_json)` to gate
  mean-B and Joule convergence independently for a same-region nonlinear
  magnetic conductor; a converged mean field cannot certify unconverged loss
- `elf_motor_mmm_quick_check(motor_type="spm")` for a public-safe PM flux,
  back-EMF, torque, Ld/Lq, and induction slip-loss scale check before solver runs
- `elf_sample_decks_validation()` to check the public validation levels,
  counts, and limitations before claiming a deck is validated
- `elf_sample_decks_representatives()` to start from curated first-stop decks
  across motors, non-motor applications, and numeric validation anchors
- `elf_sample_decks_quality(label="gold")` to prioritize the strongest public
  numeric-invariant families
- `elf_sample_decks_physics(quantity="force")` to inspect physical-quantity
  coverage before choosing sample decks or making validation claims
- `elf_sample_decks_validation_matrix(quantity="transformer")` to map prompt
  intent to physical quantity, quality label, validation method, and first deck
- `elf_sample_decks_observable_contracts()` to inspect the 500-case
  observable-contract quality upgrade before publication
- `elf_sample_decks_cross_validation()` to audit independent cross-validation
  coverage and find any remaining validation gaps
- `elf_sample_decks_duplicates()` to check whether apparent duplicates are
  true `.mai` + `.meg` duplicates or intentional geometry/control reuse
- `elf_local_simulation_handoff("SPM motor flux linkage sweep")` to prepare
  the runner/parser contract for a user-local ELF/MAGIC execution layer
- `elf_public_promotion(audience="ja")` to draft a public-safe Japanese
  introduction of the 1600-case corpus
- `elf_plan_workflow("WPT misalignment with conducting shield")` to get both
  a recipe-level plan and related public sample-deck routes
- `elf_sample_decks_playbook(limit=20, family="pm_square")` for compact cards
  over the public PM motor decks
- `elf_sample_decks_playbook(limit=20, family="spm")` for surface-PM motor
  decks with stator coils, rotor/stator iron, and pickup coils
- `elf_sample_decks_playbook(limit=20, family="srm")` for switched-reluctance
  motor decks with salient iron and phase-pair excitation
- `elf_sample_decks_playbook(limit=20, family="induction_cage_10")` for induction
  motor cage decks with transient eddy-current pickup patterns
- `elf_sample_decks_playbook(limit=20, query="EMDLAB-style")` for 240
  EMDLAB-style decks covering BLDC/SPM, BLDC outer-rotor, SPM static-torque,
  IPM hairpin, induction, SynRM, SRM, AFPM, transformer, and benchmark
  patterns
- `elf_sample_decks_playbook(limit=20, query="Loop13 motor")` for extra IPM,
  wound-field synchronous, axial-flux PM, linear PM, and stepper motor decks
- `elf_sample_decks_playbook(limit=20, family="application")` for transformer
  MRI gradient-coil, WPT coupled-coil, induction-heating, and accelerator
  electromagnet application decks, plus actuator, maglev, separator, brake,
  NDT probe, magnetic-gear, voice-coil, relay/solenoid, Hall-sensor fixture,
  and electromagnetic-clutch decks
- `elf_sample_decks_playbook(limit=20, query="Loop10")` for the 10-cycle
  learning-loop decks across WPT, MRI, SR motor, SPM, IH, reluctance motor,
  hysteresis motor, transformer, and accelerator electromagnet families
- `elf_sample_decks_playbook(limit=20, query="Loop11")` for actuator,
  maglev bearing, magnetic separator, eddy-current brake, and NDT probe decks
- `elf_sample_decks_playbook(limit=20, query="Loop12")` for magnetic gear,
  voice-coil actuator, relay solenoid, Hall-sensor fixture, and
  electromagnetic-clutch decks
- `elf_sample_decks_playbook(limit=20, query="Loop13 application")` for WPT
  misalignment, MRI gradient sequence, transformer leakage, IH susceptor, and
  accelerator corrector decks
- `elf_sample_decks_route("numeric validation anchor FLUM invariant")` for
  decks whose ELF `FLUM` ratios/signs and independent NGSolve proxy invariants
  are both checked
- `elf_sample_decks_route("FLUM law current linearity superposition")` for
  64 numeric FLUM-law decks that validate magnetic flux linkage against
  current, turns, sign, distance, symmetry, superposition, and cancellation
  invariants
- `elf_sample_decks_route("inductance co-energy FLUM turn scaling")` for
  100 numeric decks validating `FLUM`-derived inductance `L = Phi/I` and
  co-energy `W = 1/2 sum(I Phi)` across current, turns, distance, symmetry,
  superposition, and add/cancel energy invariants
- `elf_sample_decks_route("force torque co-energy gradient")` for 100 numeric
  decks validating `FLUM`-derived co-energy force/torque-gradient behavior
  across distance-force sign, current-square scaling, mirror/lateral
  symmetry, angular `dW/dtheta`, and balanced-torque invariants
- `elf_sample_decks_route("AC loss frequency square OHM2")` for 100 numeric
  MOMC/FREQ/OHM2 decks validating AC-loss proxy behavior across frequency
  square, current square, resistivity inverse, distance decay, symmetry,
  add/cancel, thickness, width, and combined `I-f-rho` scaling invariants
- `elf_sample_decks_route("magnetic circuit air gap HBCU")` for 100 numeric
  MMB8T/HBUN/HBCU decks validating magnetic-circuit proxy behavior across
  B-H slope, air-gap reluctance, core area/depth, current/turn scaling,
  mirror sanity, return-yoke continuity, and add/cancel bias invariants
- `elf_sample_decks_route("permanent magnet HBRM polarity FLUM")` for 100
  numeric MWL8T/HBRM/HBCN/VEC3 decks validating permanent-magnet pickup
  behavior across remanence scaling, distance decay, magnet dimensions,
  magnetization angle, polarity reversal, symmetry, add/cancel, array count,
  and pickup-turn scaling invariants
- `elf_sample_decks_search("HBCN FLUM", ext="mai")` to find reusable input
  patterns
- `elf_sample_decks_search("SPM HBRM FLUM", ext="mai")` to find surface-PM
  motor setup patterns
- `elf_sample_decks_search("SRM reluctance FLUM", ext="mai")` to find
  switched-reluctance motor setup patterns
- `elf_sample_decks_search("WPT MOMC FLUM", ext="mai")` to find wireless
  power-transfer AC coupling patterns
- `elf_sample_decks_search("MRI OHM2 FREQ", ext="mai")` to find AC shielding
  and eddy-current setup patterns
- `elf_sample_decks_search("induction motor cage OHM2 FLUM", ext="mai")` to find
  induction-motor cage and pickup setup patterns
- `elf_sample_decks_search("EMDLAB-style IPM hairpin FLUM", ext="mai")` to find
  IPM hairpin motor setup patterns
- `elf_sample_decks_search("EMDLAB-style SynRM flux-barrier FLUM", ext="mai")`
  to find synchronous-reluctance flux-barrier setup patterns
- `elf_sample_decks_search("EMDLAB-style AFPM linearized-airgap FLUM", ext="mai")`
  to find axial-flux PM line-airgap setup patterns
- `elf_sample_decks_search("Loop13 wound-field synchronous FLUM", ext="mai")`
  to find wound-field synchronous motor setup patterns
- `elf_sample_decks_search("Loop13 stepper motor detent FLUM", ext="mai")` to
  find stepper motor setup patterns
- `elf_sample_decks_search("accelerator electromagnet FLUM", ext="mai")` to
  find coil/yoke electromagnet setup patterns
- `elf_sample_decks_search("IH induction-heating MOMC", ext="mai")` to find
  induction-heating AC conductor setup patterns
- `elf_sample_decks_search("Loop11 actuator plunger FLUM", ext="mai")` to find
  solenoid/plunger actuator setup patterns
- `elf_sample_decks_search("Loop11 NDT eddy-current probe OHM2", ext="mai")` to
  find eddy-current inspection probe setup patterns
- `elf_sample_decks_search("Loop12 magnetic gear HBCN FLUM", ext="mai")` to
  find PM magnetic-gear setup patterns
- `elf_sample_decks_search("Loop12 electromagnetic clutch OHM2", ext="mai")` to
  find AC clutch and conducting-plate setup patterns
- `elf_sample_decks_search("Loop13 WPT misalignment OHM2", ext="mai")` to find
  wireless-power-transfer misalignment setup patterns
- `elf_sample_decks_get("application/motor/pm_cosine_pickup_72/pm001/pm001.mai")` to open a
  concrete public deck
- `elf_python_team28()` to inspect the Python-interface seed manifest
- `elf_python_interface_design("overview")` to inspect the public Python
  facade contract, product-Python reference policy, immutable DLL boundary,
  motor schemas, backend protocol, validation gates, and vendor proposal
- `elf_python_api_schema("spm")` to get the concrete public MotorSpec,
  DeckBundle, RunRequest, and RunResult vocabulary plus a JSON template
- `elf_python_deck_lint(mai_path="application/motor/pm_cosine_pickup_72/pm001/pm001.mai", requested_observables="flux_linkage,back_emf_constant")`
  to dry-run check a public `.mai` deck before local execution
- `elf_python_run_contract("SPM motor back EMF sweep", motor_type="spm")` to
  prepare a user-local backend request contract without calling product code
- `elf_python_motor_design_plan("IPM torque density and Ld Lq", motor_type="ipm")`
  to choose design variables, studies, observables, and validation gates
- `elf_python_motor_design_plan("PM-assisted SynRM efficiency map", motor_type="pm_assisted_synrm")`
  or `motor_type="bldc"`, `"line_start_pm"`, `"deep_bar_induction"`,
  `"flux_switching_pm"`, `"vernier_pm"`, `"transverse_flux_pm"`,
  `"slotless_pm"`, `"claw_pole"`, or `"commutator_dc"` to start the
  extended motor-model workflows
- `elf_python_motor_sweep_matrix(motor_type="spm", objective="back_emf_target", budget=9)`
  to create explicit DOE rows for local product runs
- `elf_python_motor_dq_axis_map_plan(motor_type="ipm")` to create Id/Iq map
  points with PM and reluctance torque terms split out
- `elf_python_motor_mtpa_search_plan(motor_type="ipm")` to scan current angle
  candidates for torque per amp before local RunResult confirmation
- `elf_python_reluctance_motor_design_plan(motor_type="synrm")` to plan
  SynRM/SRM saliency, Ld/Lq extraction, and reluctance torque studies
- `elf_python_motor_winding_layout_plan(stator_slots=48, pole_pairs=4)` to
  create slot/phase assignment, q, coil-pitch, and winding-factor proxy
- `elf_python_motor_topology_parameter_plan(motor_type="ipm", rotor_topology="inner_rotor")`
  to expose topology-specific geometry variables, ranges, constraints, and
  region labels
- `elf_python_motor_demag_margin_plan(motor_type="spm", temperature_c=120)` to
  record PM hot-Br, Hcj, negative-Id screening, required field observables, and
  risk labels
- `elf_python_motor_voltage_field_weakening_plan(motor_type="ipm", dc_bus_v=48)`
  to screen voltage margin and high-speed negative-Id demand
- `elf_python_motor_cogging_ripple_plan(stator_slots=48, pole_pairs=4)` to
  separate cogging, loaded ripple, harmonic orders, and mitigation variables
- `elf_python_motor_airgap_harmonics_nvh_plan(stator_slots=48, pole_pairs=4)`
  to route slot/pole force orders into NGSolve NVH validation
- `elf_python_motor_efficiency_map_plan(motor_type="spm")` to create an
  efficiency-map torque/speed grid, required observables, loss terms, and
  postprocess outputs such as `eta_grid`
- `elf_python_run_result_parse_path(run_path="<local run directory>")` to
  normalize completed user-local JSON/CSV/text result files without returning
  raw output text or local paths
- `elf_python_motor_efficiency_map_from_results(result_payloads_json="[...]")`
  to turn parsed RunResults into numeric `eta_grid`, loss grids, coverage, and
  best-efficiency point labels with machine-checked coverage, eta-range,
  nonnegative-loss, and torque-error gates
- `elf_python_motor_loss_model_contract(motor_type="spm")` to separate copper,
  iron, magnet, mechanical, rotor, and optional inverter loss assumptions
- `elf_python_motor_torque_speed_envelope(motor_type="spm")` to clip map points
  by current-limited constant-torque and voltage-limited field-weakening regions
- `elf_python_motor_drive_cycle_plan(target_market="robot_drone")` to attach
  weighted duty points for cycle efficiency, loss, and multiphysics follow-up
- `elf_python_motor_thermal_network_plan(total_loss_w=25)` to build a reduced
  thermal screening model before NGSolve thermal validation
- `elf_python_motor_manufacturing_tolerance_plan(motor_type="spm", airgap_mm=0.8)`
  to create tolerance variables and robustness DOE rows
- `elf_python_motor_material_variation_plan(motor_type="spm", focus="all")` to
  plan magnet, steel, and conductor sensitivity sweeps
- `elf_python_motor_optimization_study_plan(motor_type="spm", objective="cycle_efficiency")`
  to define variables, constraints, ranking outputs, and validation promotion
- `elf_python_motor_feasibility_study("outer-rotor drone SPM motor")` to review
  electromagnetic, thermal, NVH, stress, manufacturing, and governance gates
- `elf_python_run_result_parse(payload="torque_nm=0.82\nloss_w=12.5")` to
  normalize local/private results into parsed observables
- `elf_python_motor_optimization_loop(motor_type="spm", objective="cycle_efficiency")`
  to rank parsed candidates and propose next DOE rows
- `elf_python_motor_ngsolve_result_crosscheck(run_result_payload="{...}", ngsolve_result_payload="{...}")`
  to reconcile local RunResult observables with NGSolve runtime JSON
- `elf_python_motor_drawing_bom_handoff(motor_type="spm", validation_label="crosscheck_pass")`
  to prepare drawing views, key dimensions, BOM, export intent, and validation
  attachments
- `elf_python_induction_slip_sweep_plan(pole_pairs=2, supply_frequency_hz=50)`
  to build an IM slip sweep with synchronous speed, slip frequency, rotor speed,
  and rotor-copper-loss relations
- `elf_python_motor_observable_contract(motor_type="ipm", study="dq_inductance")`
  to map studies to ELF markers, parser keys, validation checks, and AGE targets
- `elf_python_motor_market_brief(target_market="robot_drone", motor_type="spm", rotor_topology="outer_rotor")`
  to define robotics/drone spec intake and GUI-free user experience policy
- `elf_python_motor_design_agent_handoff("outer-rotor drone SPM motor", target_market="robot_drone")`
  to prepare design-agent deliverables, required NGSolve NVH/thermal/stress routing, and manufacturing/prototype handoff
- `elf_python_ngsolve_validation_plan("outer-rotor drone SPM motor")` to build
  required NGSolve thermal/NVH/stress jobs from public specs and parsed observables
- `elf_python_ngsolve_validation_script("outer-rotor drone SPM motor", lane="all")`
  to generate a runnable NGSolve Python validation script
- `elf_python_meg_generation_plan("2D SPM motor cross-section", dimension="2d")`
  to choose Cubit, Netgen 2D, or constrained LLM 2D `.meg` generation paths
- `elf_python_2d_motor_template("spm", pole_pairs=4, stator_slots=48)` to
  create a bounded 2D drafting template before Netgen remeshing and validation

This MCP server provides documentation, public input-deck retrieval, public
facade contracts, and open-validation script generation. It does not launch
ELF, execute product solvers, manage product licenses, or publish raw validation
outputs.

### ELF/MAGIC application input authoring

ELF/MAGIC is useful for magnetostatic and AC magnetic input authoring when the
model is expressed as `.mai` analysis control plus `.meg` mesh data. This server
turns that knowledge into MCP tools:

- 652 public motor input-deck pairs under `application/motor/`, covering
  2-pole, 4-pole, 6-pole, 8-pole,
  cosine-remanence PM pickup families, 10 explicit SPM motor examples, and
  10 SRM switched-reluctance examples, 10 induction cage examples, plus
  loop-reviewed SPM, SR motor, synchronous-reluctance motor, hysteresis motor,
  and 200 EMDLAB-style motor cases spanning BLDC/SPM, BLDC outer-rotor,
  induction, IPM hairpin, SPMSM static torque, SynRM, SRM 6/4 through 12/16,
  and AFPM variants, plus Loop13 IPM, wound-field synchronous, axial-flux PM,
  linear PM, and stepper families
- 948 public non-motor application input-deck pairs covering transformer core/pickup
  coupling, MRI gradient-coil/eddy-current shield patterns, WPT coupled coils,
  IH induction-heating workpieces, accelerator electromagnets, actuator
  plungers, maglev bearings, magnetic separators, eddy-current brakes,
  NDT eddy-current probes, magnetic gears, voice-coil actuators,
  relay solenoids, Hall-sensor fixtures, electromagnetic clutches, WPT
  misalignment, MRI gradient sequences, transformer leakage, IH susceptors,
  accelerator corrector magnets, 40 EMDLAB-style transformer/benchmark
  application decks, 10 compact numeric-validation anchor decks, and 64
  numeric FLUM-law validation decks, plus 100 numeric inductance/co-energy
  validation decks, 100 numeric force/torque-gradient validation decks, and
  100 numeric AC-loss validation decks, plus 100 numeric magnetic-circuit
  validation decks and 100 numeric permanent-magnet/magnetization validation
  decks, plus 100 numeric transformer-coupling validation decks
- playbook cards that expose each deck's SOL blocks, PRE keywords, element
  families, feature tags, and reuse hints
- representative cards that identify first-stop examples and why each is a
  good seed for agent-assisted authoring
- quality labels that distinguish `gold_numeric_invariant` families,
  500-case `silver_observable_contract` families, and broader
  `silver_proxy_energy` families
- physical-quantity coverage that links examples to FLUM-based flux linkage,
  inductance/co-energy, force/torque-gradient, AC-loss, magnetic-circuit,
  permanent-magnet, transformer-coupling, WPT, MRI, actuator, and accelerator
  quantities without bundling solver outputs
- observable-contract audits that require 500 selected public cases to expose
  the expected FLUM/OHM2/FREQ/HBRM/HBCU markers for their physical quantities
- cross-validation audits that require every public family to have an
  independent NGSolve check and distinguish `gold_numeric_invariant`,
  `silver_observable_contract`, and `silver_proxy_energy` coverage
- curated motor topics for air-gap field, flux linkage/back-EMF pickup,
  polarity/angle conventions, force outputs, and eddy-current setup
- Python-interface `team28` seed manifest for higher-level orchestration,
  without bundling runtime state or solver outputs

Useful entry points are `elf_usage(topic="ipm_motor")`,
`elf_usage(topic="motor_radia_bridge")`,
`elf_recipe_search("motor pickup")`, and
`elf_sample_decks_route("IPM hairpin motor flux linkage")`,
`elf_sample_decks_playbook(limit=50, family="pm_square")`,
`elf_sample_decks_playbook(family="spm")`, or
`elf_sample_decks_playbook(family="srm")`, or
`elf_sample_decks_playbook(family="induction_cage_10")`, or
`elf_sample_decks_playbook(query="EMDLAB-style")`, or
`elf_sample_decks_playbook(query="Loop13 motor")`. For non-motor applications,
start with `elf_sample_decks_playbook(family="application")`,
`elf_sample_decks_search("transformer FLUM")`,
`elf_sample_decks_search("WPT MOMC FLUM")`, or
`elf_sample_decks_search("MRI OHM2 FREQ")`,
`elf_sample_decks_search("IH induction-heating MOMC")`, or
`elf_sample_decks_search("accelerator electromagnet FLUM")`,
`elf_sample_decks_search("Loop11 actuator plunger FLUM")`, or
`elf_sample_decks_search("Loop11 NDT eddy-current probe OHM2")`,
`elf_sample_decks_search("Loop12 magnetic gear HBCN FLUM")`, or
`elf_sample_decks_search("Loop12 electromagnetic clutch OHM2")`, or
`elf_sample_decks_search("Loop13 WPT misalignment OHM2")`, or
`elf_sample_decks_search("FLUM law superposition")`, or
`elf_sample_decks_route("inductance co-energy FLUM turn scaling")`, or
`elf_sample_decks_route("force torque co-energy gradient")`, or
`elf_sample_decks_route("AC loss frequency square OHM2")`, or
`elf_sample_decks_route("magnetic circuit air gap HBCU")`, or
`elf_sample_decks_route("permanent magnet HBRM polarity FLUM")`.

### Public `.meg` mesh generation

For normal ELF/MAGIC authoring, the canonical mesh path is:

```text
.mei (mesh script) --> IEmesh / mesh750.exe --> .meg
```

For the bundled public sample corpus, the `.meg` files are generated as small
ASCII ELF/MAGIC mesh decks directly by lab-authored Python generators. The
writer emits `BOOK MEP 3.50`, `MGSC`, `MGR1` node records, and 8-node element
connectivity records such as `MMB8T`, `MCL8T`, `MAB8T`, and `MWL8T`. Cubit is
not used for these compact public examples.

For larger CAD/mesh workflows, Cubit-side `cubit_mesh_export` also supports
ELF-compatible `.meg` export through helper calls such as
`cubit_mesh_export.export_meg(cubit, "model.meg", DIM="T")` and
`cubit_mesh_export.export_3D_meg(cubit, "model")`. A command-style route such
as `radia_export meg "output.meg" threed labels "1:MMB,2:MWL"` is documented in
`elf_usage(topic="meg_export")`. The published examples keep the geometry
deliberately inspectable and dependency-free.

### Public lint

Before publishing, run:

```bash
python -m pytest
elf-mcp-server --selftest
elf-mcp-policy-lint
```

`elf-mcp-policy-lint` checks the public package boundary: no private validation
paths, no unrelated commercial-tool references, no bundled solver outputs
inside the public sample decks, and exact agreement with
`public_samples/VALIDATED_MANIFEST.json` and
`public_samples/PUBLICATION_BATCHES.json`. Only sample families marked
`validation: passed` in that manifest are intended for publication.
The manifest records the public verification level for each family:
`ngsolve_proxy_energy` or `ngsolve_numeric_invariant`. All 1600 public sample
decks are cross-checked with an independent NGSolve proxy-field energy gate
before they are listed. The numeric-validation anchor decks and numeric
FLUM-law decks go one level further; the numeric inductance/co-energy decks
also require `FLUM`-derived `L = Phi/I` and `W = 1/2 sum(I Phi)` invariants.
The numeric force/torque-gradient decks add `FLUM`-derived co-energy
finite-difference checks for `dW/dx` and angular `dW/dtheta` trends.
The numeric AC-loss decks add MOMC/FREQ/OHM2 decks with AC `FLUM` series
checks and NGSolve proxy invariants for `P ~ I^2 f^2 / rho` trends.
The numeric magnetic-circuit decks add MMB8T/HBUN/HBCU decks with `FLUM`
sanity checks and NGSolve proxy invariants for B-H slope, air-gap reluctance,
core area/depth, return-yoke, and add/cancel bias trends.
The numeric permanent-magnet decks add MWL8T/HBRM/HBCN/VEC3 decks with
`FLUM` sanity checks and NGSolve proxy invariants for remanence, PM volume,
magnetization angle, polarity reversal, add/cancel, array count, and pickup
turn scaling trends.
The numeric transformer-coupling decks add MMB8T/HBUN/HBCU transformer-core
decks with primary/secondary `FLUM` sanity checks and NGSolve proxy invariants
for current/turn scaling, turns ratio, B-H slope, air-gap leakage, winding
span, core area/depth, secondary offset, and buck/boost superposition trends.
Analytic `FLUM`-contract invariants and independent NGSolve proxy invariants
must both pass. No product execution or product-result data is used as public
evidence in this manifest.
MCP clients can inspect this contract with `elf_sample_decks_validation()`;
the broad proxy gate is intentionally not claimed as a full absolute field,
force, torque, or loss agreement suite.
The publication batch manifest groups the validated baseline into deterministic
100-case checkpoints: 16 full checkpoints, 1600 cases total.
No additional cases are required for this baseline. A future optional
100-case checkpoint would be 1700 cases.

Bundled data consists of repository-owned public input decks, validation
manifests, original summaries, schemas, and contracts. Product manuals, help
pages, wiki text, example files, wrappers, configuration files, binaries, and
solver outputs are excluded. See [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

### Curated topics (`elf_usage`)

Returns documentation on:

- **File formats**: `.mai` (analysis input), `.mei` (mesh script), `.meg` (compiled mesh)
- **Solvers**: MAGIC (magnetostatic, transient, AC), ELFIN (electrostatic), BEAM (particle tracking)
- **Eddy current**: MAB / MAT / MBB elements, time-stepping, sinusoidal AC (SOL MOMC)
- **Element types**: full catalog with DOF counts and symmetry restrictions (3D / 2D / Axisym)
- **B-H curves**: anisotropy (HBA1/HBA2), recoil, extrapolation
- **Motor workflows**: IPM Ld/Lq plus a radia-mcp/open-FEA concept bridge for air-gap field, torque, flux linkage/back-EMF, lamination, and eddy-current studies
- **Inductance**: Lsc (JIS) and Ll (IEEJ) with 6 samples
- **Magnetization / demagnetization** (MAGNE2)
- **Convergence** troubleshooting, error codes (160+ ELF-Q/E/W codes)
- **Force methods**: FORC vs FORT vs FIXB
- **Tools**: IEmesh, Wmap3, MagFilter2, MaiEditor3, ELF/Bench

Available topics:
```
all, overview, mai_format, mei_format, meg_format,
magic, elfin, beam, element_types, bh_curves,
sol_commands, mei_commands, ipm_motor, motor_radia_bridge, inductance,
magnetization, examples, meg_export, treasure_box,
sinusoidal, anisotropy, sted, meshing, convergence,
force_methods, errors, iemesh, tools, cln_extraction,
licensing, python_api, live_drive, force_gap_contract
```

The `cln_extraction` topic documents the 6-step ELF MAGIC -> Cauer Ladder
Network synthesis workflow (Foster fit + Cauer-I/II + 3-way validation
against step response / Joule loss / Lorentz force). Distilled from a
21-script rectangular-CLN reference analysis suite.

---

## Installation

```bash
pip install ELF-mcp-server
```

The current PyPI distribution name is `ELF-mcp-server`. The installed console
scripts remain lowercase: `elf-mcp-server` and `elf-mcp-policy-lint`.

Verify:
```bash
elf-mcp-server --selftest
```

---

## Usage

### Claude Code

```bash
claude mcp add elf "C:/Program Files/Python312/Scripts/elf-mcp-server.exe"
```

(Adjust path for your Python install. On Linux/macOS, the script is typically `~/.local/bin/elf-mcp-server` or similar.)

### Cursor / Other MCP clients

Add to your MCP config:
```json
{
  "mcpServers": {
    "elf": {
      "command": "elf-mcp-server"
    }
  }
}
```

### Self-test

```bash
elf-mcp-server --selftest
```
Iterates through all curated topics and asserts non-empty documentation.

---

## What is ELF600?

ELF600 is a commercial BEM (Boundary Element Method) electromagnetic analysis suite distributed by Science Solutions International Laboratory ([https://www.science-solutions.jp/elf/](https://www.science-solutions.jp/elf/)).

| Module | Purpose |
|--------|---------|
| **MAGIC** | Magnetostatic field (static, transient, AC). Eddy current via MAB/MAT/MBB. |
| **ELFIN** | Electrostatic field analysis (D-E curves) |
| **BEAM** | Charged particle beam tracking |

Workflow:
```
.mei (mesh script) --> IEmesh --> .meg (compiled mesh)
.mai (analysis) + .meg --> MAGIC/ELFIN/BEAM --> .mag/.mao results
```

---

## Why this server?

LLM coding agents authoring ELF input files (`.mai`/`.mei`) need access to:
- The ~60k character ELF reference manual content,
- Element naming conventions (T/K/R symmetry × element family),
- SOL block recipes (MOME / MOMC / FIEL / FORC / NONL),
- Frequency-sweep AC analysis structure,
- Common error code interpretation,

without polluting context with the entire vendor PDF. This MCP server returns just the relevant topical chunk on demand.

---

## License

BSD-3-Clause. See [LICENSE](./LICENSE) and
[THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

ELF600 itself is a commercial product of Science Solutions International Laboratory and is not redistributed by this package.

---

## Author

Kengo Sugahara, Kindai University ([ksugahar@ele.kindai.ac.jp](mailto:ksugahar@ele.kindai.ac.jp))
