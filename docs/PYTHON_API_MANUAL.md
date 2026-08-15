# ELF/MAGIC Python Facade API Manual

- schema: `elf-python-api-manual/v1`
- topic: `all`

## Policy
- Product-side Python is reference material, not a required dependency.
- The vendor DLL boundary is immutable product territory.
- The public facade may add typed schemas, deck builders, validators, routers, and result contracts.
- The public MCP server may execute an installed MAGIC/ELFIN DLL through a fixed isolated Python ctypes workflow; it does not bundle DLLs or publish raw product-run outputs.

## Objects
- `MotorSpec`: Describe a motor before choosing a deck or run backend.
  fields: `motor_type`, `pole_pairs`, `stator_slots`, `rotor_topology`, `airgap_m`, `stack_length_m`, `materials`, `windings`, `studies`
  LLM rule: Fill this from the user's prompt first; do not start with a raw .mai edit.
- `DeckBundle`: Carry selected or generated .mai/.meg input data plus public quality labels.
  fields: `case_id`, `mai_text`, `meg_text`, `source_public_deck_paths`, `validation_label`, `requested_observables`
  LLM rule: Always pair .mai and .meg before proposing a local run.
- `RunRequest`: Contract sent to a user-local backend that can access the installed product.
  fields: `goal`, `run_mode`, `deck`, `requested_observables`, `timeout_seconds`, `keep_outputs`, `privacy_policy`
  LLM rule: Set requested_observables explicitly; they drive parsing and validation.
- `RunResult`: Normalized result returned by a local/private backend.
  fields: `case_id`, `status`, `generated_files`, `parsed_observables`, `warnings`, `validation_labels`
  LLM rule: Report status and warnings before interpreting physics.
- `WindingLayoutPlan`: Make slot/phase assignment, q, coil pitch, and winding-factor proxy explicit.
  fields: `stator_slots`, `pole_pairs`, `slots_per_pole_per_phase`, `coil_pitch_slots`, `winding_factors`, `slot_table`
  LLM rule: Do this before claiming phase back-EMF balance, cogging, or harmonic behavior.
- `TopologyParameterPlan`: Expose topology-specific geometry variables, ranges, constraints, and region labels.
  fields: `motor_type`, `rotor_topology`, `outer_diameter_mm`, `stack_length_mm`, `parameters`, `geometry_regions`
  LLM rule: Use topology parameters before mutating a deck or mesh.
- `DemagMarginPlan`: Record PM hot-Br assumptions, Hcj, negative Id, risk label, and required field observables.
  fields: `temperature_c`, `br_hot_t_proxy`, `hcj_ka_m`, `id_min_a_peak`, `risk_label`, `required_observables`
  LLM rule: Treat demag as a screening contract until local validated field results exist.
- `DriveCyclePlan`: Attach weighted operating points to efficiency, loss, thermal, NVH, and stress decisions.
  fields: `target_market`, `operating_points`, `weighted_outputs`, `quality_gates`
  LLM rule: Use this before ranking a design by one peak point.
- `OptimizationStudyPlan`: Define variables, constraints, ranking outputs, and validation promotion for candidates.
  fields: `objective`, `budget`, `design_variables`, `constraints`, `ranking_outputs`, `workflow`
  LLM rule: Never optimize without explicit constraints and validation readiness labels.
- `VoltageFieldWeakeningPlan`: Screen voltage margin, negative-Id demand, and field-weakening regions.
  fields: `dc_bus_v`, `current_limit_a_peak`, `dq_parameters`, `rows`, `required_observables`
  LLM rule: Use this before high-speed torque or efficiency claims.
- `CoggingRipplePlan`: Expose slot/pole cogging orders, ripple parser keys, and mitigation variables.
  fields: `stator_slots`, `poles`, `cogging_order_mechanical`, `harmonic_orders`, `mitigation_variables`, `parser_keys`
  LLM rule: Open-circuit cogging and loaded torque ripple must be separated.
- `AirgapHarmonicsNVHPlan`: Route slot/pole force orders and speed frequencies into NVH validation.
  fields: `mechanical_force_orders`, `speed_rows`, `required_observables`, `ngsolve_follow_up`
  LLM rule: Do not make NVH claims without modal/order validation.
