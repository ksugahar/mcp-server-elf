# Public ELF/MAGIC Sample Decks

This directory contains lab-authored ELF-runnable ELF/MAGIC input decks.
Only validation-passed input-deck pairs are published here; candidate,
failed, or unverified cases stay outside this directory until they pass the
public sample validation gate and are listed in `VALIDATED_MANIFEST.json`.
All published cases have an independent NGSolve proxy-field gate; the numeric
anchor families additionally carry ELF `FLUM`-derived and NGSolve invariant
checks.
The machine-readable contract is `VALIDATED_MANIFEST.json`; MCP clients can
summarize it through `elf_sample_decks_validation()`.
`PUBLICATION_BATCHES.json` records deterministic 100-case publication
checkpoints for the validated baseline.

Included files are input decks only:

- `.mai` analysis-control files
- `.meg` mesh files

Excluded files:

- solver outputs such as `.mag`, `.mao`, `.mat`, `.mac`
- comparison tables, benchmark metrics, or regression summaries
- machine-local paths or private provenance

Validation levels:

- `ngsolve_proxy_energy`: broad independent proxy-field energy sanity gate for
  the published deck family; this is not a full absolute field/force/torque/loss
  agreement suite.
- `ngsolve_numeric_invariant`: stronger compact-anchor gate with ELF `FLUM`
  ratio/sign/law invariants, `FLUM`-derived inductance/co-energy invariants,
  `FLUM`-derived force/torque-gradient invariants, AC-loss proxy invariants,
  magnetic-circuit proxy invariants, permanent-magnet proxy invariants, and
  transformer-coupling proxy invariants, and independent NGSolve proxy
  invariants.

Publication cadence:

- validated decks are reviewed in 100-case checkpoints
- this baseline contains 16 full checkpoints and no release-remainder batch
- no additional cases are required for this baseline; a future optional
  100-case checkpoint would be 1700 cases

The decks are intended as public examples that users can inspect, copy, and run
with their own ELF/MAGIC installation. `elf_product_run` can execute a work copy
through the installed DLL; the MCP package does not bundle DLLs or solver
results.

Quality labels used by the MCP tools:

- `gold_numeric_invariant`: 674 numeric-anchor cases where ELF `FLUM`-derived
  scaling/sign/energy/loss/coupling invariants and independent NGSolve proxy
  invariants both passed.
- `silver_observable_contract`: 500 runnable authoring-pattern cases where
  ELF/MAGIC run checks and independent NGSolve proxy-field energy checks
  passed, and the public `.mai` decks expose the expected FLUM/OHM2/FREQ/HBRM/
  HBCU markers for their mapped physical quantities.
- `silver_proxy_energy`: 426 broader runnable authoring-pattern cases where
  ELF/MAGIC run checks passed and an independent NGSolve proxy-field energy
  sanity gate was positive. This is useful for authoring patterns, but is not
  a claim of full absolute field/force/torque/loss agreement.

Representative routing:

- `elf_sample_decks_representatives()` returns a curated first-stop tour across
  motors, non-motor applications, and numeric validation anchors.
- `elf_sample_decks_route(goal)` uses these representative decks where possible
  before falling back to the first cases in a matching family.
- `elf_sample_decks_quality(label="gold")` is the recommended way to find the
  strongest public numeric-invariant families before making validation claims.
  It also reports publication gates for `.mai/.meg` pairing, manifest and
  100-case checkpoint coverage, public-boundary hygiene, solver-output
  exclusion, `application/motor` hierarchy, and representative-path resolution.
- `elf_sample_decks_physics(quantity="force")` maps decks to physical
  quantities before an agent chooses examples. The public map covers FLUM-based
  flux linkage, inductance/co-energy, force/torque-gradient, AC-loss,
  magnetic-circuit, permanent-magnet, transformer-coupling, WPT, MRI,
  actuator, and accelerator quantities without bundling solver outputs.