- `ThermalNetworkPlan`: Convert loss terms into node temperatures before full thermal validation.
  fields: `total_loss_w`, `nodes`, `required_inputs`, `ngsolve_follow_up`
  LLM rule: Use reduced thermal networks as screening only.
- `ManufacturingTolerancePlan`: Define tolerance variables and robustness DOE rows for prototype handoff.
  fields: `airgap_mm`, `production_intent`, `tolerance_variables`, `doe_rows`, `required_observables`
  LLM rule: Freeze nominal design before tolerance DOE.
- `MaterialVariationPlan`: Plan magnet, steel, and conductor sensitivity studies.
  fields: `focus`, `variables`, `recommended_observables`, `study_rules`
  LLM rule: Material sensitivity is not material qualification.
- `FeasibilityStudy`: Bundle electromagnetic, thermal, NVH, stress, and manufacturing gates.
  fields: `goal`, `production_intent`, `lanes`, `extra_quality_gates`, `mcp_can_do`, `mcp_cannot_claim_alone`
  LLM rule: Use this before presenting a prototype-ready design story.
- `OperatingPointRunQueue`: Turn map axes into explicit local-run rows with observables and parser keys.
  fields: `run_rows`, `requested_observables`, `parser_keys`, `quality_gates`
  LLM rule: Use this before asking a backend to sweep many operating points.
- `InverterPWMHarmonicPlan`: Represent fundamental, low-order, and switching-sideband rows for loss and ripple screening.
  fields: `modulation`, `switching_frequency_hz`, `harmonic_rows`, `required_observables`, `validation_routes`
  LLM rule: Keep inverter/PWM assumptions separate from electromagnetic loss results.
- `SaturationInductanceMapPlan`: Track Ld/Lq and torque over current amplitude and current angle.
  fields: `current_axis_a_peak`, `angle_axis_deg_from_q_axis`, `map_rows`, `parser_keys`, `quality_gates`
  LLM rule: Do not use a single nominal Ld/Lq point for high-current MTPA or field weakening.
- `RotorStressRetentionPlan`: Screen high-speed rotor tip speed, hoop-stress proxy, and retention margin.
  fields: `max_speed_rpm`, `tip_speed_m_s`, `hoop_stress_mpa_proxy`, `retention_margin_proxy`, `ngsolve_follow_up`
  LLM rule: Do not approve high-speed operation from electromagnetic results alone.
- `RunResultParser`: Normalize local RunResult JSON or key-value text into parsed observables.
  fields: `case_id`, `status`, `parsed_observables`, `warnings`, `validation_labels`
  LLM rule: Never rank or validate raw text directly; normalize it first.
- `RunResultPathParser`: Scan user-local result files or directories and normalize observables without returning raw output text.
  fields: `source_label`, `files_scanned`, `parsed_results`, `combined_observables`, `warnings`
  LLM rule: Use for completed local runs; only file basenames and normalized values may leave the parser.
- `EfficiencyMapResult`: Convert parsed RunResults into numeric eta/loss/torque-error grids.
  fields: `map_axes`, `eta_grid`, `total_loss_w_grid`, `torque_error_nm_grid`, `best_efficiency_point`, `coverage`, `quality_gate_results`
  LLM rule: Missing cells stay missing; do not interpolate or claim a full map unless coverage says so.
- `OptimizationLoop`: Rank parsed candidates and propose next DOE rows or validation promotion.
  fields: `ranked_candidates`, `best_candidate`, `next_run_rows`, `promotion_rules`
  LLM rule: Only rank normalized observables; keep execution user-local.
- `NGSolveResultCrosscheck`: Compare parsed local observables with NGSolve runtime lane JSON.
  fields: `overall_status`, `run_result_status`, `lane_checks`, `next_actions`
  LLM rule: Use this before attaching validation labels to a handoff.
- `DrawingBOMHandoff`: Prepare drawing views, dimensions, BOM, and validation attachments.
  fields: `drawing_views`, `key_dimensions`, `bom`, `winding_summary`, `quality_gates`
  LLM rule: Call after validation status is known or label missing validation explicitly.