- `elf_sample_decks_validation_matrix(quantity="transformer")` joins physical
  quantity, public observable, quality label, validation methods,
  representative `.mai` decks, and next MCP calls so agents can answer prompts
  without guessing which quantity to evaluate.
- `elf_sample_decks_observable_contracts()` audits the 500-case public
  observable-contract upgrade and reports required deck markers for each
  enhanced family.
- `elf_sample_decks_cross_validation()` audits the validation contract across
  all 1600 cases. It requires every family to have an independent NGSolve
  cross-check, reports that no family is missing one, and separates stronger
  `gold_numeric_invariant` families from enhanced `silver_observable_contract`
  and broader `silver_proxy_energy` proxy-check families.
- `elf_sample_decks_duplicates()` audits apparent duplicates before deletion:
  exact `.mai` + `.meg` pair duplicates are deletion candidates, while `.mai`
  or `.meg` reuse is treated as intentional design-space coverage that MCP
  clients should collapse or summarize in concise views.
- `elf_local_simulation_handoff(goal)` converts a natural-language simulation
  goal into a public-safe local-runner contract: deck family, physical
  quantities, runner inputs, parser outputs, and motor design-loop steps. Use
  `elf_product_detect`, `elf_product_case_check`, and `elf_product_run` for the
  guarded local Python/ctypes execution sequence; solver outputs are not bundled.
- `elf_mcp_readiness()` aggregates the public quality gates, cross-validation
  gates, duplicate audit, local-runner handoff boundary, and high-value route
  checks into a release-readiness report before tag push.
- `elf_motor_readiness()` audits the motor subset specifically: 652 cases
  across 37 public motor families, current quality-label coverage, validation
  depth gaps, and radia-motor/radia-ngsolve strengthening targets such as
  back-EMF, cogging torque, Ld/Lq, MTPA, slip loss, and reluctance torque.
- `elf_motor_hybrid_router(goal)` dispatches motor prompts across public ELF
  deck routes, radia-motor 2D MMM/BEM-like quick checks, NGSolve AGE validation
  targets, and the user-local ELF/MAGIC product-run handoff.
- `elf_motor_mmm_quick_check()` runs the public-safe 2D magnetic-circuit /
  MMM-like first-order check directly in the MCP server. It estimates PM flux
  linkage, back-EMF constant, dq torque proxy, and induction slip-loss proxy
  without calling ELF/MAGIC or bundling solver outputs.

For these compact public examples, `.meg` files are generated as small ASCII
ELF/MAGIC mesh decks directly by lab-authored Python generators. They are not
generated through Cubit. The normal ELF authoring route remains `.mei` through
IEmesh/mesh750.exe. Cubit also remains useful for larger CAD/mesh workflows:
`cubit_mesh_export.export_meg(...)` and `cubit_mesh_export.export_3D_meg(...)`
can emit ELF-compatible `.meg` meshes when that route is appropriate.

Current families:

- `application/motor/`: 652 motor-oriented examples, including 332 permanent-magnet
  pickup decks, 10 explicit SPM decks, 10 SRM switched-reluctance decks,
  10 induction cage decks, and 40 loop-reviewed SR/SPM/reluctance/hysteresis
  motor decks, plus 200 EMDLAB-style motor decks covering all bundled EMDLAB
  v0.2.0 motor example scripts, plus 50 Loop13 IPM, wound-field synchronous,
  axial-flux PM, linear PM, and stepper motor decks
- `application/motor/emdlab_bldc_spm_10/`: 10 EMDLAB-style BLDC/SPM examples using
  slotted stator iron, surface PM rotor proxies, phase coils, and `FLUM`
- `application/motor/emdlab_ipm_hairpin_10/`: 10 EMDLAB-style IPM hairpin examples with
  buried PM rotor proxies, hairpin-conductor proxy counts, and `FLUM`
- `application/motor/emdlab_induction_bar_10/`: 10 EMDLAB-style induction-machine rotor-bar
  examples using phase coils, conductive bar proxies, `OHM2`, and `FLUM`
- `application/motor/emdlab_synrm_flux_barrier_10/`: 10 EMDLAB-style SynRM flux-barrier
  examples with saliency, rotor-angle proxies, and `FLUM`
- `application/motor/emdlab_srm_pole_variants_10/`: 10 EMDLAB-style SRM pole-variant
  examples covering 6/4, 8/6, 12/8, and 12/16 pole proxy patterns
- `application/motor/emdlab_afpm_linearized_10/`: 10 EMDLAB-style AFPM linearized-airgap
  examples with unfolded pole pitch, face magnets, stator coils, and `FLUM`
- `application/motor/emdlab_bldc_outer_rotor_10/`: 10 EMDLAB-style BLDC outer-rotor
  examples with surface PM proxies, stator iron, phase coils, and `FLUM`
- `application/motor/emdlab_induction_fraction_10/`: 10 EMDLAB-style fractional-sector
  induction-machine examples with phase coils, conducting bars, and `OHM2`
- `application/motor/emdlab_ipm_hairpin_fraction_10/`: 10 EMDLAB-style fractional-sector
  IPM hairpin examples with buried PMs, hairpin proxies, and `FLUM`
- `application/motor/emdlab_spmsm_10/`, `application/motor/emdlab_spmsm_fraction_10/`, and
  `application/motor/emdlab_spmsm_static_torque_10/`: 30 EMDLAB-style SPMSM examples
  covering full, fractional-sector, and static-torque variants
- `application/motor/emdlab_srm64_10/`, `application/motor/emdlab_srm86_10/`,
  `application/motor/emdlab_srm86_fraction_10/`, `application/motor/emdlab_srm86_static_torque_10/`,
  `application/motor/emdlab_srm128_10/`, and `application/motor/emdlab_srm1216_outer_rotor_10/`: 60
  EMDLAB-style SRM examples covering 6/4, 8/6, 12/8, and 12/16 proxy patterns
- `application/motor/emdlab_synrm_static_torque_10/` and
  `application/motor/emdlab_synrm_fraction_static_torque_10/`: 20 EMDLAB-style SynRM
  static-torque examples with flux-barrier and fractional-sector proxies
- `application/motor/ipm_interior_pm_10/`: 10 Loop13 IPM examples with buried PM pairs,
  rotor/stator iron, phase coils, rotor-angle parameters, and `FLUM`
- `application/motor/wound_field_sync_10/`: 10 Loop13 wound-field synchronous motor
  examples with DC rotor field coils, stator phase coils, soft iron, and `FLUM`
- `application/motor/axial_flux_pm_10/`: 10 Loop13 axial-flux PM motor examples with dual
  axial yokes, face magnets, skew offsets, stator coils, and `FLUM`
- `application/motor/linear_pm_motor_10/`: 10 Loop13 linear PM motor examples with
  alternating PM tracks, moving three-coil forcers, translator offsets, and
  `FLUM`
- `application/motor/stepper_motor_10/`: 10 Loop13 stepper motor examples with four stator
  phases, PM rotor proxies, detent offsets, and `FLUM`
- `application/motor/spm_surface_pm_10/`: 10 surface permanent-magnet motor examples
  using `MWL8T` magnets, `MMB8T` iron, three-phase `MCL8T` coils, and `FLUM`
- `application/motor/spm_loop_10/`: 10 loop-reviewed surface-PM motor examples using
  `MWL8T` magnets, stator coils, rotor/stator iron, and `FLUM`
- `application/motor/induction_cage_10/`: 10 induction motor cage examples using
  three-phase coils, `MAB8T` conducting bars, `OHM2`, and transient `FLUM`
- `application/motor/srm_switched_reluctance_10/`: 10 switched-reluctance motor examples
  using salient `MMB8T` stator/rotor iron, phase `MCL8T` coils, and `FLUM`