- `MotorValidationScorecard`: Combine parsed results, NGSolve lanes, loss separation, and handoff labels into a promotion decision.
  fields: `overall_status`, `score`, `gate_results`, `promotion_decision`, `next_actions`
  LLM rule: Use this as the final gate before claiming a candidate is ready for prototype handoff.

## LLM Call Order
1. `elf_python_api_manual("quickstart")`
   reason: Load API policy, object names, and the preferred call order.
2. `elf_motor_hybrid_router("<user motor goal>")`
   reason: Route intent across public decks, quick checks, AGE targets, and local backend handoff.
3. `elf_python_motor_market_brief(target_market="robot_drone", motor_type="<motor_type>")`
   reason: Normalize spec intake fields, topology choices, and GUI-free user experience policy.
4. `elf_python_api_schema("<motor_type>")`
   reason: Get the MotorSpec template and enum vocabulary.
5. `elf_python_motor_topology_parameter_plan(motor_type="<motor_type>", rotor_topology="<rotor_topology>")`
   reason: Choose topology-specific geometry variables, ranges, and region labels.
6. `elf_python_motor_winding_layout_plan(stator_slots=48, pole_pairs=4)`
   reason: Make q, coil pitch, phase-belt assignment, and winding-factor proxy explicit.
7. `elf_python_motor_design_plan("<user motor goal>")`
   reason: Choose design variables, objectives, studies, observables, and validation gates.
8. `elf_python_meg_generation_plan("<geometry goal>", dimension="2d|3d|auto")`
   reason: Choose Cubit, Netgen 2D, or constrained LLM 2D template path.
9. `elf_python_2d_motor_template("<motor_type>")`
   reason: Only for simple 2D drafting before deterministic remeshing.
10. `elf_python_deck_lint(mai_path="<public .mai>", requested_observables="flux_linkage,torque")`
   reason: Verify SOL/output markers before handing off to a local runner.
11. `elf_python_motor_sweep_matrix(motor_type="<motor_type>", objective="<objective>", budget=9)`
   reason: Create explicit DOE rows for local runs and ranking.
12. `elf_python_motor_dq_axis_map_plan(motor_type="<motor_type>")`
   reason: Create Id/Iq points and split PM torque from reluctance torque.
13. `elf_python_motor_mtpa_search_plan(motor_type="<motor_type>")`
   reason: Scan current angle for torque per amp before local RunResult confirmation.
14. `elf_python_reluctance_motor_design_plan(motor_type="synrm")`
   reason: Use for SynRM/SRM saliency, Ld/Lq extraction, and reluctance torque planning.
15. `elf_python_motor_demag_margin_plan(motor_type="<motor_type>", temperature_c=120)`
   reason: Screen PM hot-Br and negative-Id demagnetization risk before field-weakening claims.
16. `elf_python_motor_efficiency_map_plan(motor_type="<motor_type>")`
   reason: Create torque/speed operating points, feasibility labels, loss terms, and eta-grid outputs.
16a. `elf_python_motor_operating_point_run_queue(motor_type="<motor_type>")`
   reason: Turn map axes into concrete local-run rows with explicit observables and parser keys.
16b. `elf_python_motor_inverter_pwm_harmonic_plan(motor_type="<motor_type>", switching_frequency_hz=20000)`
   reason: Add inverter/PWM sideband rows for AC loss, magnet loss, ripple, and NVH screening.
16c. `elf_python_motor_saturation_inductance_map_plan(motor_type="<motor_type>")`
   reason: Track Ld/Lq and torque over current amplitude and current angle before high-current claims.
17. `elf_python_motor_loss_model_contract(motor_type="<motor_type>")`
   reason: Separate copper, iron, magnet, rotor, mechanical, and inverter loss assumptions.
18. `elf_python_motor_torque_speed_envelope(motor_type="<motor_type>")`
   reason: Clip map points by constant-torque and field-weakening limits.
19. `elf_python_motor_drive_cycle_plan(target_market="robot_drone")`
   reason: Convert duty points into weighted map, loss, thermal, NVH, and stress decisions.
20. `elf_python_motor_voltage_field_weakening_plan(motor_type="<motor_type>", dc_bus_v=48)`
   reason: Screen voltage margin, high-speed field weakening, and negative-Id demand.