- `application/motor/sr_motor_loop_10/`: 10 loop-reviewed SR-motor examples with salient
  stator/rotor iron, phase coils, rotor-angle sweeps, and `FLUM`
- `application/motor/reluctance_motor_10/`: 10 synchronous-reluctance motor examples with
  saliency, phase excitation, and passive pickup coils
- `application/motor/hysteresis_motor_10/`: 10 high-coercivity hysteresis-motor input-deck
  proxy examples using origin-starting B-H curves and pickup coils
- non-motor `application/` families: 948 examples covering transformers, MRI,
  wireless power transfer, induction heating, accelerator electromagnets,
  actuator plungers, maglev bearings, magnetic separators, eddy-current
  brakes, NDT eddy-current probes, magnetic gears, voice-coil actuators,
  relay solenoids, Hall-sensor fixtures, electromagnetic clutches, WPT
  misalignment, MRI gradient sequences, transformer leakage, IH susceptors,
  accelerator corrector magnets, EMDLAB-style transformer/benchmark decks,
  numeric-validation anchors, numeric FLUM-law validation decks, numeric
  inductance/co-energy validation decks, and numeric force/torque-gradient
  validation decks, numeric AC-loss validation decks, and numeric
  magnetic-circuit validation decks, numeric permanent-magnet validation decks,
  and numeric transformer-coupling validation decks
- `application/emdlab_1ph_transformer_static_10/`: 10 EMDLAB-style
  single-phase transformer static examples with core limbs, primary/secondary
  coils, and `FLUM`
- `application/emdlab_benchmark_ccore_10/`,
  `application/emdlab_benchmark_geometry_10/`, and
  `application/emdlab_benchmark_magnet_10/`: 30 EMDLAB-style benchmark
  examples covering C-core, geometry, and magnet patterns
- `application/numeric_validation_anchors_10/`: 10 compact numeric anchor
  examples for current scaling, sign reversal, distance decay, symmetry, and
  cancellation checks using ELF `FLUM` and NGSolve proxy invariants
- `application/numeric_flum_law_64/`: 64 numeric FLUM-law examples validating
  magnetic flux linkage against current, turns, sign, distance, symmetry,
  superposition, and cancellation invariants
- `application/numeric_inductance_energy_100/`: 100 numeric examples validating
  `FLUM`-derived inductance `L = Phi/I` and co-energy
  `W = 1/2 sum(I Phi)` against current, turns, distance, symmetry,
  superposition, and add/cancel energy invariants
- `application/numeric_force_torque_100/`: 100 numeric examples validating
  `FLUM`-derived co-energy force/torque-gradient behavior against
  distance-force sign, current-square scaling, mirror/lateral symmetry,
  angular `dW/dtheta`, and balanced-torque invariants
- `application/numeric_ac_loss_100/`: 100 numeric MOMC/FREQ/OHM2 examples
  validating AC-loss proxy behavior against frequency-square, current-square,
  resistivity-inverse, distance-decay, mirror/lateral symmetry, add/cancel,
  thickness, width, and combined `I-f-rho` scaling invariants
- `application/numeric_magnetic_circuit_100/`: 100 numeric MMB8T/HBUN/HBCU
  examples validating magnetic-circuit proxy behavior against B-H slope,
  air-gap reluctance, core area/depth, current/turn scaling, mirror/height
  sanity, return-yoke continuity, and add/cancel bias invariants
- `application/numeric_permanent_magnet_100/`: 100 numeric MWL8T/HBRM/HBCN/VEC3
  examples validating permanent-magnet pickup behavior against remanence
  scaling, distance decay, magnet width/depth, magnetization-angle cosine,
  polarity reversal, lateral symmetry, add/cancel, array count, and
  pickup-turn scaling invariants
- `application/numeric_transformer_coupling_100/`: 100 numeric MMB8T/HBUN/HBCU
  transformer-coupling examples validating primary/secondary `FLUM`, apparent
  turns ratio, B-H slope, air-gap leakage, winding span, core area/depth,
  secondary-offset symmetry, and buck/boost superposition invariants