21. `elf_python_motor_cogging_ripple_plan(stator_slots=48, pole_pairs=4)`
   reason: Separate cogging torque, loaded ripple, harmonic orders, and mitigation variables.
22. `elf_python_motor_airgap_harmonics_nvh_plan(stator_slots=48, pole_pairs=4)`
   reason: Route air-gap force orders into NGSolve NVH validation.
23. `elf_python_motor_thermal_network_plan(total_loss_w=25)`
   reason: Create reduced thermal screening before full NGSolve thermal validation.
24. `elf_python_motor_manufacturing_tolerance_plan(motor_type="<motor_type>", airgap_mm=0.8)`
   reason: Attach tolerance variables and robustness DOE rows.
25. `elf_python_motor_material_variation_plan(motor_type="<motor_type>", focus="all")`
   reason: Plan magnet, steel, and conductor sensitivity sweeps.
26. `elf_python_motor_optimization_study_plan(motor_type="<motor_type>", objective="cycle_efficiency", budget=48)`
   reason: Rank candidates with explicit variables, constraints, outputs, and validation promotion.
27. `elf_python_induction_slip_sweep_plan(pole_pairs=2, supply_frequency_hz=50)`
   reason: Use when the motor type is induction and slip must be explicit.
28. `elf_python_run_contract("<goal>", motor_type="<motor_type>", source_public_deck_path="<public .mai>")`
   reason: Prepare a backend-neutral RunRequest contract.
28a. `elf_product_detect()`
   reason: Discover the supported installed product DLL without loading it or accepting an arbitrary binary path.
28b. `elf_product_case_check(case_directory="<work-copy>", case_name="<case>", solver="MAGIC", workflow="mome_fiel")`
   reason: Validate the local .mai/.meg pair, fixed DLL mapping, workflow, and writable work directory before native execution.
28c. `elf_product_run(case_directory="<work-copy>", case_name="<case>", solver="MAGIC", workflow="mome_fiel", confirm_product_execution=True)`
   reason: Execute the allow-listed product API through the isolated Python ctypes worker after explicit confirmation.
29. `elf_python_motor_observable_contract(motor_type="<motor_type>", study="<study>")`
   reason: Tell the parser and LLM which output markers, keys, and validation checks apply.
30. `elf_python_run_result_parse(payload="<local RunResult JSON or key-value text>", requested_observables="torque,loss_proxy")`
   reason: Normalize local/private results into public-safe parsed observables.
30a. `elf_python_run_result_parse_path(run_path="<local run directory>", requested_observables="torque,loss_proxy")`
   reason: Normalize completed local result files while withholding raw paths and raw output text.
31. `elf_python_motor_optimization_loop(motor_type="<motor_type>", objective="cycle_efficiency", result_payloads_json="<JSON list>")`
   reason: Rank parsed candidates and choose next run rows or validation promotion.
31a. `elf_python_motor_efficiency_map_from_results(motor_type="<motor_type>", result_payloads_json="<JSON list or path-parse JSON>")`
   reason: Compute eta/loss grids and best efficiency point from parsed local RunResults.
32. `elf_python_motor_design_agent_handoff("<goal>", target_market="robot_drone")`
   reason: Bundle specs, design plan, routing, deliverables, required NGSolve NVH/thermal/stress, and prototype handoff.
33. `elf_python_motor_feasibility_study("<goal>", production_intent="prototype_small_lot")`
   reason: Review what MCP can and cannot claim before prototype or small-lot work.
34. `elf_python_ngsolve_validation_plan("<goal>", lanes="all")`
   reason: Build required NGSolve thermal/NVH/stress validation jobs from specs and parsed observables.
35. `elf_python_ngsolve_validation_script("<goal>", lane="all")`
   reason: Generate a runnable NGSolve Python validation script for open multiphysics checks.
36. `elf_python_motor_ngsolve_result_crosscheck(run_result_payload="<parsed/local result>", ngsolve_result_payload="<NGSolve JSON>")`
   reason: Attach PASS/WARN/FAIL labels from open multiphysics validation.
37. `elf_python_motor_drawing_bom_handoff(motor_type="<motor_type>", validation_label="<label>")`
   reason: Prepare drawing views, key dimensions, BOM, and validation attachments.
37a. `elf_python_motor_rotor_stress_retention_plan(motor_type="<motor_type>", max_speed_rpm=12000)`
   reason: Screen high-speed rotor stress and retention before prototype release.
37b. `elf_python_motor_validation_scorecard(run_result_payload="<result>", ngsolve_result_payload="<NGSolve JSON>")`
   reason: Combine result parsing, open validation lanes, loss separation, and handoff labels into one promotion decision.
38. `elf_sample_decks_validation_matrix(quantity="motor")`
   reason: Attach public validation labels and independent check expectations.

## Deck Lint Rules
- MAGIC motor decks should contain USE MAGIC, PRE, primary SOL MOME or MOMC, and DMEG.
- Flux linkage, back-EMF, and Ld/Lq requests should map to SOL FIXA plus FLUM.
- Field probes should map to SOL FIEL.
- Force or torque should map to FORC, FORT, FIXB, or a documented FLUM/co-energy route.
- AC or eddy-current loss proxies should map to OHM2, FREQ, or SOL MOMC markers.

## MEG Generation Rules
- Use Cubit mesh export for 3D, CAD-like, curved, or high-order geometry.
- Use Netgen 2D for deterministic motor cross-sections and polygonal regions.
- Use constrained LLM 2D templates only as drafts before deterministic remeshing.
- A .meg path is not publish-quality until geometry lint, .mai/.meg pairing, observable lint, and physics checks pass.

## Local Backend Rules
- The public server can discover, validate, and execute a supported installed product DLL through its fixed isolated Python ctypes worker.
- Call elf_product_detect, then elf_product_case_check on a work copy, then elf_product_run with confirm_product_execution=True.
- Arbitrary DLL paths, native symbols, shell commands, and Python code are not accepted by the product runner.
- Raw outputs and numeric product-run references remain local/private unless explicitly scrubbed.
- The default MCP response reports bounded status and fresh-file metadata; native diagnostics require an explicit local troubleshooting option.

## Validation Rules
- Choose the observable before editing deck parameters.
- Choose design variables and sweep rows before preparing run contracts.
- Run deck lint before local execution.
- Use MMM quick checks for first-order sign and scale.
- Use AGE or numeric invariant checks for independent validation routing.
- Do not claim absolute agreement from a proxy-energy label.