- `application/transformer_core_pickup_12/`: 12 transformer core, primary,
  secondary, and passive pickup-coil examples
- `application/transformer_loop_10/`: 10 loop-reviewed transformer core,
  primary, secondary, and passive pickup-coil examples
- `application/mri_gradient_shield_12/`: 12 MRI gradient-coil and
  eddy-current shield examples using linear AC `SOL MOMC`
- `application/mri_loop_10/`: 10 loop-reviewed MRI gradient-coil and
  conducting-shield examples with `OHM2`, `FREQ`, and `FLUM`
- `application/wpt_coupled_coils_10/`: 10 wireless-power-transfer coupled
  coil examples using `SOL MOMC`, primary/secondary `MCL8T` coils, optional
  conducting shields, and `FLUM`
- `application/wpt_loop_10/`: 10 loop-reviewed wireless-power-transfer
  coupled-coil examples with primary/secondary coils, optional shields, and
  `FLUM`
- `application/ih_induction_heating_10/`: 10 induction-heating examples with
  `MCL8T` coils, `MAB8T` conducting workpieces, `OHM2`, and `SOL MOMC`
- `application/accelerator_magnet_10/`: 10 accelerator electromagnet examples
  with yokes, excitation coils, aperture pickups, and `FLUM`
- `application/actuator_plunger_10/`: 10 actuator plunger examples with
  U-yokes, movable plungers, dual coils, air-gap pickups, and `FLUM`
- `application/maglev_bearing_10/`: 10 maglev/magnetic-bearing examples with
  opposed pole pairs, differential coils, mover offsets, and `FLUM`
- `application/magnetic_separator_10/`: 10 magnetic separator examples with
  PM pole pairs, steel back-yokes, conductive belt proxies, and `FLUM`
- `application/eddy_current_brake_10/`: 10 eddy-current brake examples with
  conducting plates, `OHM2`, AC `SOL MOMC`, and pickup coils
- `application/ndt_eddy_probe_10/`: 10 NDT eddy-current probe examples with
  conductive plates, local flaw-property patches, `OHM2`, and `FLUM`
- `application/magnetic_gear_10/`: 10 magnetic gear examples with alternating
  PM teeth, soft yokes, relative tooth offsets, `HBCN`, and `FLUM`
- `application/voice_coil_10/`: 10 voice-coil actuator examples with PM bias
  fields, moving differential coils, return iron, and `FLUM`
- `application/relay_solenoid_10/`: 10 relay/solenoid examples with U-cores,
  armature gaps, twin coil legs, and `FLUM`
- `application/hall_sensor_fixture_10/`: 10 Hall-sensor fixture examples with
  opposed PM blocks, flux concentrator yokes, probe coils, and `FLUM`
- `application/electromagnetic_clutch_10/`: 10 electromagnetic clutch examples
  with AC coils, steel plates, conducting armatures, `OHM2`, and `FLUM`
- `application/wpt_misalignment_10/`: 10 Loop13 wireless-power-transfer
  misalignment examples with primary/secondary pad offsets, conducting shields,
  `OHM2`, `SOL MOMC`, and `FLUM`
- `application/mri_gradient_sequence_10/`: 10 Loop13 MRI gradient-sequence
  examples with bipolar coils, split eddy-current shields, `OHM2`, `FREQ`, and
  `FLUM`
- `application/transformer_leakage_10/`: 10 Loop13 transformer leakage examples
  with gapped cores, primary/secondary coils, leakage pickup coils, and `FLUM`
- `application/ih_susceptor_ring_10/`: 10 Loop13 induction-heating susceptor
  examples with nested conducting workpieces, `OHM2` contrast, AC coils, and
  `FLUM`
- `application/accelerator_corrector_10/`: 10 Loop13 accelerator corrector
  magnet examples with main dipole coils, trim-correction coils, aperture
  pickup, and `FLUM`