## Examples
### SPM back-EMF sweep
- `elf_motor_hybrid_router("SPM motor back EMF sweep")`
- `elf_python_motor_market_brief(target_market="robot_drone", motor_type="spm", rotor_topology="outer_rotor")`
- `elf_python_api_schema("spm")`
- `elf_python_motor_topology_parameter_plan(motor_type="spm", rotor_topology="outer_rotor")`
- `elf_python_motor_winding_layout_plan(stator_slots=48, pole_pairs=4)`
- `elf_python_motor_design_plan("SPM motor back EMF sweep", motor_type="spm", objective="back_emf_target")`
- `elf_python_meg_generation_plan("2D SPM motor cross-section", dimension="2d")`
- `elf_python_deck_lint(mai_path="application/motor/pm_cosine_pickup_72/pm001/pm001.mai", requested_observables="flux_linkage,back_emf_constant")`
- `elf_python_motor_sweep_matrix(motor_type="spm", objective="back_emf_target", budget=9)`
- `elf_python_motor_dq_axis_map_plan(motor_type="spm")`
- `elf_python_motor_mtpa_search_plan(motor_type="spm")`
- `elf_python_motor_demag_margin_plan(motor_type="spm", temperature_c=120)`
- `elf_python_motor_efficiency_map_plan(motor_type="spm", torque_points=5, speed_points=6)`
- `elf_python_motor_operating_point_run_queue(motor_type="spm", torque_points=5, speed_points=6)`
- `elf_python_motor_inverter_pwm_harmonic_plan(motor_type="spm", switching_frequency_hz=20000)`
- `elf_python_motor_saturation_inductance_map_plan(motor_type="spm")`
- `elf_python_motor_loss_model_contract(motor_type="spm")`
- `elf_python_motor_torque_speed_envelope(motor_type="spm")`
- `elf_python_motor_drive_cycle_plan(target_market="robot_drone")`
- `elf_python_motor_voltage_field_weakening_plan(motor_type="spm", dc_bus_v=48)`
- `elf_python_motor_cogging_ripple_plan(motor_type="spm", stator_slots=48, pole_pairs=4)`
- `elf_python_motor_airgap_harmonics_nvh_plan(motor_type="spm", stator_slots=48, pole_pairs=4)`
- `elf_python_motor_thermal_network_plan(total_loss_w=25)`
- `elf_python_motor_manufacturing_tolerance_plan(motor_type="spm", airgap_mm=0.8)`
- `elf_python_motor_material_variation_plan(motor_type="spm", focus="magnet")`
- `elf_python_motor_optimization_study_plan(motor_type="spm", objective="cycle_efficiency", budget=48)`
- `elf_python_run_contract("SPM motor back EMF sweep", motor_type="spm", source_public_deck_path="application/motor/pm_cosine_pickup_72/pm001/pm001.mai")`
- `elf_product_detect()`
- `elf_product_case_check(case_directory="<work-copy>", case_name="<case>", solver="MAGIC", workflow="mome_fiel")`
- `elf_product_run(case_directory="<work-copy>", case_name="<case>", solver="MAGIC", workflow="mome_fiel", confirm_product_execution=True)`
- `elf_python_run_result_parse(payload="torque_nm=0.82\nloss_w=12.5\nefficiency=0.91", case_id="cand_a")`
- `elf_python_run_result_parse_path(run_path="<local run directory>", requested_observables="torque,loss_proxy")`
- `elf_python_motor_efficiency_map_from_results(motor_type="spm", result_payloads_json="[...parsed local results...]")`
- `elf_python_motor_optimization_loop(motor_type="spm", objective="cycle_efficiency", result_payloads_json="[...local parsed results...]")`
- `elf_python_motor_observable_contract(motor_type="spm", study="back_emf_speed_sweep")`
- `elf_python_motor_design_agent_handoff("outer-rotor drone SPM motor", target_market="robot_drone", motor_type="spm", rotor_topology="outer_rotor")`
- `elf_python_motor_feasibility_study("outer-rotor drone SPM motor", production_intent="prototype_small_lot")`
- `elf_python_motor_ngsolve_result_crosscheck(run_result_payload="{...}", ngsolve_result_payload="{...}")`
- `elf_python_motor_drawing_bom_handoff(motor_type="spm", rotor_topology="outer_rotor", validation_label="crosscheck_pass")`
- `elf_python_motor_rotor_stress_retention_plan(motor_type="spm", max_speed_rpm=12000)`
- `elf_python_motor_validation_scorecard(run_result_payload="{...}", ngsolve_result_payload="{...}")`
### IPM torque-angle and Ld/Lq
- `elf_motor_hybrid_router("IPM torque angle and Ld Lq")`
- `elf_python_api_schema("ipm")`
- `elf_python_motor_topology_parameter_plan(motor_type="ipm", rotor_topology="inner_rotor")`
- `elf_python_motor_winding_layout_plan(stator_slots=48, pole_pairs=4)`
- `elf_python_motor_design_plan("IPM torque angle and Ld Lq", motor_type="ipm")`
- `elf_python_motor_dq_axis_map_plan(motor_type="ipm", id_points=5, iq_points=5)`
- `elf_python_motor_saturation_inductance_map_plan(motor_type="ipm", current_points=5, angle_points=7)`
- `elf_python_motor_mtpa_search_plan(motor_type="ipm")`
- `elf_python_motor_demag_margin_plan(motor_type="ipm", temperature_c=140)`
- `elf_python_motor_voltage_field_weakening_plan(motor_type="ipm", dc_bus_v=48)`
- `elf_python_motor_cogging_ripple_plan(motor_type="ipm", stator_slots=48, pole_pairs=4)`
- `elf_python_deck_lint(mai_path="application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai", requested_observables="flux_linkage,torque,ld_lq")`
- `elf_python_motor_sweep_matrix(motor_type="ipm", objective="torque_density", budget=9)`
- `elf_python_motor_optimization_study_plan(motor_type="ipm", objective="torque_density", budget=36)`
- `elf_python_motor_optimization_loop(motor_type="ipm", objective="torque_density", result_payloads_json="[...local parsed results...]")`
- `elf_python_run_contract("IPM torque angle and Ld Lq", motor_type="ipm")`
- `elf_python_motor_observable_contract(motor_type="ipm", study="dq_inductance")`
### SynRM reluctance torque and dq axes
- `elf_motor_hybrid_router("SynRM reluctance torque Ld Lq MTPA")`
- `elf_python_motor_topology_parameter_plan(motor_type="synrm", rotor_topology="flux_barrier")`
- `elf_python_motor_winding_layout_plan(stator_slots=36, pole_pairs=2)`
- `elf_python_reluctance_motor_design_plan(motor_type="synrm", pole_pairs=2, stator_slots=36)`
- `elf_python_motor_dq_axis_map_plan(motor_type="synrm")`
- `elf_python_motor_mtpa_search_plan(motor_type="synrm", angle_min_deg=0, angle_max_deg=90)`
- `elf_python_motor_cogging_ripple_plan(motor_type="synrm", stator_slots=36, pole_pairs=2)`
- `elf_python_motor_airgap_harmonics_nvh_plan(motor_type="synrm", stator_slots=36, pole_pairs=2)`
- `elf_python_motor_observable_contract(motor_type="synrm", study="dq_inductance")`
### Induction motor slip and efficiency map
- `elf_motor_hybrid_router("induction motor slip loss efficiency map")`
- `elf_python_motor_topology_parameter_plan(motor_type="induction", rotor_topology="squirrel_cage")`
- `elf_python_motor_winding_layout_plan(stator_slots=36, pole_pairs=2)`
- `elf_python_motor_design_plan("IM slip loss efficiency map", motor_type="induction", objective="efficiency_map")`
- `elf_python_induction_slip_sweep_plan(pole_pairs=2, supply_frequency_hz=50, slip_min=0.005, slip_max=0.20)`
- `elf_python_motor_loss_model_contract(motor_type="induction")`
- `elf_python_motor_efficiency_map_plan(motor_type="induction")`
- `elf_python_motor_operating_point_run_queue(motor_type="induction")`
- `elf_python_motor_drive_cycle_plan(target_market="industrial_servo")`
- `elf_python_motor_thermal_network_plan(target_market="industrial_servo", total_loss_w=120)`
- `elf_python_motor_manufacturing_tolerance_plan(motor_type="induction", airgap_mm=0.6)`
- `elf_python_motor_observable_contract(motor_type="induction", study="induction_slip_loss")`
### Advanced motor model coverage
- `elf_python_motor_design_plan("PM-assisted SynRM efficiency map", motor_type="pm_assisted_synrm")`
- `elf_python_motor_design_plan("six-step BLDC torque ripple", motor_type="bldc")`
- `elf_python_motor_design_plan("line-start PM pull-in torque", motor_type="line_start_pm")`
- `elf_python_motor_design_plan("deep-bar induction starting torque", motor_type="deep_bar_induction")`
- `elf_python_motor_design_plan("flux-switching PM torque ripple", motor_type="flux_switching_pm")`
- `elf_python_motor_design_plan("Vernier PM low-speed high-torque map", motor_type="vernier_pm")`
- `elf_python_motor_design_plan("transverse-flux PM 3D module", motor_type="transverse_flux_pm")`
- `elf_python_motor_design_plan("slotless coreless PM low-cogging motor", motor_type="slotless_pm")`
- `elf_python_motor_design_plan("claw-pole Lundell field-current sweep", motor_type="claw_pole")`
- `elf_python_motor_design_plan("commutator universal motor torque and loss", motor_type="commutator_dc")`
- `elf_python_motor_topology_parameter_plan(motor_type="<advanced_motor_type>")`
- `elf_python_2d_motor_template("<advanced_motor_type>")`
- `elf_python_motor_optimization_study_plan(motor_type="<advanced_motor_type>", objective="torque_density")`
### 3D WPT or shielded application mesh
- `elf_python_meg_generation_plan("3D WPT shielded coils", dimension="3d")`
- `elf_local_simulation_handoff("WPT shielded coupling")`
- `elf_sample_decks_validation_matrix(quantity="wpt")`
