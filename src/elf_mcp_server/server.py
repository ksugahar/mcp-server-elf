"""
ELF MCP Server

Provides documentation and knowledge for the ELF600 electromagnetic field
analysis suite (MAGIC / ELFIN / BEAM solvers) — file formats, commands,
element types, solver options, and mesh scripting.

Topics:
- .mai file format (analysis/solver control input)
- .mei file format (mesh generation script)
- .meg file format (compiled mesh data)
- MAGIC solver (magnetostatic BEM)
- ELFIN solver (eddy current BEM)
- BEAM solver (charged particle tracking)
- Element type naming convention
- B-H curve specification
- IPM motor analysis
- Inductance computation (LscLl)
- Magnetization / demagnetization

Usage:
    elf-mcp-server              # Start MCP server (stdio transport)
    elf-mcp-server --selftest   # Run self-test
"""

import json
import re
import sys

from mcp.server.fastmcp import FastMCP

from .learning_quality import build_balanced_learning_profile

from .elf_knowledge import get_elf_documentation
from .help_access import list_help_files, search_help, get_help_file
from .examples_access import list_examples, search_examples, get_example
from .example_playbook import build_example_cards, format_example_cards
from .sample_decks import (
    list_sample_decks,
    search_sample_decks,
    get_sample_deck,
    route_sample_decks,
    build_sample_deck_cards,
    build_representative_cards,
    build_team28_cards,
    build_cross_validation_summary,
    build_duplicate_audit,
    build_local_simulation_handoff,
    build_mcp_readiness,
    build_motor_hybrid_router,
    build_motor_mmm_quick_check,
    build_motor_readiness,
    build_quality_summary,
    build_observable_contract_summary,
    build_physical_quantity_summary,
    build_validation_matrix,
    build_validation_summary,
    format_public_promotion,
    format_sample_deck_cards,
    format_cross_validation_summary,
    format_duplicate_audit,
    format_local_simulation_handoff,
    format_mcp_readiness,
    format_motor_hybrid_router,
    format_motor_mmm_quick_check,
    format_motor_readiness,
    format_observable_contract_summary,
    format_validation_matrix,
    format_representative_cards,
    format_sample_deck_routes,
    format_team28_cards,
    format_quality_summary,
    format_physical_quantity_summary,
    format_validation_summary,
)
from .python_interface_design import (
    build_python_interface_design,
    format_python_interface_design,
)
from .python_api_manual import build_python_api_manual, format_python_api_manual
from .python_facade import (
    build_2d_motor_template,
    build_meg_generation_plan,
    build_induction_motor_slip_sweep_plan,
    build_motor_design_agent_handoff,
    build_motor_design_plan,
    build_motor_demag_margin_plan,
    build_motor_drive_cycle_plan,
    build_motor_dq_axis_map_plan,
    build_motor_efficiency_map_plan,
    build_motor_efficiency_map_from_results,
    build_motor_airgap_harmonics_nvh_plan,
    build_motor_cogging_ripple_plan,
    build_motor_feasibility_study,
    build_motor_loss_model_contract,
    build_motor_manufacturing_tolerance_plan,
    build_motor_market_brief,
    build_motor_material_variation_plan,
    build_motor_mtpa_search_plan,
    build_motor_ngsolve_result_crosscheck,
    build_motor_observable_contract,
    build_motor_operating_point_run_queue,
    build_motor_optimization_study_plan,
    build_motor_optimization_loop,
    build_motor_inverter_pwm_harmonic_plan,
    build_motor_saturation_inductance_map_plan,
    build_motor_rotor_stress_retention_plan,
    build_motor_spec_template,
    build_motor_sweep_matrix,
    build_motor_topology_parameter_plan,
    build_motor_torque_speed_envelope,
    build_motor_thermal_network_plan,
    build_motor_validation_scorecard,
    build_motor_voltage_field_weakening_plan,
    build_motor_winding_layout_plan,
    build_motor_drawing_bom_handoff,
    build_reluctance_motor_design_plan,
    build_run_request_contract,
    parse_run_result_payload,
    parse_run_result_path,
    format_deck_lint,
    format_pm_demag_step_lint,
    format_2d_motor_template,
    format_induction_motor_slip_sweep_plan,
    format_meg_generation_plan,
    format_motor_drawing_bom_handoff,
    format_motor_design_agent_handoff,
    format_motor_demag_margin_plan,
    format_motor_design_plan,
    format_motor_drive_cycle_plan,
    format_motor_dq_axis_map_plan,
    format_motor_efficiency_map_plan,
    format_motor_efficiency_map_result,
    format_motor_airgap_harmonics_nvh_plan,
    format_motor_cogging_ripple_plan,
    format_motor_feasibility_study,
    format_motor_loss_model_contract,
    format_motor_manufacturing_tolerance_plan,
    format_motor_market_brief,
    format_motor_material_variation_plan,
    format_motor_mtpa_search_plan,
    format_motor_ngsolve_result_crosscheck,
    format_motor_observable_contract,
    format_motor_operating_point_run_queue,
    format_motor_optimization_study_plan,
    format_motor_optimization_loop,
    format_motor_inverter_pwm_harmonic_plan,
    format_motor_saturation_inductance_map_plan,
    format_motor_rotor_stress_retention_plan,
    format_motor_topology_parameter_plan,
    format_motor_winding_layout_plan,
    format_reluctance_motor_design_plan,
    format_motor_spec_lint,
    format_motor_sweep_matrix,
    format_motor_torque_speed_envelope,
    format_motor_thermal_network_plan,
    format_motor_validation_scorecard,
    format_motor_voltage_field_weakening_plan,
    format_python_api_schema,
    format_run_request_contract,
    format_run_result_parse,
    format_run_result_path_parse,
    lint_mai_text,
    lint_pm_demag_step_contract,
    python_api_schema,
    validate_motor_spec_dict,
)
from .ngsolve_multiphysics import (
    build_ngsolve_validation_plan,
    build_ngsolve_validation_script,
    build_ngsolve_validation_spec,
    format_ngsolve_validation_plan,
    format_ngsolve_validation_script,
)
from .recipes import (
    list_recipes,
    search_recipes,
    get_recipe,
    format_recipe_index,
    format_search_results,
    format_recipe,
    plan_workflow,
)
from .wiki_access import list_wiki_pages, search_wiki, get_wiki_page
from .python_access import list_python_files, search_python, get_python_file

mcp = FastMCP("elf-mcp-server")


# ============================================================
# Meta / overview (★ recommended first call)
# Pattern adopted 2026-05-25 from radia-mcp.meta (Sugahara lab
# discovery infrastructure). The tool surface is large enough that a cold-start
# LLM benefits from an overview before browsing tool-by-tool.
# ============================================================

_TOOL_CATALOG = [
    ("elf_usage(topic)", "Curated documentation across 32 topics: "
                          ".mai/.mei/.meg formats, MAGIC/ELFIN/BEAM "
                          "solvers, element conventions, B-H, IPM motor, "
                          "radia motor bridge, SOL MOMC AC, cln_extraction, "
                          "licensing (dongle)"),
    ("elf_help_index / search / get", "Raw access to C:/ELF600/help/ "
                                       "(1141 files, 1.18 MB)"),
    ("elf_examples_index / search / get / playbook", "C:/ELF600/examples/ "
                                                       "(332 .mai/.mei/.txt, 533 KB) "
                                                       "plus 100 compact example cards"),
    ("elf_sample_decks_index / search / route / handoff / validation / readiness / "
     "validation_matrix / observable_contracts / cross_validation / duplicates / "
     "quality / physics / representatives / get / playbook",
                                              "Lab-authored ELF-runnable "
                                              "public .mai/.meg input decks "
                                              "(input files only; no solver outputs; "
                                              "machine-readable validation levels)"),
    ("elf_public_promotion", "Public-safe Japanese/English promotion copy "
                              "for the 1600-case corpus"),
    ("elf_python_interface_design(topic)", "Public-safe design contract for "
                                           "a richer Python facade above a "
                                           "user-local ELF/MAGIC product "
                                           "backend; product Python is "
                                           "reference-only, vendor DLL is an "
                                           "immutable boundary"),
    ("elf_python_api_manual(topic)", "LLM-oriented Python facade manual: "
                                    "policy, object vocabulary, call order, "
                                    "deck lint, MEG generation, backend "
                                    "contract, validation, and examples"),
    ("elf_python_api_schema / motor_spec_lint / deck_lint / pm_demag_step_lint / run_contract / "
     "meg_generation_plan / 2d_motor_template",
                            "Typed public Python facade: MotorSpec schema, "
                            "deck lint, PM demag step lint, local backend contract, MEG "
                            "generation routing across Cubit, Netgen 2D, "
                            "and constrained LLM 2D motor templates"),
    ("elf_python_motor_design_plan / motor_sweep_matrix / motor_observable_contract",
                            "Motor-design API layer: design variables, "
                            "objectives, sweep/DOE rows, ELF observable "
                            "markers, parser keys, and validation targets"),
    ("elf_python_motor_efficiency_map_plan / motor_efficiency_map_from_results / "
     "loss_model_contract / "
     "torque_speed_envelope / induction_slip_sweep_plan",
                            "Motor-design API layer for efficiency maps, "
                            "numeric eta grids from parsed RunResults, "
                            "loss-term accounting, torque-speed envelopes, "
                            "and IM slip sweeps"),
    ("elf_python_motor_operating_point_run_queue / "
     "motor_inverter_pwm_harmonic_plan / "
     "motor_saturation_inductance_map_plan",
                            "Motor execution-planning API layer for concrete "
                            "operating-point run rows, inverter/PWM harmonic "
                            "loss and ripple screening, and saturated Ld/Lq "
                            "current maps"),
    ("elf_python_motor_dq_axis_map_plan / mtpa_search_plan / "
     "reluctance_design_plan",
                            "Motor-design API layer for Id/Iq maps, "
                            "PM-vs-reluctance torque decomposition, MTPA "
                            "searches, SynRM/PMa-SynRM saliency, and SRM "
                            "aligned/unaligned inductance planning"),
    ("elf_python_motor_winding_layout_plan / topology_parameter_plan / "
     "demag_margin_plan / drive_cycle_plan / optimization_study_plan",
                            "Motor-design API layer for phase-belt winding "
                            "layout, topology-specific geometry variables, "
                            "PM demagnetization margin screening, weighted "
                            "drive-cycle points, and constrained candidate "
                            "ranking"),
    ("elf_python_motor_voltage_field_weakening_plan / cogging_ripple_plan / "
     "airgap_harmonics_nvh_plan / thermal_network_plan / "
     "manufacturing_tolerance_plan / material_variation_plan / feasibility_study",
                            "Motor-design API layer for voltage/current "
                            "limits, field weakening, cogging and torque "
                            "ripple, air-gap harmonic NVH orders, reduced "
                            "thermal networks, manufacturing robustness, "
                            "material sensitivity, and feasibility gates"),
    ("elf_python_run_result_parse / run_result_parse_path / "
     "motor_optimization_loop / "
     "motor_ngsolve_result_crosscheck / motor_drawing_bom_handoff / "
     "motor_rotor_stress_retention_plan / motor_validation_scorecard",
                            "Closed-loop motor design API layer: normalize "
                            "local RunResult payloads or user-local result "
                            "files, rank candidates, "
                            "cross-check NGSolve runtime JSON, and prepare "
                            "rotor-stress, drawing/BOM, and validation "
                            "scorecard handoffs without exposing raw private "
                            "outputs"),
    ("elf_python_motor_market_brief / motor_design_agent_handoff",
                            "Spec-to-design-agent layer for robotics/drone "
                            "and servo markets: user spec intake, GUI-free "
                            "licensed-backend handoff, required NGSolve "
                            "NVH/thermal/stress routing, "
                            "drawing/BOM/prototype deliverables"),
    ("elf_python_ngsolve_validation_plan / validation_script",
                            "Executable open-validation implementation for "
                            "motor thermal, NVH, and mechanical stress checks: "
                            "builds NGSolve lane jobs and runnable Python "
                            "scripts from parsed observables and public specs"),
    ("elf_recipe_index / search / get / plan", "Public-safe workflow "
                                                "recipes for choosing ELF "
                                                "elements, PRE/SOL blocks, "
                                                "outputs, checks, and pitfalls"),
    ("elf_wiki_index / search / get", "elf.co.jp PukiWiki cache "
                                       "(146 pages, 211 KB)"),
    ("elf_python_index / search / get; elf_python_team28",
                                                  "C:/ELF600/bin/ Python ctypes "
                                                  "API + config (15 files, 246 KB) "
                                                  "plus Python-interface seed manifest"),
]

_RELATED_PUBLIC_PACKAGES = [
    ("radia-mcp", "pip install radia-mcp",
     "https://github.com/ksugahar/Radia",
     "Optional public companion for open electromagnetic modeling references"),
]


@mcp.tool()
def elf_overview() -> dict:
    """RECOMMENDED FIRST CALL. Catalog of ELF MCP's 87 tools + 1
    prompt, with public-safe routing hints for MCP clients.

    Returns:
        dict with `tool_families` (curated 85-tool grouping), `n_tools`,
        public boundary notes, recommended calls, and public companion package
        hints.
    """
    return {
        "n_tools": 87,
        "n_prompts": 1,
        "tool_families": [
            {"signature": sig, "description": desc}
            for sig, desc in _TOOL_CATALOG
        ],
        "recommended_calls": [
            {
                "goal": "Inspect the server surface",
                "call": "elf_overview()",
            },
            {
                "goal": "Check whether the public MCP package is ready for tag push",
                "call": "elf_mcp_readiness()",
            },
            {
                "goal": "Audit motor-specific corpus breadth and validation gaps",
                "call": "elf_motor_readiness()",
            },
            {
                "goal": "Route motor work across ELF deck, radia AGE validation, and MMM quick check",
                "call": "elf_motor_hybrid_router('IPM hairpin motor flux linkage and MTPA')",
            },
            {
                "goal": "Run a public-safe 2D MMM/BEM-like motor quick check",
                "call": "elf_motor_mmm_quick_check(motor_type='SPM')",
            },
            {
                "goal": "Find the right ELF/MAGIC command pattern",
                "call": "elf_usage(topic='all') or elf_recipe_search(query)",
            },
            {
                "goal": "Route a user prompt to the right public input-deck family",
                "call": "elf_sample_decks_route('IPM hairpin motor flux linkage')",
            },
            {
                "goal": "Prepare a public-safe handoff to a user-local ELF/MAGIC runner",
                "call": "elf_local_simulation_handoff('SPM motor flux linkage sweep')",
            },
            {
                "goal": "Parse completed local run-result files without exposing raw outputs",
                "call": "elf_python_run_result_parse_path(run_path='<local run directory>')",
            },
            {
                "goal": "Build a numeric efficiency map from parsed RunResults",
                "call": "elf_python_motor_efficiency_map_from_results(result_payloads_json='<JSON list>')",
            },
            {
                "goal": "Learn from the 1600 public input-deck cases",
                "call": "elf_sample_decks_playbook(limit=20, query='permanent magnet HBRM')",
            },
            {
                "goal": "Start from curated representative decks",
                "call": "elf_sample_decks_representatives(area='motor')",
            },
            {
                "goal": "Inspect quality labels for public sample families",
                "call": "elf_sample_decks_quality(label='gold')",
            },
            {
                "goal": "Inspect physical quantities covered by public samples",
                "call": "elf_sample_decks_physics(quantity='force')",
            },
            {
                "goal": "Map prompt intent to quantity, quality label, validation method, and representative decks",
                "call": "elf_sample_decks_validation_matrix(quantity='transformer')",
            },
            {
                "goal": "Audit the 500-case observable-contract quality upgrade",
                "call": "elf_sample_decks_observable_contracts()",
            },
            {
                "goal": "Audit cross-validation coverage and gaps",
                "call": "elf_sample_decks_cross_validation()",
            },
            {
                "goal": "Prepare a public motor deck for independent AGE and VIM review lanes",
                "call": "elf_motor_dual_solver_review_packet()",
            },
            {
                "goal": "Audit duplicate/deck-reuse groups before deleting samples",
                "call": "elf_sample_decks_duplicates()",
            },
            {
                "goal": "Draft public-safe promotion copy",
                "call": "elf_public_promotion(audience='ja')",
            },
            {
                "goal": "Check validation levels before claiming a deck is validated",
                "call": "elf_sample_decks_validation()",
            },
            {
                "goal": "Open a specific public .mai/.meg input deck",
                "call": "elf_sample_decks_get(path)",
            },
            {
                "goal": "Inspect the Python-interface team28 seed manifest",
                "call": "elf_python_team28()",
            },
            {
                "goal": "Inspect the public Python facade and immutable DLL-boundary design",
                "call": "elf_python_interface_design(topic='overview')",
            },
            {
                "goal": "Load the LLM-oriented Python API manual and call order",
                "call": "elf_python_api_manual(topic='quickstart')",
            },
            {
                "goal": "Inspect the concrete public Python API schema and MotorSpec template",
                "call": "elf_python_api_schema(motor_type='spm')",
            },
            {
                "goal": "Lint a public .mai deck against requested observables before a local run",
                "call": "elf_python_deck_lint(mai_path='application/motor/pm_cosine_pickup_72/pm001/pm001.mai', requested_observables='flux_linkage,back_emf_constant')",
            },
            {
                "goal": "Check HBRM/HBCN PM demagnetization 3-step deck contract before a local run",
                "call": "elf_python_pm_demag_step_lint(mai_path='application/motor/spm_loop_10/spl001/spl001.mai')",
            },
            {
                "goal": "Choose a .meg generation backend for a 2D/3D motor prompt",
                "call": "elf_python_meg_generation_plan(goal='2D SPM motor cross-section', dimension='2d')",
            },
            {
                "goal": "Draft a constrained 2D motor geometry template before Netgen remeshing",
                "call": "elf_python_2d_motor_template(motor_type='spm', pole_pairs=4, stator_slots=48)",
            },
            {
                "goal": "Plan motor design variables, studies, observables, and validation gates",
                "call": "elf_python_motor_design_plan(goal='IPM torque density and Ld/Lq')",
            },
            {
                "goal": "Build a deterministic DOE/sweep matrix for motor design",
                "call": "elf_python_motor_sweep_matrix(motor_type='spm', objective='back_emf_target', budget=9)",
            },
            {
                "goal": "Build an Id/Iq map with PM and reluctance torque decomposition",
                "call": "elf_python_motor_dq_axis_map_plan(motor_type='ipm')",
            },
            {
                "goal": "Search MTPA current angle candidates",
                "call": "elf_python_motor_mtpa_search_plan(motor_type='ipm')",
            },
            {
                "goal": "Plan SynRM/PMa-SynRM/SRM reluctance motor design",
                "call": "elf_python_reluctance_motor_design_plan(motor_type='pm_assisted_synrm')",
            },
            {
                "goal": "Start an advanced motor model: BLDC, line-start PM, deep-bar IM, flux-switching, Vernier, transverse-flux, slotless, claw-pole, or commutator",
                "call": "elf_python_motor_design_plan(goal='six-step BLDC torque ripple')",
            },
            {
                "goal": "Build a phase-belt winding layout and winding-factor proxy",
                "call": "elf_python_motor_winding_layout_plan(stator_slots=48, pole_pairs=4)",
            },
            {
                "goal": "Choose topology-specific geometry variables and constraints",
                "call": "elf_python_motor_topology_parameter_plan(motor_type='ipm', rotor_topology='inner_rotor')",
            },
            {
                "goal": "Screen PM demagnetization margin before high-current field weakening",
                "call": "elf_python_motor_demag_margin_plan(motor_type='spm', temperature_c=120)",
            },
            {
                "goal": "Plan voltage limits and field-weakening operating points",
                "call": "elf_python_motor_voltage_field_weakening_plan(motor_type='ipm', dc_bus_v=48)",
            },
            {
                "goal": "Plan cogging torque and torque-ripple reduction",
                "call": "elf_python_motor_cogging_ripple_plan(stator_slots=48, pole_pairs=4)",
            },
            {
                "goal": "Route air-gap harmonics into NVH force-order validation",
                "call": "elf_python_motor_airgap_harmonics_nvh_plan(stator_slots=48, pole_pairs=4)",
            },
            {
                "goal": "Build a motor efficiency-map operating grid",
                "call": "elf_python_motor_efficiency_map_plan(motor_type='spm')",
            },
            {
                "goal": "Turn map axes into concrete local-run operating rows",
                "call": "elf_python_motor_operating_point_run_queue(motor_type='spm')",
            },
            {
                "goal": "Plan inverter/PWM harmonic rows for AC loss and ripple screening",
                "call": "elf_python_motor_inverter_pwm_harmonic_plan(motor_type='spm', switching_frequency_hz=20000)",
            },
            {
                "goal": "Plan saturated Ld/Lq maps over current amplitude and current angle",
                "call": "elf_python_motor_saturation_inductance_map_plan(motor_type='ipm')",
            },
            {
                "goal": "Attach weighted drive-cycle points to an efficiency map",
                "call": "elf_python_motor_drive_cycle_plan(target_market='robot_drone')",
            },
            {
                "goal": "Plan a constrained motor optimization study",
                "call": "elf_python_motor_optimization_study_plan(motor_type='spm', objective='cycle_efficiency')",
            },
            {
                "goal": "Build a reduced thermal network before NGSolve thermal validation",
                "call": "elf_python_motor_thermal_network_plan(total_loss_w=25)",
            },
            {
                "goal": "Plan manufacturing tolerance robustness studies",
                "call": "elf_python_motor_manufacturing_tolerance_plan(motor_type='spm', airgap_mm=0.8)",
            },
            {
                "goal": "Plan material sensitivity studies",
                "call": "elf_python_motor_material_variation_plan(motor_type='spm', focus='all')",
            },
            {
                "goal": "Build a feasibility gate for prototype or small-lot motor work",
                "call": "elf_python_motor_feasibility_study(goal='outer-rotor drone motor')",
            },
            {
                "goal": "Define motor loss terms for efficiency-map postprocessing",
                "call": "elf_python_motor_loss_model_contract(motor_type='spm')",
            },
            {
                "goal": "Clip map points with a torque-speed envelope",
                "call": "elf_python_motor_torque_speed_envelope(motor_type='spm')",
            },
            {
                "goal": "Plan an induction-motor slip sweep",
                "call": "elf_python_induction_slip_sweep_plan(pole_pairs=2, supply_frequency_hz=50)",
            },
            {
                "goal": "Map a motor study to ELF markers and RunResult parser keys",
                "call": "elf_python_motor_observable_contract(motor_type='ipm', study='dq_inductance')",
            },
            {
                "goal": "Normalize a local RunResult payload into parsed observables",
                "call": "elf_python_run_result_parse(payload='torque_nm=0.8\\nloss_w=12')",
            },
            {
                "goal": "Rank parsed candidate results and choose next optimization rows",
                "call": "elf_python_motor_optimization_loop(motor_type='spm', objective='cycle_efficiency')",
            },
            {
                "goal": "Cross-check local RunResult observables against NGSolve runtime JSON",
                "call": "elf_python_motor_ngsolve_result_crosscheck(run_result_payload='{}', ngsolve_result_payload='{}')",
            },
            {
                "goal": "Prepare drawing/BOM prototype handoff after validation labels",
                "call": "elf_python_motor_drawing_bom_handoff(motor_type='spm', validation_label='needs_local_run')",
            },
            {
                "goal": "Screen high-speed rotor stress and retention before prototype release",
                "call": "elf_python_motor_rotor_stress_retention_plan(motor_type='spm', max_speed_rpm=12000)",
            },
            {
                "goal": "Combine parsed results, NGSolve lanes, and handoff labels into a promotion scorecard",
                "call": "elf_python_motor_validation_scorecard(run_result_payload='{}', ngsolve_result_payload='{}')",
            },
            {
                "goal": "Build a robotics/drone SPM spec-intake brief",
                "call": "elf_python_motor_market_brief(target_market='robot_drone', motor_type='spm', rotor_topology='outer_rotor')",
            },
            {
                "goal": "Prepare a spec-to-design-agent handoff for users who do not operate analysis software",
                "call": "elf_python_motor_design_agent_handoff(goal='outer-rotor drone SPM motor', target_market='robot_drone')",
            },
            {
                "goal": "Build required NGSolve thermal/NVH/stress validation jobs",
                "call": "elf_python_ngsolve_validation_plan(goal='outer-rotor drone SPM motor')",
            },
            {
                "goal": "Generate a runnable NGSolve validation script",
                "call": "elf_python_ngsolve_validation_script(goal='outer-rotor drone SPM motor', lane='all')",
            },
        ],
        "public_boundary": (
            "Documentation and lab-authored public input decks only. This MCP "
            "server does not execute ELF, launch GUI/CLI solvers, bundle solver "
            "outputs, expose comparison metrics, or publish private validation "
            "provenance."
        ),
        "related_public_packages": [
            {"name": n, "install": inst, "github": gh, "description": d}
            for n, inst, gh, d in _RELATED_PUBLIC_PACKAGES
        ],
        "next_step_hint":
            "Call elf_usage(topic='all') for the 32 curated topic "
            "catalogue, elf_plan_workflow('goal') for a workflow plan, "
            "elf_mcp_readiness() for release-quality gates, "
            "elf_motor_readiness() for motor-specific coverage and validation gaps, "
            "elf_motor_hybrid_router('goal') for ELF/radia/MMM motor dispatch, "
            "elf_motor_mmm_quick_check(motor_type='spm') for quick sign/scale checks, "
            "elf_recipe_search('keyword') for decision cards, or "
            "elf_sample_decks_playbook() for ELF-runnable public .mai/.meg decks, "
            "elf_sample_decks_representatives() for curated first-stop decks, "
            "elf_sample_decks_quality() for quality labels, "
            "elf_sample_decks_physics() for physical-quantity coverage, "
            "elf_local_simulation_handoff('goal') for public-safe local runner contracts, "
            "elf_sample_decks_validation_matrix() for quantity-to-validation routing, "
            "elf_sample_decks_observable_contracts() for the 500-case observable-contract audit, "
            "elf_sample_decks_cross_validation() for cross-validation gaps, "
            "elf_sample_decks_duplicates() before deleting apparent duplicates, "
            "elf_sample_decks_validation() for public validation levels and limits, "
            "elf_public_promotion() for public-safe promotion copy, "
            "elf_python_team28() for the Python-interface team28 seed manifest, "
            "elf_python_interface_design() for the public Python facade contract, "
            "elf_python_api_manual() for the LLM-oriented API manual, "
            "elf_python_api_schema() / elf_python_deck_lint() / "
            "elf_python_pm_demag_step_lint() / "
            "elf_python_run_contract() for concrete Python facade contracts, "
            "elf_python_meg_generation_plan() for Cubit/Netgen/LLM 2D MEG routing, "
            "elf_python_2d_motor_template() for constrained 2D motor drafting, "
            "elf_python_motor_design_plan() / elf_python_motor_sweep_matrix() / "
            "elf_python_motor_observable_contract() for design-variable APIs, "
            "elf_python_motor_efficiency_map_plan() / "
            "elf_python_motor_loss_model_contract() / "
            "elf_python_motor_torque_speed_envelope() / "
            "elf_python_induction_slip_sweep_plan() for motor-design maps, "
            "loss models, envelopes, and IM slip sweeps, "
            "elf_python_motor_operating_point_run_queue() / "
            "elf_python_motor_inverter_pwm_harmonic_plan() / "
            "elf_python_motor_saturation_inductance_map_plan() for concrete "
            "operating rows, PWM harmonic screening, and saturated Ld/Lq maps, "
            "elf_python_motor_dq_axis_map_plan() / elf_python_motor_mtpa_search_plan() / "
            "elf_python_reluctance_motor_design_plan() for Id/Iq maps, "
            "MTPA, SynRM, PMa-SynRM, and SRM reluctance design, "
            "elf_python_motor_winding_layout_plan() / "
            "elf_python_motor_topology_parameter_plan() / "
            "elf_python_motor_demag_margin_plan() / "
            "elf_python_motor_drive_cycle_plan() / "
            "elf_python_motor_optimization_study_plan() for winding, "
            "topology, demag, drive-cycle, and optimization design-suite APIs, "
            "elf_python_motor_voltage_field_weakening_plan() / "
            "elf_python_motor_cogging_ripple_plan() / "
            "elf_python_motor_airgap_harmonics_nvh_plan() / "
            "elf_python_motor_thermal_network_plan() / "
            "elf_python_motor_manufacturing_tolerance_plan() / "
            "elf_python_motor_material_variation_plan() / "
            "elf_python_motor_feasibility_study() for production-style "
            "motor design gates, "
            "elf_python_run_result_parse() / elf_python_motor_optimization_loop() / "
            "elf_python_motor_ngsolve_result_crosscheck() / "
            "elf_python_motor_drawing_bom_handoff() / "
            "elf_python_motor_rotor_stress_retention_plan() / "
            "elf_python_motor_validation_scorecard() for closed-loop "
            "RunResult parsing, candidate ranking, validation reconciliation, "
            "rotor stress screening, scorecards, and prototype handoff, "
            "elf_python_motor_market_brief() / elf_python_motor_design_agent_handoff() "
            "for spec-to-design-agent workflows, "
            "elf_python_ngsolve_validation_plan() / elf_python_ngsolve_validation_script() "
            "for required open NGSolve multiphysics validation implementation, "
            "elf_help_search('keyword') / "
            "elf_examples_search('keyword') for raw access, or "
            "elf_examples_playbook(limit=100) for compact example cards.",
    }


@mcp.tool()
def elf_agentic_profile() -> dict:
    """Return ELF/MAGIC MCP agentic runtime, boundary, and verification policy."""
    return {
        "schema": "cae-ai-lab.agentic-mcp-profile.v1",
        "server": "ELF-mcp-server",
        "runtime_pattern": "FastMCP public documentation/input-deck server; no ELF/MAGIC solver execution",
        "mathworks_reference_pattern": {
            "runtime_vs_skills": "Keep callable public docs/contracts separate from private runner skills, mirroring MATLAB MCP Server plus Agentic Toolkit.",
            "environment_probe": "Call elf_overview and elf_mcp_readiness before release or tag push claims.",
            "focused_skills": "Use motor/demag/BEM/public-deck skills only when the source lane is ELF/MAGIC.",
            "result_contract": "Expose public input contracts and scrubbed observable schemas; keep local RunResult files and commercial numbers private.",
        },
        "recommended_first_calls": [
            "elf_overview",
            "elf_mcp_readiness",
            "elf_motor_readiness",
            "elf_sample_decks_validation_matrix",
        ],
        "execution_policy": {
            "public_boundary": "product-public documentation MCP",
            "executes_solver": False,
            "ships_solver_outputs": False,
            "private_converter": "separate private converter lane; not bundled or exposed by this public MCP",
            "private_validation_store": "separate private validation store; not bundled or exposed by this public MCP",
            "temp_root": "runner-local temporary directory",
        },
        "source_lane": {
            "public_mcp_server": "ELF/MAGIC product documentation MCP package",
            "private_converter": "separate non-public converter lane",
            "private_validation_lane": "separate non-public validation lane",
        },
        "verification": [
            "python -m pytest tests/test_smoke.py -q",
            "python -m elf_mcp_server.policy_lint",
            "elf-mcp-server --selftest",
        ],
        "balanced_learning": build_balanced_learning_profile(
            "ELF-mcp-server", "radia-mcp", "ELF/MAGIC product MCP"
        ),
        "mcp_learning_rule": "An ELF/MAGIC product slot is learned only after public-safe ELF MCP knowledge/input contracts and scrubbed radia motor/demag/BEM gates are verified; raw product results remain private.",
    }


# ============================================================
# MCP Tools
# ============================================================

@mcp.tool()
def elf_usage(topic: str = "all") -> str:
    """
    Get ELF600 electromagnetic field analysis documentation.

    ELF600 is a BEM-based electromagnetic analysis suite with three solvers:
    MAGIC (magnetostatic), ELFIN (electrostatic), BEAM (particle tracking).
    Input consists of .mai (analysis control), .mei (mesh script), and
    .meg (compiled mesh) files.

    Args:
        topic: Documentation topic. Options:
            "all"              - Complete documentation (~60k chars)
            "overview"         - ELF600 suite overview, solver modules, tools
            "mai_format"       - .mai file format (PRE keywords, all solvers)
            "mei_format"       - .mei file format (mesh scripting structure)
            "meg_format"       - .meg file format (symmetry, nodes, elements)
            "magic"            - MAGIC magnetostatic solver details
            "elfin"            - ELFIN electrostatic solver (D-E curves)
            "beam"             - BEAM particle tracking (RELA, BINT, GRAV)
            "element_types"    - All element types (MAGIC/ELFIN/BEAM, DOF)
            "bh_curves"        - B-H curves, recoil, extrapolation
            "sol_commands"     - SOL blocks, NONL strategy, PASS optimization
            "mei_commands"     - IEmesh commands (AA/AN/AE/ME/BE/TE/NB/...)
            "ipm_motor"        - IPM motor Ld/Lq calculation workflow
            "motor_radia_bridge" - Translate radia-mcp/open motor-FEA
                                 quantities (air-gap field, torque,
                                 flux linkage/back-EMF, lamination, eddy
                                 currents) to ELF/MAGIC elements, SOL blocks,
                                 and extraction steps
            "inductance"       - Lsc (JIS) and Ll (IEEJ) with 6 samples
            "magnetization"    - Magnetization (MAGNE2) and demagnetization
            "examples"         - Example file catalog
            "meg_export"       - MEG export from Cubit (labels, DIM)
            "treasure_box"     - Quick-reference tables (element-PRE map, etc.)
            "sinusoidal"       - SOL MOMC, complex permeability, AC force
            "anisotropy"       - HBA1/HBA2, VEC1/VEC3, lamination
            "sted"             - Steady-state eddy current motion
            "meshing"          - Element quality, gaps, connectivity rules
            "convergence"      - Nonlinear convergence troubleshooting
            "force_methods"    - FORC vs FORT vs FIXB comparison
            "errors"           - Error messages (ELF-Q/E/W, 160+ codes)
            "iemesh"           - IEmesh tool overview and command families
            "tools"            - Wmap3, MagFilter2, MaiEditor3, ELF/Bench
            "cln_extraction"   - ELF MAGIC -> Cauer Ladder Network synthesis
                                 workflow (6-step Foster + Cauer-I/II + 3-way
                                 cross-validation against step response /
                                 Joule loss / Lorentz force). Distilled from
                                 a 21-script rectangular-CLN reference suite.
            "licensing"        - Sentinel HL USB dongle (HASP): run-time,
                                 Admin Control Center (localhost:1947), and
                                 "dongle not recognized" troubleshooting
                                 (Code 43 / descriptor-request-failed on USB 3.x
                                 -> move to a USB 2.0 port)
            "python_api"       - Python ctypes API: DLL wrappers (magtypes /
                                 elftypes), Fortran-ABI calling convention,
                                 end-to-end call sequence, key function table,
                                 _R return variants, common pitfalls
            "live_drive"       - Open MAGIC kernel live-drive note
            "force_gap_contract" - PM force-gap observable contract for
                                 ELF/MAGIC force rows before open validation
    """
    return get_elf_documentation(topic)


@mcp.tool()
def elf_mcp_readiness() -> str:
    """
    Check public MCP readiness before release/tag push.

    This aggregates publication-quality gates, cross-validation gates, exact
    duplicate checks, local-runner handoff boundary checks, and high-value
    prompt routing checks. It is intended for MCP clients and maintainers to
    decide whether the public package is ready to tag and publish.

    Returns:
        Markdown readiness report. `ready_for_tag_push` means the public MCP
        quality gates pass locally; GitHub/PyPI still require tag push and CI.
    """
    return format_mcp_readiness(build_mcp_readiness())


@mcp.tool()
def elf_motor_readiness(family: str = "") -> str:
    """
    Audit motor-specific public sample coverage and validation gaps.

    This answers whether the public motor corpus is broad enough for MCP
    routing, where it is still only proxy-validated, and which radia-motor /
    radia-ngsolve validation targets should be strengthened next.

    Args:
        family: Optional motor-family substring such as "spm", "ipm",
            "induction", "srm", "synrm", "reluctance", or "hysteresis".

    Returns:
        Markdown motor-readiness report with archetype coverage, quality
        labels, validation-depth gaps, and radia-motor strengthening targets.
    """
    return format_motor_readiness(build_motor_readiness(family=family or None))


@mcp.tool()
def elf_motor_hybrid_router(goal: str) -> str:
    """
    Route a motor goal across ELF decks, radia AGE validation, and MMM quick checks.

    This is the public MCP dispatch layer for the hybrid workflow:
    ELF/MAGIC public `.mai/.meg` decks for product-input authoring, radia-motor's
    2D MMM/BEM-like quick check for first-order sign/scale sanity, NGSolve AGE
    for independent physics validation, and a user-local ELF/MAGIC runner for
    product solves. It does not execute any solver.

    Args:
        goal: Natural-language motor goal such as "SPM back-EMF",
            "IPM hairpin MTPA", "induction motor slip loss", or
            "SRM reluctance torque".

    Returns:
        Markdown dispatch plan with deck routes, radia-motor quick-check calls,
        AGE validation targets, and local ELF/MAGIC handoff.
    """
    return format_motor_hybrid_router(build_motor_hybrid_router(goal))


@mcp.tool()
def elf_motor_mmm_quick_check(
    motor_type: str = "spm",
    pole_pairs: int = 4,
    airgap_radius_m: float = 0.05,
    stack_length_m: float = 0.05,
    airgap_m: float = 1.0e-3,
    turns_per_phase: float = 50.0,
    phase_current_a: float = 10.0,
    electrical_angle_deg: float = 0.0,
    magnet_br_t: float = 1.2,
    magnet_thickness_m: float = 3.0e-3,
    magnet_arc_fraction: float = 0.75,
    saliency_ratio_lq_over_ld: float = 1.5,
    slip_hz: float = 5.0,
) -> str:
    """
    Public-safe 2D MMM/BEM-like motor quick check.

    This is a first-order magnetic-circuit style evaluator for sign/scale
    sanity checks before local ELF/MAGIC product runs or NGSolve AGE validation.
    It estimates PM flux linkage, back-EMF constant, dq torque proxy, and an
    induction slip-loss proxy. It does not execute ELF/MAGIC or NGSolve.

    Args:
        motor_type: "spm", "ipm", "induction", "srm", "synrm",
            "hysteresis", etc.
        pole_pairs: Number of pole pairs.
        airgap_radius_m: Air-gap radius in meters.
        stack_length_m: Active stack length in meters.
        airgap_m: Mechanical air gap in meters.
        turns_per_phase: Effective series turns per phase.
        phase_current_a: Peak phase current.
        electrical_angle_deg: Electrical current angle from q-axis convention.
        magnet_br_t: PM remanence in tesla.
        magnet_thickness_m: Magnet thickness in meters.
        magnet_arc_fraction: Fraction of pole pitch covered by magnet.
        saliency_ratio_lq_over_ld: Lq/Ld proxy for IPM/SynRM/SRM checks.
        slip_hz: Slip frequency for induction-machine proxy checks.

    Returns:
        Markdown quick-check report and AGE validation route.
    """
    result = build_motor_mmm_quick_check(
        motor_type=motor_type,
        pole_pairs=pole_pairs,
        airgap_radius_m=airgap_radius_m,
        stack_length_m=stack_length_m,
        airgap_m=airgap_m,
        turns_per_phase=turns_per_phase,
        phase_current_a=phase_current_a,
        electrical_angle_deg=electrical_angle_deg,
        magnet_br_t=magnet_br_t,
        magnet_thickness_m=magnet_thickness_m,
        magnet_arc_fraction=magnet_arc_fraction,
        saliency_ratio_lq_over_ld=saliency_ratio_lq_over_ld,
        slip_hz=slip_hz,
    )
    return format_motor_mmm_quick_check(result)


@mcp.tool()
def elf_help_index(prefix: str = "") -> str:
    """
    List all 1141 ELF600 help files (HTM source) bundled with this server.

    Useful for discovering files to read with ``elf_help_get``.

    Args:
        prefix: Filter by path prefix (e.g. "m_rf1/" for MAGIC reference,
                "d_ken/" for technical docs, "u_support/" for error messages,
                "m_treasure/" for quick-reference tables, etc.).
                Empty string lists all files.

    Returns:
        Tab-separated list: PATH<TAB>CHARS<TAB>TITLE per line.
    """
    files = list_help_files(prefix=prefix or None)
    if not files:
        return f"No files match prefix '{prefix}'. Try 'm_rf1/', 'e_rf1/', 'b_rf1/', 'd_ken/', 't_iemesh/', etc."
    lines = [f"{f['path']}\t{f['char_count']}\t{f['title']}" for f in files]
    header = f"# {len(files)} files" + (f" under '{prefix}'" if prefix else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_help_search(query: str, top_k: int = 10, prefix: str = "") -> str:
    """
    Substring-search across all 1141 ELF600 help files (case-insensitive).

    Multiple keywords (space-separated) require ALL to match (AND).
    Returns ranked snippets — drill into specific files via ``elf_help_get``.

    Args:
        query: Search keywords (e.g. "MOMC sinusoidal", "渦電流 MAB",
               "OHM2 resistivity", "FORC FIXB").
        top_k: Max results to return (default 10).
        prefix: Restrict search to a directory (e.g. "m_rf1/", "d_ken/").

    Returns:
        Ranked list of matches with title and ~300-char snippet.
    """
    results = search_help(query, top_k=top_k, prefix=prefix or None)
    if not results:
        return f"No matches for '{query}'" + (f" under '{prefix}'" if prefix else "")
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['path']}  (score={r['score']})")
        if r["title"]:
            out.append(f"_title: {r['title']}_")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_examples_index(solver: str = "", category: str = "", ext: str = "") -> str:
    """
    List all 332 ELF600 example input files (.mai analysis + .mei mesh + .txt + .props + .model)
    bundled with this server, from C:/ELF600/examples/.

    Use this to discover authoritative input file templates for any ELF analysis pattern.
    The examples cover: BASIC, IPM motors, LscLl inductance, MK Maxwell, MOMC sinusoidal,
    MR moment, MT time-stepping, V6Conv, WorkBook (MAGIC: 228 files), ELFIN: 66, BEAM: 38.

    Args:
        solver: "MAGIC" / "ELFIN" / "BEAM" (case-insensitive, empty = all).
        category: Subcategory filter ("BASIC", "IPM", "MOMC", "LscLl", etc.).
        ext: File extension ("mai", "mei", "txt", "props", "model"). Empty = all.

    Returns:
        Tab-separated: PATH<TAB>SOLVER<TAB>CATEGORY<TAB>EXT<TAB>CHARS per line.
    """
    files = list_examples(solver=solver or None, category=category or None, ext=ext or None)
    if not files:
        return f"No examples match (solver='{solver}', category='{category}', ext='{ext}')."
    lines = [f"{f['path']}\t{f['solver']}\t{f['category']}\t{f['ext']}\t{f['char_count']}"
             for f in files]
    filt = []
    if solver: filt.append(f"solver={solver}")
    if category: filt.append(f"category={category}")
    if ext: filt.append(f"ext={ext}")
    header = f"# {len(files)} examples" + (f" ({', '.join(filt)})" if filt else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_examples_search(query: str, top_k: int = 10, solver: str = "", ext: str = "") -> str:
    """
    Substring-search across all 332 ELF600 example input files (case-insensitive).

    Multiple keywords (space-separated) require ALL to match (AND).
    Find concrete .mai/.mei templates that demonstrate specific keywords/elements.

    Args:
        query: Keywords (e.g. "MOMC FREQ", "OHM2 MAB", "AMP1I", "HBA1 lamination").
        top_k: Max results.
        solver: Restrict to "MAGIC" / "ELFIN" / "BEAM".
        ext: Restrict to "mai" / "mei" / "txt".

    Returns:
        Ranked snippets — drill into specific files via ``elf_examples_get``.
    """
    results = search_examples(query, top_k=top_k, solver=solver or None, ext=ext or None)
    if not results:
        return f"No matches for '{query}'"
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['path']}  ({r['solver']}/{r['category']}, .{r['ext']}, score={r['score']})")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_examples_get(path: str, max_chars: int = 30000) -> str:
    """
    Get full text of a specific ELF600 example input file.

    Args:
        path: Relative path under C:/ELF600/examples/, e.g. "magic/BASIC/ABCL2.mai",
              "magic/MOMC/coil_eddy.mai", "elfin/MOMC/cap1.mei".
              Filename-only also works if unambiguous.
        max_chars: Truncate output if longer (default 30000).

    Returns:
        File metadata + raw text (Shift_JIS decoded if needed).
    """
    result = get_example(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{path}': {result['error']}"
    head = f"# {result['path']}  ({result['solver']}/{result['category']}, .{result['ext']})"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


@mcp.tool()
def elf_examples_playbook(
    limit: int = 100,
    solver: str = "",
    category: str = "",
    feature: str = "",
    query: str = "",
) -> str:
    """
    Build compact public-safe cards from bundled ELF example .mai files.

    This is the fastest way to browse many authoritative examples without
    reading raw files one by one. Each card lists the example path, paired
    .mei/.model/.props files, detected SOL blocks, element families, keywords,
    feature tags, and a one-line reuse hint.

    Args:
        limit: Number of cards to return. Default 100. Max 200.
        solver: Optional solver filter: "MAGIC", "ELFIN", or "BEAM".
                Note: bundled MAGIC has 97 .mai examples; leaving this empty
                returns 100 cards by adding ELFIN/BEAM cards after MAGIC.
        category: Optional category filter such as "BASIC", "IPM", "MT",
                  "LscLl", "MOMC", "MK", "MR", "magne".
        feature: Optional feature tag filter, e.g. "motor", "flux-linkage",
                 "maxwell-force", "eddy-current", "sinusoidal-ac",
                 "electrostatic", "beam".
        query: Optional keyword filter across path, tags, and example text.

    Returns:
        Markdown-formatted compact cards. Drill down into any raw file with
        ``elf_examples_get(path)``.
    """
    cards = build_example_cards(
        limit=limit,
        solver=solver or None,
        category=category or None,
        feature=feature or None,
        query=query or None,
    )
    return format_example_cards(cards)


@mcp.tool()
def elf_sample_decks_index(family: str = "", case: str = "", ext: str = "") -> str:
    """
    List lab-authored public runnable ELF/MAGIC sample decks.

    These are `.mai` and `.meg` input files only. Solver outputs and
    comparison metrics are intentionally not bundled.

    Args:
        family: Optional family substring, e.g. "motor", "pm_square",
            "spm", "srm", "sr_motor", "induction", "ipm",
                "emdlab", "afpm", "linear_pm", "stepper",
                "wound_field", "synrm", "reluctance",
                "hysteresis", "application", "wpt", "mri", "ih",
                "transformer", "accelerator", "actuator", "maglev",
                "separator", "brake", "ndt", "magnetic_gear",
                "voice_coil", "relay_solenoid", "hall_sensor",
                or "clutch".
        case: Optional case ID such as "pm001".
        ext: Optional file extension: "mai" or "meg".

    Returns:
        Tab-separated: PATH<TAB>FAMILY<TAB>CASE<TAB>EXT<TAB>CHARS per line.
    """
    decks = list_sample_decks(family=family or None, case=case or None, ext=ext or None)
    if not decks:
        return f"No sample decks match (family='{family}', case='{case}', ext='{ext}')."
    lines = [
        f"{d['path']}\t{d['family']}\t{d['case']}\t{d['ext']}\t{d['char_count']}"
        for d in decks
    ]
    filters = []
    if family:
        filters.append(f"family={family}")
    if case:
        filters.append(f"case={case}")
    if ext:
        filters.append(f"ext={ext}")
    header = f"# {len(decks)} sample decks" + (f" ({', '.join(filters)})" if filters else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_sample_decks_search(query: str, top_k: int = 10, ext: str = "") -> str:
    """
    Search lab-authored public sample deck paths and text.

    Multiple keywords require all terms to match. Use this to find runnable
    `.mai`/`.meg` input decks that contain specific ELF commands such as
    `HBCN`, `MWL8T`, `COI1`, or `FLUM`.

    Args:
        query: Search keywords.
        top_k: Max results.
        ext: Optional extension filter: "mai" or "meg".

    Returns:
        Ranked snippets. Drill down with ``elf_sample_decks_get(path)``.
    """
    results = search_sample_decks(query, top_k=top_k, ext=ext or None)
    if not results:
        return f"No sample deck matches for '{query}'"
    out = [f"# {len(results)} sample deck matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(
            f"## [{i}] {r['path']}  ({r['family']}/{r['case']}, .{r['ext']}, score={r['score']})"
        )
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_sample_decks_route(goal: str, limit: int = 5) -> str:
    """
    Route a natural-language engineering goal to public sample-deck families.

    Use this before raw search when a user prompt says things like
    "IPM hairpin motor", "WPT misalignment", "SynRM flux barrier",
    "stepper detent", or "transformer leakage". The router returns the
    recommended family, why it matches, next MCP calls, and representative
    `.mai` decks to inspect.

    Args:
        goal: Natural-language target or prompt fragment.
        limit: Maximum routes to return. Default 5. Max 12.

    Returns:
        Markdown routing cards with follow-up `elf_sample_decks_playbook`,
        `elf_sample_decks_search`, `elf_sample_decks_get`, and recipe hints.
    """
    routes = route_sample_decks(goal, limit=limit)
    return format_sample_deck_routes(routes, goal)


@mcp.tool()
def elf_local_simulation_handoff(
    goal: str,
    family: str = "",
    quantity: str = "",
    limit: int = 3,
) -> str:
    """
    Prepare a public-safe handoff contract for a user-local ELF/MAGIC runner.

    This is the public MCP bridge between LLM prompt routing and actual local
    simulation. It selects public validated deck families, physical quantities,
    runner input fields, parser output fields, and a motor-design loop. It does
    not execute ELF/MAGIC, launch GUI/CLI solvers, or bundle solver outputs.

    Args:
        goal: Natural-language simulation goal, e.g.
            "SPM motor flux linkage sweep" or "SRM torque angle sweep".
        family: Optional public sample family substring, e.g. "spm",
            "srm", "induction", "ipm", "wpt", or "transformer".
        quantity: Optional physical-quantity substring, e.g. "flux",
            "force", "torque", "loss", "motor", or "transformer".
        limit: Number of candidate deck routes to include. Default 3. Max 8.

    Returns:
        Markdown handoff contract for a private/local runner and parser.
    """
    handoff = build_local_simulation_handoff(
        goal=goal,
        family=family or None,
        quantity=quantity or None,
        limit=limit,
    )
    return format_local_simulation_handoff(handoff)


@mcp.tool()
def elf_sample_decks_get(path: str, max_chars: int = 60000) -> str:
    """
    Get full text of a public runnable ELF/MAGIC sample deck.

    Args:
        path: Relative sample path, e.g.
              "application/motor/pm_cosine_pickup_72/pm001/pm001.mai".
              Filename-only works if unambiguous.
        max_chars: Truncate output if longer. Default 60000, enough for
                   the bundled public `.meg` decks.

    Returns:
        File metadata plus raw `.mai` or `.meg` text.
    """
    result = get_sample_deck(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading sample deck '{path}': {result['error']}"
    head = f"# {result['path']}  ({result['family']}/{result['case']}, .{result['ext']})"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


@mcp.tool()
def elf_sample_decks_playbook(limit: int = 100, family: str = "", query: str = "") -> str:
    """
    Build compact cards from the 1600 public ELF-runnable `.mai`/`.meg` cases.

    Each card links the `.mai` and `.meg` pair and summarizes detected SOL
    blocks, PRE keywords, element types, feature tags, and a reuse hint. This
    is the fastest way to learn from the public deck corpus without reading
    every raw file.

    Args:
        limit: Number of cards to return. Default 100. Max 1600.
        family: Optional family substring, e.g. "pm_square", "cosine",
            "spm", "srm", "sr_motor", "induction", "ipm",
            "emdlab", "afpm", "linear_pm", "stepper", "wound_field",
            "synrm", "reluctance", "hysteresis",
            "wpt", "mri", "ih", "transformer",
            "accelerator", "actuator", "maglev", "separator",
            "brake", "ndt", "magnetic_gear", "voice_coil",
            "relay_solenoid", "hall_sensor", "clutch", or
            "numeric_validation", "numeric_flum_law",
            "numeric_inductance_energy", "numeric_force_torque",
            "numeric_ac_loss", "numeric_magnetic_circuit", or
            "numeric_permanent_magnet", or "numeric_transformer_coupling".
        query: Optional keyword filter across paths, tags, and deck text.

    Returns:
        Markdown compact cards. Drill into raw files with
        ``elf_sample_decks_get(path)``.
    """
    cards = build_sample_deck_cards(limit=limit, family=family or None, query=query or None)
    return format_sample_deck_cards(cards)


@mcp.tool()
def elf_sample_decks_representatives(area: str = "", limit: int = 36) -> str:
    """
    Return curated first-stop representative decks from the 1600-case corpus.

    Args:
        area: Optional area filter, e.g. "motor", "application",
              "numeric", "numeric-gold", "pm", or "wpt".
        limit: Number of representative cards to return. Default 36.

    Returns:
        Markdown cards with representative `.mai`/`.meg` paths, why each deck
        is representative, quality label, validation level, SOL blocks, PRE
        keywords, and element families.
    """
    cards = build_representative_cards(area=area or None, limit=limit)
    return format_representative_cards(cards)


@mcp.tool()
def elf_sample_decks_validation(family: str = "", level: str = "") -> str:
    """
    Summarize public validation levels and limitations for sample decks.

    Use this before claiming validation strength. The result distinguishes
    broad NGSolve proxy-field energy gates from the stronger numeric invariant
    anchors, and states what is not bundled in the public package.

    Args:
        family: Optional family substring such as "numeric_validation",
            "numeric_flum_law", "numeric_inductance_energy",
            "numeric_force_torque", "numeric_ac_loss",
            "numeric_magnetic_circuit", "numeric_permanent_magnet",
            "numeric_transformer_coupling", "emdlab_ipm", "wpt", or "motor".
        level: Optional exact validation level, e.g.
            "ngsolve_proxy_energy" or "ngsolve_numeric_invariant".

    Returns:
        Markdown summary of validation counts, selected families, checks,
        scopes, and public limitations.
    """
    summary = build_validation_summary(family=family or None, level=level or None)
    return format_validation_summary(summary)


@mcp.tool()
def elf_sample_decks_quality(family: str = "", label: str = "") -> str:
    """
    Summarize quality labels for public sample-deck families.

    Quality labels are public-safe wrappers around validation levels:
    `gold_numeric_invariant` for numeric invariant families and
    `silver_observable_contract` for the 500-case observable-contract upgrade,
    plus `silver_proxy_energy` for broader proxy-energy-gated runnable examples.

    Args:
        family: Optional family substring, e.g. "motor", "numeric",
            "transformer", "wpt", or "permanent_magnet".
        label: Optional quality-label substring, e.g. "gold" or "silver".

    Returns:
        Markdown quality-label summary with counts, meaning, recommended use,
        and matching families.
    """
    summary = build_quality_summary(family=family or None, label=label or None)
    return format_quality_summary(summary)


@mcp.tool()
def elf_sample_decks_physics(quantity: str = "", family: str = "") -> str:
    """
    Summarize physical quantities covered by the public sample-deck corpus.

    Use this when an agent needs to decide what physical quantity a prompt is
    asking for before choosing examples or making validation claims. The map is
    derived from public input decks and validation metadata only.

    Args:
        quantity: Optional physical-quantity substring, e.g. "flux",
            "inductance", "force", "torque", "loss", "permanent",
            "transformer", "wpt", or "mri".
        family: Optional family substring, e.g. "motor", "numeric",
            "transformer", "wpt", or "permanent_magnet".

    Returns:
        Markdown physical-quantity coverage with gold/silver counts,
        representative decks, gates, and public-use limitations.
    """
    summary = build_physical_quantity_summary(
        quantity=quantity or None,
        family=family or None,
    )
    return format_physical_quantity_summary(summary)


@mcp.tool()
def elf_sample_decks_validation_matrix(
    quantity: str = "",
    family: str = "",
    label: str = "",
) -> str:
    """
    Map prompt intents to quantities, validation methods, and representative decks.

    This is the recommended audit view when an agent must answer "which
    physical quantity should I evaluate?" or "which validated public deck
    should seed this prompt?" It joins physical quantity coverage, quality
    labels, independent cross-validation methods, representative `.mai`
    decks, and next MCP calls without exposing solver outputs.

    Args:
        quantity: Optional physical-quantity substring, e.g. "flux",
            "force", "torque", "loss", "transformer", "motor", or "wpt".
        family: Optional family substring, e.g. "numeric", "motor",
            "transformer", "permanent_magnet", or "emdlab".
        label: Optional quality-label substring, e.g. "gold" or "silver".

    Returns:
        Markdown validation matrix with quantity rows, family routes,
        cross-validation methods, representative decks, and public-safe notes.
    """
    summary = build_validation_matrix(
        quantity=quantity or None,
        family=family or None,
        label=label or None,
    )
    return format_validation_matrix(summary)


@mcp.tool()
def elf_sample_decks_observable_contracts(family: str = "", label: str = "") -> str:
    """
    Audit the 500-case public observable-contract quality upgrade.

    These cases remain public input decks only, but they have a stronger
    MCP-visible contract than a generic proxy-energy silver case: each selected
    family retains independent NGSolve proxy-energy cross-validation and each
    public `.mai` deck exposes the expected observable markers for the mapped
    physical quantity.

    Args:
        family: Optional family substring, e.g. "motor", "wpt", "mri",
            "transformer", "pm_square", or "emdlab".
        label: Optional quality-label substring, normally
            "silver_observable_contract".

    Returns:
        Markdown audit with gates, family rows, required observable markers,
        representative decks, and public-safe limitations.
    """
    summary = build_observable_contract_summary(
        family=family or None,
        label=label or None,
    )
    return format_observable_contract_summary(summary)


@mcp.tool()
def elf_sample_decks_cross_validation(family: str = "", level: str = "") -> str:
    """
    Audit cross-validation coverage and gaps for the 1600 public sample decks.

    Use this before publishing or before claiming that a sample family is
    cross-validated. The audit reports independent NGSolve cross-check coverage,
    gold dual-invariant coverage, silver proxy-energy coverage, gap status, and
    silver-to-gold upgrade candidates.

    Args:
        family: Optional family substring such as "motor", "numeric",
            "transformer", "wpt", or "permanent_magnet".
        level: Optional exact validation level, e.g.
            "ngsolve_proxy_energy" or "ngsolve_numeric_invariant".

    Returns:
        Markdown cross-validation audit with gates, method counts, gaps,
        selected families, upgrade candidates, and public-use limitations.
    """
    summary = build_cross_validation_summary(
        family=family or None,
        level=level or None,
    )
    return format_cross_validation_summary(summary)


@mcp.tool()
def elf_motor_dual_solver_review_packet(
    family: str = "application/motor/emdlab_ipm_hairpin_10",
    observable: str = "torque",
    limit: int = 3,
) -> str:
    """Build a public-safe source-deck packet for two independent motor lanes.

    The packet selects public input decks and records the comparison contract;
    it contains no licensed solver output or benchmark values.
    """

    limit = max(1, min(int(limit), 10))
    cards = build_sample_deck_cards(limit=limit, family=family or None)
    selected = [
        {
            "family": card.get("family", ""),
            "case": card.get("case", ""),
            "title": card.get("title", ""),
            "mai_path": card.get("mai_path", ""),
            "tags": card.get("tags", []),
            "validation_level": card.get("validation_level", ""),
        }
        for card in cards
    ]
    packet = {
        "schema_version": "motor-source-deck-review-packet/v1",
        "family_filter": family,
        "observable_id": str(observable or "").strip(),
        "selected_decks": selected,
        "required_lanes": ["ngsolve_age", "hdiv_vim_reduced_fem"],
        "required_result_fields": [
            "observable_id",
            "observable_unit",
            "coordinate_frame",
            "sign_convention",
            "solver_version",
            "run_date_utc",
            "timing_breakdown_s",
        ],
        "acceptance_rule": "both required lanes must be solver-validated for the same observable before MCP learning",
        "publication_boundary": "public input-deck metadata and comparison contract only; no solver outputs or benchmark values",
        "status": "ready" if selected and str(observable or "").strip() else "needs_attention",
    }
    return json.dumps(packet, ensure_ascii=False, indent=2)


@mcp.tool()
def elf_sample_decks_duplicates(family: str = "", max_groups: int = 12) -> str:
    """
    Audit exact duplicates and intentional deck reuse in the public sample corpus.

    Use this before deleting examples. Exact `.mai` + `.meg` duplicate pairs are
    the only automatic deletion candidates. Single-file reuse is reported as an
    MCP display/collapse candidate because it usually means one control pattern
    is swept across different geometry, or one geometry is swept across
    different controls, quantities, or validation intents.

    Args:
        family: Optional family substring such as "motor", "pm_square",
            "numeric", "srm", "wpt", or "transformer".
        max_groups: Maximum duplicate/reuse groups to show. Default 12. Max 50.

    Returns:
        Markdown audit with deletion recommendation, duplicate gates, exact
        duplicate groups, and single-file reuse groups.
    """
    summary = build_duplicate_audit(family=family or None, max_groups=max_groups)
    return format_duplicate_audit(summary, max_groups=max_groups)


@mcp.tool()
def elf_public_promotion(audience: str = "ja") -> str:
    """
    Return public-safe promotion copy for ELF-mcp-server.

    Args:
        audience: "ja" / "yano" for Japanese collaborator-facing copy, or
            "en" for English copy.

    Returns:
        Markdown promotion draft that mentions the 1600-case public corpus,
        representative routing, quality labels, and public boundary.
    """
    return format_public_promotion(audience)


@mcp.tool()
def elf_python_team28() -> str:
    """
    Return the Python-interface team28 seed manifest.

    team28 is a compact 28-case tour across 2-pole, 4-pole, 6-pole,
    8-pole, and cosine-remanence PM pickup families. Unlike the normal
    public `.mai`/`.meg` sample decks, team28 is intended for orchestration
    through the ELF Python interface, not normal ELF GUI/CLI deck execution.
    The listed public decks are seed/inspection material for that Python
    orchestration.

    Returns:
        Markdown compact cards for 28 Python-interface seed cases.
    """
    return format_team28_cards(build_team28_cards())


@mcp.tool()
def elf_python_interface_design(topic: str = "overview") -> str:
    """
    Return the public-safe ELF/MAGIC Python-interface design contract.

    The product-side Python implementation is treated as reference material,
    not a required dependency. The vendor DLL boundary is treated as immutable
    product territory. The public MCP/Python facade may still provide richer
    typed schemas, deck builders, validators, routers, and runner/result
    contracts for user-local ELF/MAGIC installations.

    Args:
        topic: "overview", "public_contract", "motor_api",
            "backend_protocol", "deck_generation", "validation",
            "mcp_routing", "vendor_proposal", or "roadmap".

    Returns:
        Markdown design note for a public Python facade and local backend
        protocol. It does not execute ELF/MAGIC or load product binaries.
    """
    return format_python_interface_design(build_python_interface_design(topic))


@mcp.tool()
def elf_python_api_manual(topic: str = "quickstart") -> str:
    """
    Return the LLM-oriented manual for the public Python facade API.

    This is the best first call when an agent needs to use the Python-facing
    ELF/MAGIC workflow. It summarizes policy, objects, call order, deck lint,
    `.meg` generation, local backend contracts, validation rules, and examples.

    Args:
        topic: "quickstart", "objects", "llm_call_order", "deck_lint",
            "meg_generation", "local_backend", "validation", "examples",
            or "all".

    Returns:
        Compact Markdown manual optimized for LLM clients.
    """
    return format_python_api_manual(build_python_api_manual(topic))


def _parse_observables(text: str) -> list[str]:
    """Parse comma/space separated observable names."""
    return [part.strip().lower() for part in re.split(r"[\s,]+", text or "") if part.strip()]


@mcp.tool()
def elf_python_api_schema(motor_type: str = "spm") -> str:
    """
    Return the concrete public Python facade schema and a MotorSpec template.

    The schema is independent of the product-side Python implementation. It
    defines a richer MCP-friendly API vocabulary above a user-local backend:
    MotorSpec, DeckBundle, RunRequest, and RunResult.

    Args:
        motor_type: Optional motor family for the example template, such as
            "spm", "ipm", "induction", "srm", "synrm", or "hysteresis".

    Returns:
        Markdown schema plus a JSON MotorSpec template.
    """
    schema_text = format_python_api_schema(python_api_schema())
    template = build_motor_spec_template(motor_type)
    return (
        schema_text
        + "\n\n## MotorSpec Template\n"
        + "```json\n"
        + json.dumps(template, indent=2)
        + "\n```"
    )


@mcp.tool()
def elf_python_motor_spec_lint(spec_json: str = "", motor_type: str = "spm") -> str:
    """
    Lint a MotorSpec JSON object against the public Python facade schema.

    If `spec_json` is omitted, this lints the built-in template for `motor_type`.
    The lint is solver-free and does not require product Python or product DLLs.

    Args:
        spec_json: JSON object containing a MotorSpec-like dictionary.
        motor_type: Template motor family used when spec_json is omitted.

    Returns:
        Markdown lint report with PASS/FAIL and recommended observables.
    """
    if spec_json.strip():
        try:
            spec = json.loads(spec_json)
        except json.JSONDecodeError as exc:
            return (
                "# ELF Python MotorSpec Lint\n\n"
                "- status: `FAIL`\n"
                f"- issue: invalid JSON: {exc}"
            )
        if not isinstance(spec, dict):
            return "# ELF Python MotorSpec Lint\n\n- status: `FAIL`\n- issue: JSON root must be an object"
    else:
        spec = build_motor_spec_template(motor_type)
    return format_motor_spec_lint(validate_motor_spec_dict(spec))


@mcp.tool()
def elf_python_deck_lint(
    mai_path: str = "",
    mai_text: str = "",
    requested_observables: str = "",
) -> str:
    """
    Dry-run lint a public `.mai` deck or inline `.mai` text.

    This checks whether a deck has the expected MAGIC/PRE/SOL/DMEG markers and
    whether requested observables such as FLUM-based flux linkage or field
    probes have matching output blocks. It does not execute ELF/MAGIC.

    Args:
        mai_path: Public sample `.mai` path, e.g.
            `application/motor/pm_cosine_pickup_72/pm001/pm001.mai`.
        mai_text: Inline .mai text. Used when `mai_path` is omitted.
        requested_observables: Comma/space separated observable names such as
            `flux_linkage,back_emf_constant,torque`.

    Returns:
        Markdown PASS/FAIL/WARN deck lint report.
    """
    source = "inline"
    text = mai_text
    if mai_path.strip():
        path = mai_path.strip()
        if path.lower().endswith(".meg"):
            path = path[:-4] + ".mai"
        deck = get_sample_deck(path)
        if deck.get("error"):
            return (
                "# ELF Python Deck Lint\n\n"
                "- status: `FAIL`\n"
                f"- issue: {deck['error']}"
            )
        source = deck["path"]
        text = deck["text"]
    if not text.strip():
        return "# ELF Python Deck Lint\n\n- status: `FAIL`\n- issue: provide mai_path or mai_text"
    report = lint_mai_text(text, _parse_observables(requested_observables))
    return f"- source: `{source}`\n\n" + format_deck_lint(report)


@mcp.tool()
def elf_python_pm_demag_step_lint(
    mai_path: str = "",
    mai_text: str = "",
) -> str:
    """
    Dry-run lint an ELF/MAGIC PM demagnetization `.mai` deck.

    The lint checks the HBRM recoil definition and HBCN step-to-B-H-curve
    mapping for the standard 0/1/2 demagnetization workflow. It does not run
    MAGIC and does not read private solver outputs.

    Args:
        mai_path: Public sample `.mai` path. `.meg` is accepted and mapped to
            the sibling `.mai`.
        mai_text: Inline .mai text. Used when `mai_path` is omitted.

    Returns:
        Markdown PASS/FAIL/WARN report for the PM demagnetization step contract.
    """
    source = "inline"
    text = mai_text
    if mai_path.strip():
        path = mai_path.strip()
        if path.lower().endswith(".meg"):
            path = path[:-4] + ".mai"
        deck = get_sample_deck(path)
        if deck.get("error"):
            return (
                "# ELF Python PM Demag Step Lint\n\n"
                "- status: `FAIL`\n"
                f"- issue: {deck['error']}"
            )
        source = deck["path"]
        text = deck["text"]
    if not text.strip():
        return "# ELF Python PM Demag Step Lint\n\n- status: `FAIL`\n- issue: provide mai_path or mai_text"
    report = lint_pm_demag_step_contract(text)
    return f"- source: `{source}`\n\n" + format_pm_demag_step_lint(report)


@mcp.tool()
def elf_python_run_contract(
    goal: str,
    motor_type: str = "spm",
    source_public_deck_path: str = "",
    requested_observables: str = "",
) -> str:
    """
    Build a public RunRequest contract for a user-local ELF/MAGIC backend.

    This is the contract that a local runner should accept after MCP routing
    has chosen a deck family. It keeps raw product outputs local and does not
    call product Python or product DLLs from the public server.

    Args:
        goal: Natural-language analysis goal.
        motor_type: Motor family for the template.
        source_public_deck_path: Optional public `.mai` seed deck.
        requested_observables: Comma/space separated observables.

    Returns:
        Markdown RunRequest contract and backend requirements.
    """
    contract = build_run_request_contract(
        goal=goal,
        motor_type=motor_type,
        source_public_deck_path=source_public_deck_path,
        requested_observables=_parse_observables(requested_observables),
    )
    return format_run_request_contract(contract)


@mcp.tool()
def elf_python_run_result_parse(
    payload: str,
    case_id: str = "",
    motor_type: str = "spm",
    requested_observables: str = "",
) -> str:
    """
    Normalize a user-local RunResult payload into public-safe observables.

    The payload may be JSON with `parsed_observables`, a flat JSON object, or
    key-value text such as `torque_nm=0.8`. This tool does not read local files
    and does not publish raw product outputs; it only normalizes values pasted
    into the MCP call.

    Args:
        payload: JSON or key-value text from a local/private runner.
        case_id: Optional case id.
        motor_type: Motor family.
        requested_observables: Comma/space separated expected observables.

    Returns:
        Markdown parsed RunResult summary.
    """
    parsed = parse_run_result_payload(
        payload=payload,
        case_id=case_id,
        motor_type=motor_type,
        requested_observables=_parse_observables(requested_observables),
    )
    return format_run_result_parse(parsed)


@mcp.tool()
def elf_python_run_result_parse_path(
    run_path: str,
    motor_type: str = "spm",
    requested_observables: str = "",
    max_files: int = 20,
) -> str:
    """
    Parse completed user-local RunResult files or a run directory.

    This scans JSON/CSV/text-like result files, normalizes known observable
    names, and returns only parsed values plus file basenames. It intentionally
    does not return raw local paths or raw product output text.

    Args:
        run_path: User-local result file or directory path.
        motor_type: Motor family.
        requested_observables: Comma/space separated expected observables.
        max_files: Maximum result files to scan.

    Returns:
        Markdown parse summary with normalized observables and warnings.
    """
    parsed = parse_run_result_path(
        run_path=run_path,
        motor_type=motor_type,
        requested_observables=_parse_observables(requested_observables),
        max_files=max_files,
    )
    return format_run_result_path_parse(parsed)


@mcp.tool()
def elf_python_motor_design_plan(
    goal: str,
    motor_type: str = "",
    objective: str = "",
) -> str:
    """
    Plan motor design variables, studies, observables, and validation gates.

    This is the motor-design layer above MotorSpec. It tells an agent which
    variables to sweep, which observables to request, which studies are needed,
    and which validation gates must pass before making design claims.

    Args:
        goal: Natural-language motor design goal.
        motor_type: Optional motor family override.
        objective: Optional objective such as "torque_density",
            "back_emf_target", "efficiency_map", "ripple_reduction", or
            "material_reduction".

    Returns:
        Markdown motor design plan.
    """
    return format_motor_design_plan(
        build_motor_design_plan(goal=goal, motor_type=motor_type, objective=objective)
    )


@mcp.tool()
def elf_python_motor_sweep_matrix(
    motor_type: str = "spm",
    objective: str = "torque_density",
    budget: int = 9,
) -> str:
    """
    Build a deterministic public sweep/DOE matrix for motor design.

    The matrix is intentionally small and explicit so an LLM can create local
    RunRequests, parse RunResults, and rank candidates without inventing hidden
    parameters.

    Args:
        motor_type: Motor family such as "spm", "ipm", "induction", "srm",
            "synrm", or "hysteresis".
        objective: Design objective.
        budget: Number of rows, capped at 27.

    Returns:
        Markdown sweep matrix with active variables, rows, observables, and
        postprocess rules.
    """
    return format_motor_sweep_matrix(
        build_motor_sweep_matrix(motor_type=motor_type, objective=objective, budget=budget)
    )


@mcp.tool()
def elf_python_motor_dq_axis_map_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    current_limit_a_peak: float = 40.0,
    id_points: int = 5,
    iq_points: int = 5,
    ld_h: float | None = None,
    lq_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> str:
    """
    Build an Id/Iq map with PM and reluctance torque decomposition.

    This is the dq-axis design API. It creates explicit Id/Iq operating points,
    current-limit labels, PM torque proxy, reluctance torque proxy, total torque
    proxy, parser keys for flux_d/flux_q and Ld/Lq, and the quality gates
    needed before MTPA or saliency claims.

    Args:
        motor_type: Motor family, e.g. "ipm", "spm", "synrm", or "srm".
        pole_pairs: Pole-pair count.
        current_limit_a_peak: Peak current limit.
        id_points: Number of Id samples.
        iq_points: Number of Iq samples.
        ld_h: Optional Ld override in H.
        lq_h: Optional Lq override in H.
        pm_flux_wb: Optional PM flux override in Wb.

    Returns:
        Markdown Id/Iq map plan.
    """
    return format_motor_dq_axis_map_plan(
        build_motor_dq_axis_map_plan(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            current_limit_a_peak=current_limit_a_peak,
            id_points=id_points,
            iq_points=iq_points,
            ld_h=ld_h,
            lq_h=lq_h,
            pm_flux_wb=pm_flux_wb,
        )
    )


@mcp.tool()
def elf_python_motor_mtpa_search_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    current_limit_a_peak: float = 40.0,
    angle_min_deg: float = -80.0,
    angle_max_deg: float = 80.0,
    angle_points: int = 17,
    ld_h: float | None = None,
    lq_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> str:
    """
    Build an MTPA current-angle search plan from dq-axis torque terms.

    The plan scans current angle at fixed current magnitude and reports PM
    torque, reluctance torque, total torque, and torque-per-amp proxy. Local
    product runs still own the final confirmation.

    Args:
        motor_type: Motor family, e.g. "ipm", "spm", "synrm", or "srm".
        pole_pairs: Pole-pair count.
        current_limit_a_peak: Peak current magnitude.
        angle_min_deg: Minimum current angle from q-axis.
        angle_max_deg: Maximum current angle from q-axis.
        angle_points: Number of angle samples.
        ld_h: Optional Ld override in H.
        lq_h: Optional Lq override in H.
        pm_flux_wb: Optional PM flux override in Wb.

    Returns:
        Markdown MTPA search plan.
    """
    return format_motor_mtpa_search_plan(
        build_motor_mtpa_search_plan(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            current_limit_a_peak=current_limit_a_peak,
            angle_min_deg=angle_min_deg,
            angle_max_deg=angle_max_deg,
            angle_points=angle_points,
            ld_h=ld_h,
            lq_h=lq_h,
            pm_flux_wb=pm_flux_wb,
        )
    )


@mcp.tool()
def elf_python_reluctance_motor_design_plan(
    motor_type: str = "synrm",
    pole_pairs: int = 2,
    stator_slots: int = 36,
    rotor_topology: str = "flux_barrier",
    current_limit_a_peak: float = 40.0,
) -> str:
    """
    Build a reluctance-focused design plan for SynRM, PMa-SynRM, or SRM.

    This makes saliency and reluctance torque explicit: design variables,
    Ld/Lq extraction, Id/Iq map, MTPA-style current-angle scan, SynRM/PMa-SynRM
    flux-barrier planning, and SRM aligned/unaligned inductance checks.

    Args:
        motor_type: "synrm", "pm_assisted_synrm", "srm", "reluctance", or "switched".
        pole_pairs: Pole-pair count.
        stator_slots: Stator slot count.
        rotor_topology: Topology label such as "flux_barrier" or "salient_pole".
        current_limit_a_peak: Peak current limit.

    Returns:
        Markdown reluctance motor design plan.
    """
    return format_reluctance_motor_design_plan(
        build_reluctance_motor_design_plan(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            stator_slots=stator_slots,
            rotor_topology=rotor_topology,
            current_limit_a_peak=current_limit_a_peak,
        )
    )


@mcp.tool()
def elf_python_motor_winding_layout_plan(
    stator_slots: int = 48,
    pole_pairs: int = 4,
    phases: int = 3,
    layers: int = 2,
    coil_pitch_slots: int = 0,
) -> str:
    """
    Build a phase-belt winding layout and winding-factor proxy.

    This gives the design agent an explicit slot table, q value, slot
    electrical angle, coil pitch, and fundamental winding-factor proxy before
    it asks a local runner for back-EMF phase or torque-ripple claims.

    Args:
        stator_slots: Number of stator slots.
        pole_pairs: Number of pole pairs.
        phases: Number of phases, normally 3.
        layers: Slot layer count.
        coil_pitch_slots: Optional coil pitch. Use 0 for automatic pole pitch.

    Returns:
        Markdown winding layout plan.
    """
    pitch = None if coil_pitch_slots <= 0 else coil_pitch_slots
    return format_motor_winding_layout_plan(
        build_motor_winding_layout_plan(
            stator_slots=stator_slots,
            pole_pairs=pole_pairs,
            phases=phases,
            layers=layers,
            coil_pitch_slots=pitch,
        )
    )


@mcp.tool()
def elf_python_motor_topology_parameter_plan(
    motor_type: str = "spm",
    pole_pairs: int = 4,
    stator_slots: int = 48,
    rotor_topology: str = "outer_rotor",
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
) -> str:
    """
    Build topology-specific motor geometry variables and constraints.

    The plan exposes common dimensions plus SPM, IPM, PMa-SynRM, BLDC,
    line-start PM, deep-bar IM, flux-switching PM, Vernier PM,
    transverse-flux PM, slotless PM, claw-pole, commutator, SynRM, SRM, or
    induction variables with ranges and affected observables. It is a design
    contract, not a mesh or solver run.

    Args:
        motor_type: Motor family.
        pole_pairs: Number of pole pairs.
        stator_slots: Number of stator slots.
        rotor_topology: Rotor topology label such as "outer_rotor" or
            "inner_rotor".
        outer_diameter_mm: Motor outer diameter.
        stack_length_mm: Stack length.

    Returns:
        Markdown topology parameter plan.
    """
    return format_motor_topology_parameter_plan(
        build_motor_topology_parameter_plan(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            stator_slots=stator_slots,
            rotor_topology=rotor_topology,
            outer_diameter_mm=outer_diameter_mm,
            stack_length_mm=stack_length_mm,
        )
    )


@mcp.tool()
def elf_python_motor_demag_margin_plan(
    motor_type: str = "spm",
    temperature_c: float = 120.0,
    br_20c_t: float = 1.2,
    br_temp_coeff_pct_per_k: float = -0.11,
    hcj_ka_m: float = 900.0,
    hcj_temp_coeff_pct_per_k: float = -0.45,
    id_min_a_peak: float = -40.0,
    magnet_len_m: float = 0.004,
    gap_csv_m: str = "0.0005,0.001,0.002,0.004,0.008",
    iron_path_m: float = 0.08,
    iron_mu_r: float = 1000.0,
    mu_rec: float = 1.05,
) -> str:
    """
    Build a PM demagnetization margin screening contract.

    This public plan records hot Br, Hcj, negative d-axis current, required
    observables, sweep axes, and quality gates. It intentionally labels the
    result as a margin proxy until a local validated field result exists.

    Args:
        motor_type: Motor family.
        temperature_c: Magnet temperature for hot Br proxy.
        br_20c_t: Room-temperature remanence.
        br_temp_coeff_pct_per_k: Remanence temperature coefficient.
        hcj_ka_m: Coercivity reference.
        hcj_temp_coeff_pct_per_k: Coercivity temperature coefficient.
        id_min_a_peak: Worst negative d-axis current candidate.
        magnet_len_m: Magnet length along the load line.
        gap_csv_m: Comma-separated candidate gap lengths.
        iron_path_m: Effective iron path length.
        iron_mu_r: Effective iron relative permeability.
        mu_rec: Magnet recoil relative permeability.

    Returns:
        Markdown demagnetization margin plan.
    """
    gaps_m = tuple(float(item.strip()) for item in gap_csv_m.split(",") if item.strip())
    return format_motor_demag_margin_plan(
        build_motor_demag_margin_plan(
            motor_type=motor_type,
            temperature_c=temperature_c,
            br_20c_t=br_20c_t,
            br_temp_coeff_pct_per_k=br_temp_coeff_pct_per_k,
            hcj_ka_m=hcj_ka_m,
            hcj_temp_coeff_pct_per_k=hcj_temp_coeff_pct_per_k,
            id_min_a_peak=id_min_a_peak,
            magnet_len_m=magnet_len_m,
            gaps_m=gaps_m,
            iron_path_m=iron_path_m,
            iron_mu_r=iron_mu_r,
            mu_rec=mu_rec,
        )
    )


@mcp.tool()
def elf_python_motor_drive_cycle_plan(
    target_market: str = "robot_drone",
    rated_torque_nm: float = 0.6,
    peak_torque_nm: float = 1.2,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
) -> str:
    """
    Build weighted drive-cycle operating points for motor scoring.

    The output connects user-facing duty points to efficiency-map and
    multiphysics follow-up: cycle efficiency, weighted total loss, worst
    voltage/current margin, and thermal/NVH/stress worst-case points.

    Args:
        target_market: "robot_drone" or "industrial_servo".
        rated_torque_nm: Rated/continuous torque.
        peak_torque_nm: Peak torque.
        base_speed_rpm: Base speed.
        max_speed_rpm: Maximum speed.

    Returns:
        Markdown drive-cycle plan.
    """
    return format_motor_drive_cycle_plan(
        build_motor_drive_cycle_plan(
            target_market=target_market,
            rated_torque_nm=rated_torque_nm,
            peak_torque_nm=peak_torque_nm,
            base_speed_rpm=base_speed_rpm,
            max_speed_rpm=max_speed_rpm,
        )
    )


@mcp.tool()
def elf_python_motor_optimization_study_plan(
    motor_type: str = "spm",
    objective: str = "cycle_efficiency",
    budget: int = 48,
    target_market: str = "robot_drone",
) -> str:
    """
    Build a constrained motor optimization study plan.

    The plan selects variables from the motor and topology contracts, attaches
    constraints, defines ranking outputs, and requires validation promotion for
    finalists. It is a public optimization contract, not a hidden optimizer run.

    Args:
        motor_type: Motor family.
        objective: Objective such as "cycle_efficiency" or "torque_density".
        budget: Candidate/run budget.
        target_market: Target-market label for ranking context.

    Returns:
        Markdown optimization study plan.
    """
    return format_motor_optimization_study_plan(
        build_motor_optimization_study_plan(
            motor_type=motor_type,
            objective=objective,
            budget=budget,
            target_market=target_market,
        )
    )


@mcp.tool()
def elf_python_motor_optimization_loop(
    motor_type: str = "spm",
    objective: str = "torque_density",
    result_payloads_json: str = "",
    budget: int = 9,
    target_back_emf: float = 0.0,
) -> str:
    """
    Rank parsed RunResults and propose the next optimization-loop actions.

    Args:
        motor_type: Motor family.
        objective: Objective such as "torque_density", "cycle_efficiency",
            or "back_emf_target".
        result_payloads_json: JSON list of local RunResult payloads, a single
            JSON object, or text chunks separated by `---`.
        budget: Candidate/run budget.
        target_back_emf: Optional target back-EMF constant for target matching.

    Returns:
        Markdown candidate ranking and next-run rows.
    """
    loop = build_motor_optimization_loop(
        motor_type=motor_type,
        objective=objective,
        result_payloads=result_payloads_json,
        budget=budget,
        target_back_emf=target_back_emf,
    )
    return format_motor_optimization_loop(loop)


@mcp.tool()
def elf_python_motor_voltage_field_weakening_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    dc_bus_v: float = 48.0,
    current_limit_a_peak: float = 40.0,
    speed_min_rpm: float = 500.0,
    speed_max_rpm: float = 12000.0,
    speed_points: int = 7,
    ld_h: float | None = None,
    lq_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> str:
    """
    Build a voltage-limit and field-weakening design plan.

    This creates speed rows with back-EMF voltage proxy, q-axis reactance
    proxy, voltage margin, and required negative-Id proxy. Final field
    weakening decisions still require local electromagnetic results plus demag
    and thermal validation.

    Args:
        motor_type: Motor family.
        pole_pairs: Pole-pair count.
        dc_bus_v: DC bus voltage.
        current_limit_a_peak: Peak current limit.
        speed_min_rpm: Minimum speed row.
        speed_max_rpm: Maximum speed row.
        speed_points: Number of speed rows.
        ld_h: Optional Ld override.
        lq_h: Optional Lq override.
        pm_flux_wb: Optional PM flux override.

    Returns:
        Markdown voltage/field-weakening plan.
    """
    return format_motor_voltage_field_weakening_plan(
        build_motor_voltage_field_weakening_plan(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            dc_bus_v=dc_bus_v,
            current_limit_a_peak=current_limit_a_peak,
            speed_min_rpm=speed_min_rpm,
            speed_max_rpm=speed_max_rpm,
            speed_points=speed_points,
            ld_h=ld_h,
            lq_h=lq_h,
            pm_flux_wb=pm_flux_wb,
        )
    )


@mcp.tool()
def elf_python_motor_cogging_ripple_plan(
    motor_type: str = "spm",
    stator_slots: int = 48,
    pole_pairs: int = 4,
    magnet_arc_fraction: float = 0.75,
    skew_fraction: float = 0.0,
) -> str:
    """
    Build a cogging torque and torque-ripple reduction plan.

    Args:
        motor_type: Motor family.
        stator_slots: Stator slot count.
        pole_pairs: Pole-pair count.
        magnet_arc_fraction: Surface or effective PM arc fraction.
        skew_fraction: Skew as slot-pitch fraction.

    Returns:
        Markdown cogging/ripple plan.
    """
    return format_motor_cogging_ripple_plan(
        build_motor_cogging_ripple_plan(
            motor_type=motor_type,
            stator_slots=stator_slots,
            pole_pairs=pole_pairs,
            magnet_arc_fraction=magnet_arc_fraction,
            skew_fraction=skew_fraction,
        )
    )


@mcp.tool()
def elf_python_motor_airgap_harmonics_nvh_plan(
    motor_type: str = "spm",
    stator_slots: int = 48,
    pole_pairs: int = 4,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
) -> str:
    """
    Build air-gap harmonic force-order routing for NVH validation.

    Args:
        motor_type: Motor family.
        stator_slots: Stator slot count.
        pole_pairs: Pole-pair count.
        base_speed_rpm: Base speed.
        max_speed_rpm: Maximum speed.

    Returns:
        Markdown air-gap harmonic/NVH plan.
    """
    return format_motor_airgap_harmonics_nvh_plan(
        build_motor_airgap_harmonics_nvh_plan(
            motor_type=motor_type,
            stator_slots=stator_slots,
            pole_pairs=pole_pairs,
            base_speed_rpm=base_speed_rpm,
            max_speed_rpm=max_speed_rpm,
        )
    )


@mcp.tool()
def elf_python_motor_thermal_network_plan(
    target_market: str = "robot_drone",
    total_loss_w: float = 25.0,
    ambient_c: float = 25.0,
    cooling_h_w_m2k: float = 35.0,
) -> str:
    """
    Build a reduced thermal network before open thermal validation.

    Args:
        target_market: Target-market label.
        total_loss_w: Total loss estimate.
        ambient_c: Ambient temperature.
        cooling_h_w_m2k: Cooling coefficient proxy.

    Returns:
        Markdown thermal-network plan.
    """
    return format_motor_thermal_network_plan(
        build_motor_thermal_network_plan(
            target_market=target_market,
            total_loss_w=total_loss_w,
            ambient_c=ambient_c,
            cooling_h_w_m2k=cooling_h_w_m2k,
        )
    )


@mcp.tool()
def elf_python_motor_manufacturing_tolerance_plan(
    motor_type: str = "spm",
    airgap_mm: float = 0.8,
    production_intent: str = "prototype_small_lot",
) -> str:
    """
    Build a manufacturing tolerance and robustness DOE plan.

    Args:
        motor_type: Motor family.
        airgap_mm: Nominal air gap.
        production_intent: "concept", "prototype_small_lot", or
            "mass_production".

    Returns:
        Markdown tolerance plan.
    """
    return format_motor_manufacturing_tolerance_plan(
        build_motor_manufacturing_tolerance_plan(
            motor_type=motor_type,
            airgap_mm=airgap_mm,
            production_intent=production_intent,
        )
    )


@mcp.tool()
def elf_python_motor_material_variation_plan(
    motor_type: str = "spm",
    focus: str = "all",
) -> str:
    """
    Build a motor material sensitivity plan.

    Args:
        motor_type: Motor family.
        focus: "all", "magnet", "electrical_steel", or "conductor".

    Returns:
        Markdown material variation plan.
    """
    return format_motor_material_variation_plan(
        build_motor_material_variation_plan(motor_type=motor_type, focus=focus)
    )


@mcp.tool()
def elf_python_motor_feasibility_study(
    goal: str,
    target_market: str = "robot_drone",
    motor_type: str = "spm",
    production_intent: str = "prototype_small_lot",
) -> str:
    """
    Build a feasibility gate for prototype or small-lot motor work.

    Args:
        goal: Motor design goal.
        target_market: Target-market label.
        motor_type: Motor family.
        production_intent: "concept", "prototype_small_lot", or
            "mass_production".

    Returns:
        Markdown feasibility study gate.
    """
    return format_motor_feasibility_study(
        build_motor_feasibility_study(
            goal=goal,
            target_market=target_market,
            motor_type=motor_type,
            production_intent=production_intent,
        )
    )


@mcp.tool()
def elf_python_motor_efficiency_map_plan(
    motor_type: str = "spm",
    torque_min_nm: float = 0.05,
    torque_max_nm: float = 1.0,
    torque_points: int = 5,
    speed_min_rpm: float = 500.0,
    speed_max_rpm: float = 12000.0,
    speed_points: int = 6,
    base_speed_rpm: float = 3500.0,
    dc_bus_v: float = 48.0,
    phase_current_limit_a_peak: float = 40.0,
    min_filled_fraction: float = 1.0,
    max_abs_torque_error_nm: float = 0.05,
) -> str:
    """
    Build a motor efficiency-map operating grid and postprocess contract.

    This is the motor-design API entry point for efficiency maps. It defines
    torque/speed axes, operating points, feasibility labels from a torque-speed
    envelope, required local-run observables, loss-model terms, and output
    grids such as eta, total loss, voltage margin, and current margin.

    Args:
        motor_type: Motor family, e.g. "spm", "ipm", "induction", "synrm".
        torque_min_nm: Minimum torque axis value.
        torque_max_nm: Maximum torque axis value.
        torque_points: Number of torque samples.
        speed_min_rpm: Minimum speed axis value.
        speed_max_rpm: Maximum speed axis value.
        speed_points: Number of speed samples.
        base_speed_rpm: Base speed for field-weakening labels.
        dc_bus_v: DC bus voltage.
        phase_current_limit_a_peak: Phase current limit.

    Returns:
        Markdown efficiency-map plan with operating points and quality gates.
    """
    return format_motor_efficiency_map_plan(
        build_motor_efficiency_map_plan(
            motor_type=motor_type,
            torque_min_nm=torque_min_nm,
            torque_max_nm=torque_max_nm,
            torque_points=torque_points,
            speed_min_rpm=speed_min_rpm,
            speed_max_rpm=speed_max_rpm,
            speed_points=speed_points,
            base_speed_rpm=base_speed_rpm,
            dc_bus_v=dc_bus_v,
            phase_current_limit_a_peak=phase_current_limit_a_peak,
        )
    )


@mcp.tool()
def elf_python_motor_efficiency_map_from_results(
    motor_type: str = "spm",
    result_payloads_json: str = "",
    torque_min_nm: float = 0.05,
    torque_max_nm: float = 1.0,
    torque_points: int = 5,
    speed_min_rpm: float = 500.0,
    speed_max_rpm: float = 12000.0,
    speed_points: int = 6,
    base_speed_rpm: float = 3500.0,
    dc_bus_v: float = 48.0,
    phase_current_limit_a_peak: float = 40.0,
    min_filled_fraction: float = 1.0,
    max_abs_torque_error_nm: float = 0.05,
) -> str:
    """
    Build a numeric efficiency-map grid from parsed local RunResults.

    The input may be a JSON list of RunResult payloads, a single RunResult
    object, or the JSON returned by `elf_python_run_result_parse_path`. The
    tool computes eta, total loss, torque error, best point, and coverage
    labels without exposing raw local output text.

    Args:
        motor_type: Motor family.
        result_payloads_json: JSON list/object of local RunResult payloads.
        torque_min_nm: Minimum torque axis value.
        torque_max_nm: Maximum torque axis value.
        torque_points: Number of torque samples.
        speed_min_rpm: Minimum speed axis value.
        speed_max_rpm: Maximum speed axis value.
        speed_points: Number of speed samples.
        base_speed_rpm: Base speed for field-weakening labels.
        dc_bus_v: DC bus voltage.
        phase_current_limit_a_peak: Phase current limit.
        min_filled_fraction: Minimum filled-cell fraction for PASS coverage.
        max_abs_torque_error_nm: Maximum absolute torque error for PASS.

    Returns:
        Markdown numeric efficiency map with eta grid and best point.
    """
    return format_motor_efficiency_map_result(
        build_motor_efficiency_map_from_results(
            motor_type=motor_type,
            result_payloads=result_payloads_json,
            torque_min_nm=torque_min_nm,
            torque_max_nm=torque_max_nm,
            torque_points=torque_points,
            speed_min_rpm=speed_min_rpm,
            speed_max_rpm=speed_max_rpm,
            speed_points=speed_points,
            base_speed_rpm=base_speed_rpm,
            dc_bus_v=dc_bus_v,
            phase_current_limit_a_peak=phase_current_limit_a_peak,
            min_filled_fraction=min_filled_fraction,
            max_abs_torque_error_nm=max_abs_torque_error_nm,
        )
    )


@mcp.tool()
def elf_python_motor_operating_point_run_queue(
    motor_type: str = "spm",
    objective: str = "efficiency_map",
    torque_min_nm: float = 0.05,
    torque_max_nm: float = 1.0,
    torque_points: int = 4,
    speed_min_rpm: float = 500.0,
    speed_max_rpm: float = 12000.0,
    speed_points: int = 5,
    max_rows: int = 20,
) -> str:
    """
    Build concrete local-run operating rows from map axes.

    Args:
        motor_type: Motor family.
        objective: Objective label attached to each run row.
        torque_min_nm: Minimum torque axis value.
        torque_max_nm: Maximum torque axis value.
        torque_points: Number of torque samples.
        speed_min_rpm: Minimum speed axis value.
        speed_max_rpm: Maximum speed axis value.
        speed_points: Number of speed samples.
        max_rows: Maximum rows to emit.

    Returns:
        Markdown local-run queue contract.
    """
    return format_motor_operating_point_run_queue(
        build_motor_operating_point_run_queue(
            motor_type=motor_type,
            objective=objective,
            torque_min_nm=torque_min_nm,
            torque_max_nm=torque_max_nm,
            torque_points=torque_points,
            speed_min_rpm=speed_min_rpm,
            speed_max_rpm=speed_max_rpm,
            speed_points=speed_points,
            max_rows=max_rows,
        )
    )


@mcp.tool()
def elf_python_motor_inverter_pwm_harmonic_plan(
    motor_type: str = "spm",
    modulation: str = "svpwm",
    switching_frequency_hz: float = 20000.0,
    fundamental_frequency_hz: float = 400.0,
    dc_bus_v: float = 48.0,
    phase_current_a_rms: float = 10.0,
    max_sideband_order: int = 3,
) -> str:
    """
    Plan inverter/PWM harmonic rows for loss and ripple screening.

    Args:
        motor_type: Motor family.
        modulation: Modulation label, such as "svpwm" or "sine_pwm".
        switching_frequency_hz: PWM switching frequency.
        fundamental_frequency_hz: Electrical fundamental frequency.
        dc_bus_v: DC bus voltage.
        phase_current_a_rms: Phase current RMS.
        max_sideband_order: Number of switching sideband offsets to include.

    Returns:
        Markdown PWM harmonic plan.
    """
    return format_motor_inverter_pwm_harmonic_plan(
        build_motor_inverter_pwm_harmonic_plan(
            motor_type=motor_type,
            modulation=modulation,
            switching_frequency_hz=switching_frequency_hz,
            fundamental_frequency_hz=fundamental_frequency_hz,
            dc_bus_v=dc_bus_v,
            phase_current_a_rms=phase_current_a_rms,
            max_sideband_order=max_sideband_order,
        )
    )


@mcp.tool()
def elf_python_motor_saturation_inductance_map_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    current_limit_a_peak: float = 60.0,
    current_points: int = 4,
    angle_points: int = 7,
    ld_unsat_h: float | None = None,
    lq_unsat_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> str:
    """
    Build a saturated Ld/Lq map plan over current magnitude and angle.

    Args:
        motor_type: Motor family.
        pole_pairs: Pole-pair count.
        current_limit_a_peak: Peak current limit.
        current_points: Number of current-amplitude rows.
        angle_points: Number of current-angle rows.
        ld_unsat_h: Optional unsaturated Ld reference.
        lq_unsat_h: Optional unsaturated Lq reference.
        pm_flux_wb: Optional PM flux reference.

    Returns:
        Markdown saturation inductance map plan.
    """
    return format_motor_saturation_inductance_map_plan(
        build_motor_saturation_inductance_map_plan(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            current_limit_a_peak=current_limit_a_peak,
            current_points=current_points,
            angle_points=angle_points,
            ld_unsat_h=ld_unsat_h,
            lq_unsat_h=lq_unsat_h,
            pm_flux_wb=pm_flux_wb,
        )
    )


@mcp.tool()
def elf_python_motor_loss_model_contract(
    motor_type: str = "spm",
    include_inverter: bool = True,
) -> str:
    """
    Define loss terms and parser keys for motor efficiency-map postprocessing.

    The contract separates field-solver loss proxies from copper, iron, magnet,
    rotor, mechanical, and optional inverter losses so an agent does not hide
    assumptions inside a single efficiency number.

    Args:
        motor_type: Motor family.
        include_inverter: Include inverter loss terms in the contract.

    Returns:
        Markdown loss-model contract.
    """
    return format_motor_loss_model_contract(
        build_motor_loss_model_contract(motor_type=motor_type, include_inverter=include_inverter)
    )


@mcp.tool()
def elf_python_motor_torque_speed_envelope(
    motor_type: str = "spm",
    peak_torque_nm: float = 1.0,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
    dc_bus_v: float = 48.0,
    phase_current_limit_a_peak: float = 40.0,
    speed_points: int = 9,
) -> str:
    """
    Build a torque-speed envelope for clipping efficiency-map points.

    Args:
        motor_type: Motor family.
        peak_torque_nm: Peak torque at and below base speed.
        base_speed_rpm: Base speed for constant-power transition.
        max_speed_rpm: Maximum speed.
        dc_bus_v: DC bus voltage.
        phase_current_limit_a_peak: Phase current limit.
        speed_points: Number of envelope rows.

    Returns:
        Markdown torque-speed envelope.
    """
    return format_motor_torque_speed_envelope(
        build_motor_torque_speed_envelope(
            motor_type=motor_type,
            peak_torque_nm=peak_torque_nm,
            base_speed_rpm=base_speed_rpm,
            max_speed_rpm=max_speed_rpm,
            dc_bus_v=dc_bus_v,
            phase_current_limit_a_peak=phase_current_limit_a_peak,
            speed_points=speed_points,
        )
    )


@mcp.tool()
def elf_python_induction_slip_sweep_plan(
    pole_pairs: int = 2,
    supply_frequency_hz: float = 50.0,
    slip_min: float = 0.005,
    slip_max: float = 0.20,
    slip_points: int = 9,
    phase_current_limit_a_peak: float = 40.0,
    dc_bus_v: float = 200.0,
) -> str:
    """
    Build an induction-motor slip sweep for torque/loss/efficiency studies.

    This makes slip explicit instead of hiding it behind a generic speed axis:
    synchronous speed, rotor speed, slip frequency, rotor copper loss relation,
    and breakdown-region bracketing are all part of the contract.

    Args:
        pole_pairs: Motor pole-pair count.
        supply_frequency_hz: Stator electrical supply frequency.
        slip_min: Minimum motoring slip.
        slip_max: Maximum motoring slip.
        slip_points: Number of slip samples.
        phase_current_limit_a_peak: Phase current limit.
        dc_bus_v: DC bus voltage.

    Returns:
        Markdown induction-motor slip sweep plan.
    """
    return format_induction_motor_slip_sweep_plan(
        build_induction_motor_slip_sweep_plan(
            pole_pairs=pole_pairs,
            supply_frequency_hz=supply_frequency_hz,
            slip_min=slip_min,
            slip_max=slip_max,
            slip_points=slip_points,
            phase_current_limit_a_peak=phase_current_limit_a_peak,
            dc_bus_v=dc_bus_v,
        )
    )


@mcp.tool()
def elf_python_motor_observable_contract(
    motor_type: str = "spm",
    study: str = "static_flux_linkage",
) -> str:
    """
    Map a motor study to ELF output markers, parser keys, and validation checks.

    This tells a local backend/parser what to extract from a product run and
    tells the LLM which physics checks to apply before interpreting a result.

    Args:
        motor_type: Motor family.
        study: Study type such as "back_emf_speed_sweep",
            "static_torque_angle", "dq_inductance", "force_gap_sweep",
            "induction_slip_loss", or "ac_loss_frequency_sweep".

    Returns:
        Markdown observable contract.
    """
    return format_motor_observable_contract(
        build_motor_observable_contract(motor_type=motor_type, study=study)
    )


@mcp.tool()
def elf_python_motor_market_brief(
    target_market: str = "robot_drone",
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
) -> str:
    """
    Build a market/application brief for motor design agents.

    This captures the robotics/drone style workflow where an end user provides
    specifications, the agent produces designs and handoffs, and the user does
    not need to operate analysis software directly.

    Args:
        target_market: "robot_drone" or "industrial_servo".
        motor_type: Motor family, usually "spm" for robot/drone PMSM work.
        rotor_topology: "outer_rotor" or "inner_rotor" for SPM/PMSM.

    Returns:
        Markdown market brief with spec fields, priorities, topology choices,
        first calls, and GUI-free user experience policy.
    """
    return format_motor_market_brief(
        build_motor_market_brief(
            target_market=target_market,
            motor_type=motor_type,
            rotor_topology=rotor_topology,
        )
    )


@mcp.tool()
def elf_python_motor_design_agent_handoff(
    goal: str,
    target_market: str = "robot_drone",
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    continuous_torque_nm: float = 0.0,
    base_speed_rpm: float = 0.0,
    dc_bus_v: float = 0.0,
    outer_diameter_mm: float = 0.0,
    stack_length_mm: float = 0.0,
    cooling_mode: str = "natural_air",
) -> str:
    """
    Build a spec-to-design-agent handoff for motor workflows.

    The handoff turns user specs into a design-agent contract: market brief,
    design plan, `.meg` generation route, sweep matrix, observable contract,
    analysis routing, required NGSolve NVH/thermal/stress validation planning,
    and manufacturing/prototype deliverables. It does not run licensed software.

    Args:
        goal: User design goal, e.g. "outer-rotor drone SPM motor".
        target_market: "robot_drone" or "industrial_servo".
        motor_type: Motor family.
        rotor_topology: "outer_rotor" or "inner_rotor".
        continuous_torque_nm: Optional continuous torque target.
        base_speed_rpm: Optional base speed target.
        dc_bus_v: Optional DC bus voltage.
        outer_diameter_mm: Optional outer diameter target.
        stack_length_mm: Optional stack length target.
        cooling_mode: Cooling mode text.

    Returns:
        Markdown handoff for a GUI-free design-agent workflow.
    """
    return format_motor_design_agent_handoff(
        build_motor_design_agent_handoff(
            goal=goal,
            target_market=target_market,
            motor_type=motor_type,
            rotor_topology=rotor_topology,
            continuous_torque_nm=continuous_torque_nm,
            base_speed_rpm=base_speed_rpm,
            dc_bus_v=dc_bus_v,
            outer_diameter_mm=outer_diameter_mm,
            stack_length_mm=stack_length_mm,
            cooling_mode=cooling_mode,
        )
    )


@mcp.tool()
def elf_python_motor_ngsolve_result_crosscheck(
    run_result_payload: str = "{}",
    ngsolve_result_payload: str = "{}",
    thermal_limit_c: float = 155.0,
    min_nvh_separation: float = 0.15,
    min_stress_margin: float = 1.5,
) -> str:
    """
    Cross-check normalized RunResult observables against NGSolve runtime JSON.

    Args:
        run_result_payload: Local RunResult JSON/text payload.
        ngsolve_result_payload: JSON printed by `elf_python_ngsolve_validation_script`.
        thermal_limit_c: Thermal lane peak-temperature limit.
        min_nvh_separation: Minimum relative order/modal separation.
        min_stress_margin: Minimum stress yield-margin proxy.

    Returns:
        Markdown crosscheck summary with PASS/WARN/FAIL lane labels.
    """
    crosscheck = build_motor_ngsolve_result_crosscheck(
        run_result_payload=run_result_payload,
        ngsolve_result_payload=ngsolve_result_payload,
        thermal_limit_c=thermal_limit_c,
        min_nvh_separation=min_nvh_separation,
        min_stress_margin=min_stress_margin,
    )
    return format_motor_ngsolve_result_crosscheck(crosscheck)


@mcp.tool()
def elf_python_motor_drawing_bom_handoff(
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    stator_slots: int = 48,
    pole_pairs: int = 4,
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
    validation_label: str = "needs_local_run",
    run_result_payload: str = "",
) -> str:
    """
    Build a public-safe drawing and BOM handoff for a motor prototype.

    Args:
        motor_type: Motor family.
        rotor_topology: Rotor topology label.
        stator_slots: Stator slot count.
        pole_pairs: Pole-pair count.
        outer_diameter_mm: Outer diameter.
        stack_length_mm: Stack length.
        validation_label: Current validation label.
        run_result_payload: Optional local RunResult JSON/text payload to
            summarize without exposing raw output files.

    Returns:
        Markdown drawing/BOM handoff.
    """
    handoff = build_motor_drawing_bom_handoff(
        motor_type=motor_type,
        rotor_topology=rotor_topology,
        stator_slots=stator_slots,
        pole_pairs=pole_pairs,
        outer_diameter_mm=outer_diameter_mm,
        stack_length_mm=stack_length_mm,
        validation_label=validation_label,
        run_result_payload=run_result_payload,
    )
    return format_motor_drawing_bom_handoff(handoff)


@mcp.tool()
def elf_python_motor_rotor_stress_retention_plan(
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    max_speed_rpm: float = 12000.0,
    rotor_outer_radius_mm: float = 36.0,
    bridge_thickness_mm: float = 1.0,
    sleeve_thickness_mm: float = 0.0,
    rotor_density_kg_m3: float = 7800.0,
    yield_strength_mpa: float = 450.0,
) -> str:
    """
    Build high-speed rotor stress and retention screening gates.

    Args:
        motor_type: Motor family.
        rotor_topology: Rotor topology label.
        max_speed_rpm: Maximum mechanical speed.
        rotor_outer_radius_mm: Rotor outer radius.
        bridge_thickness_mm: Minimum bridge or retention path thickness.
        sleeve_thickness_mm: Sleeve thickness, if any.
        rotor_density_kg_m3: Rotor density proxy.
        yield_strength_mpa: Material yield strength reference.

    Returns:
        Markdown rotor stress / retention plan.
    """
    return format_motor_rotor_stress_retention_plan(
        build_motor_rotor_stress_retention_plan(
            motor_type=motor_type,
            rotor_topology=rotor_topology,
            max_speed_rpm=max_speed_rpm,
            rotor_outer_radius_mm=rotor_outer_radius_mm,
            bridge_thickness_mm=bridge_thickness_mm,
            sleeve_thickness_mm=sleeve_thickness_mm,
            rotor_density_kg_m3=rotor_density_kg_m3,
            yield_strength_mpa=yield_strength_mpa,
        )
    )


@mcp.tool()
def elf_python_motor_validation_scorecard(
    run_result_payload: str = "{}",
    ngsolve_result_payload: str = "{}",
    required_observables: str = "torque,loss_proxy,efficiency",
    drawing_bom_payload: str = "",
) -> str:
    """
    Build one promotion scorecard from RunResult, NGSolve lanes, and handoff labels.

    Args:
        run_result_payload: Local RunResult JSON/text payload.
        ngsolve_result_payload: NGSolve runtime JSON payload.
        required_observables: Comma-separated observables required for the claim.
        drawing_bom_payload: Optional drawing/BOM handoff JSON-like payload.

    Returns:
        Markdown validation scorecard.
    """
    required = [
        item.strip()
        for item in required_observables.split(",")
        if item.strip()
    ]
    return format_motor_validation_scorecard(
        build_motor_validation_scorecard(
            run_result_payload=run_result_payload,
            ngsolve_result_payload=ngsolve_result_payload,
            required_observables=required,
            drawing_bom_payload=drawing_bom_payload,
        )
    )


@mcp.tool()
def elf_python_ngsolve_validation_plan(
    goal: str,
    lanes: str = "all",
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    total_loss_w: float = 25.0,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
    cooling_h_w_m2k: float = 35.0,
    thermal_conductivity_w_mk: float = 12.0,
    torque_ripple_percent: float = 5.0,
    cogging_torque_nm: float = 0.02,
    force_order: float = 12.0,
    yield_strength_mpa: float = 450.0,
) -> str:
    """
    Build required NGSolve multiphysics validation jobs for a motor design.

    This is an implementation layer, not only a routing label. It validates
    the numeric inputs needed for thermal, NVH, and mechanical stress checks
    and returns concrete NGSolve lane jobs plus script-generation calls.

    Args:
        goal: Motor validation goal.
        lanes: "all", "thermal", "nvh", "stress", or comma-separated lanes.
        motor_type: Motor family.
        rotor_topology: Rotor topology label.
        total_loss_w: Loss input for thermal validation.
        base_speed_rpm: Operating speed for NVH order frequency.
        max_speed_rpm: Maximum speed for stress validation.
        outer_diameter_mm: Motor outer diameter.
        stack_length_mm: Stack length.
        cooling_h_w_m2k: Convective cooling coefficient.
        thermal_conductivity_w_mk: Effective thermal conductivity.
        torque_ripple_percent: Torque ripple for NVH validation.
        cogging_torque_nm: Cogging torque for NVH validation.
        force_order: Electromagnetic force/torque order.
        yield_strength_mpa: Stress margin reference.

    Returns:
        Markdown NGSolve validation plan with lint status and lane jobs.
    """
    spec = build_ngsolve_validation_spec(
        goal=goal,
        lanes=lanes,
        motor_type=motor_type,
        rotor_topology=rotor_topology,
        total_loss_w=total_loss_w,
        base_speed_rpm=base_speed_rpm,
        max_speed_rpm=max_speed_rpm,
        outer_diameter_mm=outer_diameter_mm,
        stack_length_mm=stack_length_mm,
        cooling_h_w_m2k=cooling_h_w_m2k,
        thermal_conductivity_w_mk=thermal_conductivity_w_mk,
        torque_ripple_percent=torque_ripple_percent,
        cogging_torque_nm=cogging_torque_nm,
        force_order=force_order,
        yield_strength_mpa=yield_strength_mpa,
    )
    return format_ngsolve_validation_plan(build_ngsolve_validation_plan(spec))


@mcp.tool()
def elf_python_ngsolve_validation_script(
    goal: str,
    lane: str = "all",
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    total_loss_w: float = 25.0,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
    cooling_h_w_m2k: float = 35.0,
    thermal_conductivity_w_mk: float = 12.0,
    torque_ripple_percent: float = 5.0,
    cogging_torque_nm: float = 0.02,
    force_order: float = 12.0,
    yield_strength_mpa: float = 450.0,
) -> str:
    """
    Generate a runnable NGSolve Python script for motor multiphysics validation.

    The generated script implements three open validation lanes:
    scalar heat conduction with Robin cooling, structural/acoustic modal NVH
    proxy, and linear-elastic rotor stress proxy. It uses NGSolve/Netgen only
    and does not execute ELF/MAGIC or product DLLs.

    Args:
        goal: Motor validation goal.
        lane: "all", "thermal", "nvh", or "stress".
        motor_type: Motor family.
        rotor_topology: Rotor topology label.
        total_loss_w: Loss input for thermal validation.
        base_speed_rpm: Operating speed for NVH order frequency.
        max_speed_rpm: Maximum speed for stress validation.
        outer_diameter_mm: Motor outer diameter.
        stack_length_mm: Stack length.
        cooling_h_w_m2k: Convective cooling coefficient.
        thermal_conductivity_w_mk: Effective thermal conductivity.
        torque_ripple_percent: Torque ripple for NVH validation.
        cogging_torque_nm: Cogging torque for NVH validation.
        force_order: Electromagnetic force/torque order.
        yield_strength_mpa: Stress margin reference.

    Returns:
        Markdown containing a Python code fence with the runnable NGSolve script.
    """
    spec = build_ngsolve_validation_spec(
        goal=goal,
        lanes=lane,
        motor_type=motor_type,
        rotor_topology=rotor_topology,
        total_loss_w=total_loss_w,
        base_speed_rpm=base_speed_rpm,
        max_speed_rpm=max_speed_rpm,
        outer_diameter_mm=outer_diameter_mm,
        stack_length_mm=stack_length_mm,
        cooling_h_w_m2k=cooling_h_w_m2k,
        thermal_conductivity_w_mk=thermal_conductivity_w_mk,
        torque_ripple_percent=torque_ripple_percent,
        cogging_torque_nm=cogging_torque_nm,
        force_order=force_order,
        yield_strength_mpa=yield_strength_mpa,
    )
    return format_ngsolve_validation_script(build_ngsolve_validation_script(spec, lane=lane))


@mcp.tool()
def elf_python_meg_generation_plan(
    goal: str,
    dimension: str = "auto",
    geometry_complexity: str = "auto",
) -> str:
    """
    Plan a public-safe `.meg` generation backend for a Python/MCP workflow.

    Recommended paths include Cubit mesh export for 3D or CAD-like geometry,
    Netgen for deterministic 2D motor cross-sections, and constrained LLM 2D
    templates for simple educational/prototyping decks. This tool only plans;
    it does not run a mesher or solver.

    Args:
        goal: Natural-language geometry/deck generation goal.
        dimension: "auto", "2d", or "3d".
        geometry_complexity: "auto", "simple", "template", "low", or "high".

    Returns:
        Markdown generation plan with backend strategy and validation gates.
    """
    return format_meg_generation_plan(
        build_meg_generation_plan(
            goal=goal,
            dimension=dimension,
            geometry_complexity=geometry_complexity,
        )
    )


@mcp.tool()
def elf_python_2d_motor_template(
    motor_type: str = "spm",
    pole_pairs: int = 4,
    stator_slots: int = 48,
) -> str:
    """
    Build a constrained 2D motor template for LLM-assisted MEG drafting.

    This gives an agent a bounded 2D cross-section schema: radial layers,
    angular features, material roles, requested observables, and hard validation
    rules. The intended path is LLM draft -> deterministic Netgen 2D remesh ->
    `.mai/.meg` lint -> physics validation. This tool does not generate a mesh
    file or execute ELF/MAGIC.

    Args:
        motor_type: "spm", "ipm", "induction", "srm", "synrm",
            "hysteresis", etc.
        pole_pairs: Number of pole pairs.
        stator_slots: Number of stator slots.

    Returns:
        Markdown plus JSON constrained 2D template.
    """
    return format_2d_motor_template(
        build_2d_motor_template(
            motor_type=motor_type,
            pole_pairs=pole_pairs,
            stator_slots=stator_slots,
        )
    )


@mcp.tool()
def elf_recipe_index(tag: str = "", solver: str = "") -> str:
    """
    List public-safe workflow recipe cards.

    Recipes are decision cards for selecting ELF/MAGIC elements, PRE
    commands, SOL blocks, outputs, checks, and common pitfalls. They contain
    no solver outputs or machine-local validation paths.

    Args:
        tag: Optional tag filter, e.g. "motor", "flux-linkage",
             "maxwell-force", "eddy-current", "sinusoidal-ac".
        solver: Optional solver filter, currently mostly "MAGIC".

    Returns:
        Markdown index of recipe names. Drill down with ``elf_recipe_get``.
    """
    recipes = list_recipes(tag=tag or None, solver=solver or None)
    return format_recipe_index(recipes)


@mcp.tool()
def elf_recipe_search(query: str, top_k: int = 5, tag: str = "", solver: str = "") -> str:
    """
    Search public-safe workflow recipes by goal or keyword.

    Args:
        query: Goal or keywords, e.g. "back EMF pickup", "cogging torque",
               "current mutual flux", "MOMC frequency".
        top_k: Max recipes to return.
        tag: Optional tag filter.
        solver: Optional solver filter.

    Returns:
        Ranked recipe summaries with ``elf_recipe_get`` drilldown hints.
    """
    results = search_recipes(query, top_k=top_k, tag=tag or None, solver=solver or None)
    return format_search_results(results, query)


@mcp.tool()
def elf_recipe_get(name: str) -> str:
    """
    Get one public-safe workflow recipe by name.

    Args:
        name: Recipe name or unambiguous substring. Use
              ``elf_recipe_index`` or ``elf_recipe_search`` to discover
              names.

    Returns:
        Full recipe card with use cases, elements, PRE/SOL commands, outputs,
        checks, pitfalls, examples, and follow-up recipes.
    """
    recipe = get_recipe(name)
    if recipe is None:
        return f"No unique recipe named '{name}'. Try elf_recipe_index() or elf_recipe_search()."
    return format_recipe(recipe)


@mcp.tool()
def elf_plan_workflow(goal: str) -> str:
    """
    Propose a short ELF workflow plan from a natural-language goal.

    This is a recipe-level planner, not a solver. It chooses public-safe
    workflow cards and lists first checks and pitfalls.

    Args:
        goal: Natural-language target, e.g. "measure motor back EMF",
              "cogging torque sweep", "mutual inductance between coils".

    Returns:
        Markdown plan with recipe sequence and drilldown command.
    """
    plan = plan_workflow(goal)
    routes = route_sample_decks(goal, limit=3)
    return plan + "\n\n" + format_sample_deck_routes(routes, goal)


@mcp.tool()
def elf_help_get(path: str, max_chars: int = 30000) -> str:
    """
    Get full extracted text of a specific ELF600 help file.

    Args:
        path: Relative path under C:/ELF600/help/, e.g. "m_rf1/mr0003.htm",
              "d_ken/MOMC.htm", "u_support/error.htm". Use ``elf_help_index``
              or ``elf_help_search`` to discover paths. Filename-only also
              works if unambiguous.
        max_chars: Truncate output if longer (default 30000).

    Returns:
        File title + extracted text (HTML stripped, decoded from Shift_JIS).
    """
    result = get_help_file(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{path}': {result['error']}"
    head = f"# {result['path']}"
    if result["title"]:
        head += f"\n_title: {result['title']}_"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


# ============================================================
# Wiki tools (elf.co.jp PukiWiki vendor pages)
# ============================================================

@mcp.tool()
def elf_wiki_index() -> str:
    """
    List 146 ELF600 vendor wiki pages (https://elf.co.jp/) bundled with this server.

    Full crawl of all PukiWiki pages discoverable via cmd=list, including
    technical articles, case studies, FAQ, product info, download portals,
    and version-specific pages.

    Returns:
        Tab-separated: NAME<TAB>CHARS<TAB>URL per line.
    """
    pages = list_wiki_pages()
    lines = [f"{p['name']}\t{p['char_count']}\t{p['url']}" for p in pages]
    return f"# {len(pages)} wiki pages from elf.co.jp\n" + "\n".join(lines)


@mcp.tool()
def elf_wiki_search(query: str, top_k: int = 10) -> str:
    """
    Substring-search across all 146 bundled ELF vendor wiki pages.

    Multiple keywords (space-separated) require ALL to match (AND).

    Args:
        query: Keywords (e.g. "磁気モーメント法", "MRI 比較", "渦電流").
        top_k: Max results.

    Returns:
        Ranked snippets with page name, URL, and ~300-char excerpt.
    """
    results = search_wiki(query, top_k=top_k)
    if not results:
        return f"No matches for '{query}'"
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['name']}  (score={r['score']})")
        out.append(f"_{r['url']}_")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_wiki_get(name: str, max_chars: int = 30000) -> str:
    """
    Get full extracted text of a specific ELF vendor wiki page.

    Args:
        name: Page name (e.g. "磁場解析", "解析手順の紹介(magic)",
              "有限要素法との違い", "磁気モーメント法", "FAQ").
              Substring match also works if unambiguous.
        max_chars: Truncate output if longer (default 30000).

    Returns:
        Page name + URL + extracted text.
    """
    result = get_wiki_page(name, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{name}': {result['error']}"
    head = f"# {result['name']}\n_url: {result['url']}_"
    if result["title"]:
        head += f"\n_title: {result['title']}_"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


# ============================================================
# Python interface tools (C:/ELF600/bin/ Python wrappers + configs)
# ============================================================

@mcp.tool()
def elf_python_index(ext: str = "") -> str:
    """
    List 15 ELF600 bin/ files bundled with this server: Python ctypes
    interface (.py), configs (.cfg), definitions (.def, error codes etc.),
    and helper scripts (.bat, .txt) from C:/ELF600/bin/.

    Includes:
    - **elftypes.py / magtypes.py**: ctypes wrappers for elfh1300.dll /
      magh1600.dll exposing 83 API functions each (PRE / SOL / GET_FIEL /
      SET_AMP1 etc.) — the official Python interface for automating ELF.
    - **ELFERR.def / MESERR.def**: error code definitions.
    - **MAGIC.cfg / ELFIN.cfg**: solver default configs.
    - **Wmap2def.txt, *.def**: tool/format definitions.

    Args:
        ext: Filter by extension ("py", "cfg", "def", "txt", "bat"). Empty = all.

    Returns:
        Tab-separated: PATH<TAB>EXT<TAB>CHARS per line.
    """
    files = list_python_files(ext=ext or None)
    if not files:
        return f"No files match ext='{ext}'."
    lines = [f"{f['path']}\t{f['ext']}\t{f['char_count']}" for f in files]
    header = f"# {len(files)} bin/ files" + (f" (ext={ext})" if ext else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_python_search(query: str, top_k: int = 10, ext: str = "") -> str:
    """
    Substring-search across all 15 bundled ELF600 bin/ text files.

    Useful for finding specific API functions in elftypes.py / magtypes.py
    (e.g. "GET_FIEL" → see all related ctypes signatures), or looking up
    error codes (e.g. "ELF-Q103" in ELFERR.def).

    Args:
        query: Keywords (e.g. "GET_FIEL", "SET_AMP1", "MAGIC.cfg",
               "ELF-Q103", "MOMC").
        top_k: Max results.
        ext: Restrict to "py" / "cfg" / "def" / "txt" / "bat".

    Returns:
        Ranked snippets with file path and ~350-char excerpt.
    """
    results = search_python(query, top_k=top_k, ext=ext or None)
    if not results:
        return f"No matches for '{query}'"
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['path']}  (.{r['ext']}, score={r['score']})")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_python_get(path: str, max_chars: int = 30000) -> str:
    """
    Get full text of a specific ELF600 bin/ file.

    Args:
        path: Filename or relative path under C:/ELF600/bin/, e.g.
              "elftypes.py", "magtypes.py", "ELFERR.def", "MAGIC.cfg".
        max_chars: Truncate output if longer (default 30000).

    Returns:
        File text (UTF-8 / Shift_JIS auto-decoded).
    """
    result = get_python_file(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{path}': {result['error']}"
    head = f"# {result['path']}  (.{result['ext']})"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


# ============================================================
# MCP Prompts
# ============================================================

@mcp.prompt()
def new_elf_analysis(geometry: str, solver: str = "MAGIC") -> str:
    """Set up a new ELF analysis."""
    solver = solver.upper()
    if solver == "MAGIC":
        return (
            f"Set up a MAGIC magnetostatic analysis for: {geometry}\n\n"
            "Workflow:\n"
            "1. Create .mei mesh script (MODEL MAGIC T/K/R)\n"
            "2. Define coils (MCL), iron (MWL/MMB), magnets (HBRM)\n"
            "3. Add evaluation contour (MCO) after SPACE\n"
            "4. Run IEmesh to generate .meg\n"
            "5. Create .mai: USE MAGIC 3.50, PRE block (B-H, coils), SOL MOME\n"
            "6. Add SOL FIEL, SOL FORC/FORT as needed\n"
        )
    elif solver == "ELFIN":
        return (
            f"Set up an ELFIN eddy current analysis for: {geometry}\n\n"
            "Workflow:\n"
            "1. Create .mei mesh script (MODEL ELFIN T/K/R)\n"
            "2. Define conductors (ESC), magnetic bodies (EMB)\n"
            "3. Add evaluation contour (ECO) after SPACE\n"
            "4. Run IEmesh to generate .meg\n"
            "5. Create .mai: USE ELFIN 3.50, PRE block (VOL1, EDSC), SOL MOME\n"
            "6. Add SOL FIEL for field computation\n"
        )
    else:
        return (
            f"Set up a BEAM particle tracking analysis for: {geometry}\n\n"
            "Workflow:\n"
            "1. Compute EM fields with MAGIC or ELFIN first\n"
            "2. Create .mei mesh script (MODEL BEAM T/K/R)\n"
            "3. Define beam source nodes\n"
            "4. Create .mai: USE BEAM 3.50, PRE (CHAR, MASS, VOLB, FILE)\n"
            "5. SOL BEAM for tracking\n"
        )


# ============================================================
# Entry point
# ============================================================

def _use_utf8_stdout() -> None:
    """Force stdout/stderr to UTF-8 (cp932 Japanese consoles can't encode em-dashes etc).

    No-op if the streams don't expose ``reconfigure``. Never raises.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main():
    if "--selftest" in sys.argv:
        _use_utf8_stdout()
        print("ELF MCP server self-test:")

        # 1. Curated topics
        print("[1/16] elf_usage topics:")
        readiness = elf_mcp_readiness()
        assert "ready_for_tag_push" in readiness
        assert "S:" + "\\" not in readiness
        motor_readiness = elf_motor_readiness()
        assert "motor_coverage_ready_validation_upgrade_recommended" in motor_readiness
        assert "652 cases across 37 families" in motor_readiness
        assert "motor_gold_numeric_anchors" in motor_readiness
        assert "WARN" in motor_readiness
        assert "radia-motor targets" in motor_readiness
        assert "S:" + "\\" not in motor_readiness
        hybrid_route = elf_motor_hybrid_router("IPM hairpin motor flux linkage and MTPA")
        assert "ELF/radia motor hybrid router" in hybrid_route
        assert "application/motor/emdlab_ipm_hairpin_10" in hybrid_route
        assert "elf_motor_mmm_quick_check" in hybrid_route
        assert "ngsolve_usage(\"mtpa\")" in hybrid_route
        assert "elf_local_simulation_handoff" in hybrid_route
        assert "S:" + "\\" not in hybrid_route
        mmm_check = elf_motor_mmm_quick_check(motor_type="spm")
        assert "ELF motor 2D MMM/BEM-like quick check" in mmm_check
        assert "ngsolve_usage(\"back_emf\")" in mmm_check
        assert "not a production solver" in mmm_check
        python_design = elf_python_interface_design()
        assert "ELF/MAGIC Python Interface Design" in python_design
        assert "product_python_is_reference_not_required" in python_design
        assert "vendor_dll_is_immutable_boundary" in python_design
        assert "public_api_may_expand_above_product_python" in python_design
        assert "S:" + "\\" not in python_design
        api_manual = elf_python_api_manual()
        assert "ELF/MAGIC Python Facade API Manual" in api_manual
        assert "LLM Call Order" in api_manual
        assert "elf_python_deck_lint" in api_manual
        assert "Cubit mesh export" in api_manual
        assert "Netgen 2D" in api_manual
        assert "Product-side Python is reference material" in api_manual
        assert "S:" + "\\" not in api_manual
        api_schema = elf_python_api_schema("spm")
        assert "ELF Python Facade Schema" in api_schema
        assert '"motor_type": "spm"' in api_schema
        assert "`product_python_required`: `False`" in api_schema
        spec_lint = elf_python_motor_spec_lint(motor_type="ipm")
        assert "status: `PASS`" in spec_lint
        assert "ld_lq" in spec_lint
        deck_lint = elf_python_deck_lint(
            mai_path="application/motor/pm_cosine_pickup_72/pm001/pm001.mai",
            requested_observables="flux_linkage,back_emf_constant",
        )
        assert "status: `PASS`" in deck_lint
        assert "FLUM: `True`" in deck_lint
        pm_demag_lint = elf_python_pm_demag_step_lint(
            mai_text="USE MAGIC 3.50\nPRE 1 2\nHBRM 1 1.05 1.2\nHBCN 1 0 1\nHBCN 1 1 1\nHBCN 1 2 1\nEND\nSOL MOME\nEND"
        )
        assert "PM Demag Step Lint" in pm_demag_lint
        assert "status: `PASS`" in pm_demag_lint
        run_contract = elf_python_run_contract(
            goal="SPM motor back EMF sweep",
            motor_type="spm",
            source_public_deck_path="application/motor/pm_cosine_pickup_72/pm001/pm001.mai",
        )
        assert "keep_raw_outputs_user_local" in run_contract
        assert "RunRequest Contract" in run_contract
        parsed_run_result = elf_python_run_result_parse(
            payload="torque_nm=0.82\nloss_w=12.5\nefficiency=0.91\nLd_h=0.001\nLq_h=0.0018",
            case_id="cand_a",
            motor_type="spm",
            requested_observables="torque,loss_proxy",
        )
        assert "ELF Python RunResult Parser" in parsed_run_result
        assert "torque_value" in parsed_run_result
        assert "ld_lq_value" in parsed_run_result
        efficiency_map_result = elf_python_motor_efficiency_map_from_results(
            motor_type="spm",
            result_payloads_json=(
                '[{"case_id":"s00_t00","status":"PASS","parsed_observables":'
                '{"point_id":"s00_t00","speed_rpm":1000,"requested_torque_nm":0.1,'
                '"torque_nm":0.1,"loss_w":1.0}},'
                '{"case_id":"s00_t01","status":"PASS","parsed_observables":'
                '{"point_id":"s00_t01","speed_rpm":1000,"requested_torque_nm":0.2,'
                '"torque_nm":0.2,"loss_w":2.0}}]'
            ),
            torque_min_nm=0.1,
            torque_max_nm=0.2,
            torque_points=2,
            speed_min_rpm=1000,
            speed_max_rpm=1000,
            speed_points=1,
            base_speed_rpm=1000,
        )
        assert "ELF Python Motor Efficiency Map Result" in efficiency_map_result
        assert "Eta Grid" in efficiency_map_result
        design_plan = elf_python_motor_design_plan(
            goal="IPM torque density and Ld Lq",
            motor_type="ipm",
        )
        assert "ELF Python Motor Design Plan" in design_plan
        assert "magnet_v_angle_deg" in design_plan
        assert "dq_inductance" in design_plan
        sweep = elf_python_motor_sweep_matrix(
            motor_type="spm",
            objective="back_emf_target",
            budget=7,
        )
        assert "ELF Python Motor Sweep Matrix" in sweep
        assert "magnet_arc_fraction" in sweep
        assert "back_emf_constant" in sweep
        dq_map = elf_python_motor_dq_axis_map_plan(
            motor_type="ipm",
            pole_pairs=4,
            current_limit_a_peak=40,
            id_points=3,
            iq_points=3,
        )
        assert "ELF Python Motor DQ Axis Map Plan" in dq_map
        assert "PM and reluctance torque" in dq_map
        assert "flux_d_wb" in dq_map
        mtpa_plan = elf_python_motor_mtpa_search_plan(
            motor_type="ipm",
            pole_pairs=4,
            current_limit_a_peak=40,
            angle_points=9,
        )
        assert "ELF Python Motor MTPA Search Plan" in mtpa_plan
        assert "torque-per-amp" in mtpa_plan
        reluctance_plan = elf_python_reluctance_motor_design_plan(
            motor_type="synrm",
            pole_pairs=2,
            stator_slots=36,
        )
        assert "ELF Python Reluctance Motor Design Plan" in reluctance_plan
        assert "Ld/Lq" in reluctance_plan
        assert "dq_inductance" in reluctance_plan
        winding_plan = elf_python_motor_winding_layout_plan(
            stator_slots=48,
            pole_pairs=4,
        )
        assert "ELF Python Motor Winding Layout Plan" in winding_plan
        assert "q slots/pole/phase" in winding_plan
        assert "winding factor proxy" in winding_plan
        topology_plan = elf_python_motor_topology_parameter_plan(
            motor_type="ipm",
            rotor_topology="inner_rotor",
        )
        assert "ELF Python Motor Topology Parameter Plan" in topology_plan
        assert "bridge_thickness_mm" in topology_plan
        assert "magnet_v_angle_deg" in topology_plan
        demag_plan = elf_python_motor_demag_margin_plan(
            motor_type="spm",
            temperature_c=120,
        )
        assert "ELF Python Motor Demag Margin Plan" in demag_plan
        assert "risk label" in demag_plan
        assert "field_probe" in demag_plan
        drive_cycle = elf_python_motor_drive_cycle_plan(target_market="robot_drone")
        assert "ELF Python Motor Drive Cycle Plan" in drive_cycle
        assert "cycle_efficiency" in drive_cycle
        assert "weighted_total_loss_w" in drive_cycle
        optimization_plan = elf_python_motor_optimization_study_plan(
            motor_type="spm",
            objective="cycle_efficiency",
        )
        assert "ELF Python Motor Optimization Study Plan" in optimization_plan
        assert "constraint_violation_count" in optimization_plan
        assert "build winding layout plan" in optimization_plan
        optimization_loop = elf_python_motor_optimization_loop(
            motor_type="spm",
            objective="cycle_efficiency",
            result_payloads_json=(
                '[{"case_id":"baseline","status":"PASS","parsed_observables":'
                '{"torque_nm":0.7,"loss_w":15,"efficiency":0.88}},'
                '{"case_id":"candidate_hi","status":"PASS","parsed_observables":'
                '{"torque_nm":0.82,"loss_w":12,"efficiency":0.92}}]'
            ),
            budget=4,
        )
        assert "ELF Python Motor Optimization Loop" in optimization_loop
        assert "candidate_hi" in optimization_loop
        assert "Promotion Rules" in optimization_loop
        voltage_fw = elf_python_motor_voltage_field_weakening_plan(
            motor_type="ipm",
            dc_bus_v=48,
            speed_points=4,
        )
        assert "ELF Python Motor Voltage / Field-Weakening Plan" in voltage_fw
        assert "field_weakening_required" in voltage_fw or "voltage_margin_ok" in voltage_fw
        assert "required_negative_id_a_peak_proxy" in voltage_fw or "Idfw" in voltage_fw
        cogging_plan = elf_python_motor_cogging_ripple_plan(
            motor_type="spm",
            stator_slots=48,
            pole_pairs=4,
        )
        assert "ELF Python Motor Cogging / Ripple Plan" in cogging_plan
        assert "cogging order mechanical" in cogging_plan
        assert "torque_ripple_percent" in cogging_plan
        nvh_harmonics = elf_python_motor_airgap_harmonics_nvh_plan(
            motor_type="spm",
            stator_slots=48,
            pole_pairs=4,
        )
        assert "ELF Python Motor Airgap Harmonics / NVH Plan" in nvh_harmonics
        assert "slot-pass" in nvh_harmonics
        assert "NGSolve Follow-Up" in nvh_harmonics
        thermal_network = elf_python_motor_thermal_network_plan(total_loss_w=25)
        assert "ELF Python Motor Thermal Network Plan" in thermal_network
        assert "winding" in thermal_network
        assert "NGSolve Follow-Up" in thermal_network
        tolerance_plan = elf_python_motor_manufacturing_tolerance_plan(
            motor_type="spm",
            airgap_mm=0.8,
        )
        assert "ELF Python Motor Manufacturing Tolerance Plan" in tolerance_plan
        assert "eccentricity_mm" in tolerance_plan
        assert "unbalanced-force" in tolerance_plan
        material_plan = elf_python_motor_material_variation_plan(
            motor_type="spm",
            focus="magnet",
        )
        assert "ELF Python Motor Material Variation Plan" in material_plan
        assert "magnet.br_t" in material_plan
        feasibility_study = elf_python_motor_feasibility_study(
            goal="outer-rotor drone motor",
            target_market="robot_drone",
        )
        assert "ELF Python Motor Feasibility Study" in feasibility_study
        assert "mechanical_stress_feasibility" in feasibility_study
        assert "MCP Cannot Claim Alone" in feasibility_study
        ngsolve_crosscheck = elf_python_motor_ngsolve_result_crosscheck(
            run_result_payload='{"case_id":"cand_a","status":"PASS","parsed_observables":{"torque_nm":0.82,"loss_w":12.5}}',
            ngsolve_result_payload=(
                '{"schema_version":"elf-ngsolve-runtime-result/v1","results":['
                '{"lane":"thermal","peak_temperature_c":92.0},'
                '{"lane":"nvh","relative_order_separation":0.25},'
                '{"lane":"stress","yield_margin_proxy":2.1}]}'
            ),
        )
        assert "ELF Python Motor NGSolve Result Crosscheck" in ngsolve_crosscheck
        assert "overall status: `PASS`" in ngsolve_crosscheck
        drawing_bom = elf_python_motor_drawing_bom_handoff(
            motor_type="spm",
            rotor_topology="outer_rotor",
            validation_label="crosscheck_pass",
            run_result_payload='{"case_id":"cand_a","status":"PASS","parsed_observables":{"torque_nm":0.82}}',
        )
        assert "ELF Python Motor Drawing / BOM Handoff" in drawing_bom
        assert "permanent_magnets" in drawing_bom
        assert "Export Intent" in drawing_bom
        rotor_stress = elf_python_motor_rotor_stress_retention_plan(
            motor_type="spm",
            max_speed_rpm=12000,
        )
        assert "ELF Python Motor Rotor Stress / Retention Plan" in rotor_stress
        assert "retention margin proxy" in rotor_stress
        assert "NGSolve Follow-Up" in rotor_stress
        validation_scorecard = elf_python_motor_validation_scorecard(
            run_result_payload=(
                '{"case_id":"cand_a","status":"PASS","parsed_observables":'
                '{"torque_nm":0.82,"loss_w":12.5,"efficiency":0.91,'
                '"copper_loss_w":7.0,"iron_loss_w":3.0}}'
            ),
            ngsolve_result_payload=(
                '{"schema_version":"elf-ngsolve-runtime-result/v1","results":['
                '{"lane":"thermal","peak_temperature_c":92.0},'
                '{"lane":"nvh","relative_order_separation":0.25},'
                '{"lane":"stress","yield_margin_proxy":2.1}]}'
            ),
            drawing_bom_payload='{"validation_label":"crosscheck_pass"}',
        )
        assert "ELF Python Motor Validation Scorecard" in validation_scorecard
        assert "promotion decision" in validation_scorecard
        assert "loss_separation" in validation_scorecard
        efficiency_map = elf_python_motor_efficiency_map_plan(
            motor_type="spm",
            torque_points=3,
            speed_points=4,
            base_speed_rpm=3000,
            speed_max_rpm=9000,
        )
        assert "ELF Python Motor Efficiency Map Plan" in efficiency_map
        assert "eta_grid" in efficiency_map
        assert "feasible points by envelope" in efficiency_map
        run_queue = elf_python_motor_operating_point_run_queue(
            motor_type="spm",
            torque_points=2,
            speed_points=3,
            max_rows=6,
        )
        assert "ELF Python Motor Operating-Point Run Queue" in run_queue
        assert "op_001" in run_queue
        assert "requested observables" in run_queue.lower()
        pwm_plan = elf_python_motor_inverter_pwm_harmonic_plan(
            motor_type="spm",
            switching_frequency_hz=20000,
            fundamental_frequency_hz=400,
        )
        assert "ELF Python Motor Inverter / PWM Harmonic Plan" in pwm_plan
        assert "switching_sideband" in pwm_plan
        assert "magnet_loss_w" in pwm_plan
        saturation_map = elf_python_motor_saturation_inductance_map_plan(
            motor_type="ipm",
            current_points=2,
            angle_points=3,
        )
        assert "ELF Python Motor Saturation Inductance Map Plan" in saturation_map
        assert "sat_001" in saturation_map
        assert "saliency" in saturation_map
        loss_contract = elf_python_motor_loss_model_contract(motor_type="induction")
        assert "ELF Python Motor Loss Model Contract" in loss_contract
        assert "rotor_loss_w" in loss_contract
        envelope = elf_python_motor_torque_speed_envelope(
            motor_type="spm",
            peak_torque_nm=1.2,
            base_speed_rpm=3000,
            max_speed_rpm=9000,
            speed_points=4,
        )
        assert "ELF Python Motor Torque-Speed Envelope" in envelope
        assert "field_weakening_constant_power" in envelope
        slip_sweep = elf_python_induction_slip_sweep_plan(
            pole_pairs=2,
            supply_frequency_hz=50,
            slip_min=0.01,
            slip_max=0.05,
            slip_points=3,
        )
        assert "ELF Python Induction Motor Slip Sweep Plan" in slip_sweep
        assert "rotor_copper_loss_w = slip * airgap_power_w" in slip_sweep
        observable_contract = elf_python_motor_observable_contract(
            motor_type="ipm",
            study="dq_inductance",
        )
        assert "ELF Python Motor Observable Contract" in observable_contract
        assert "ld_lq_value" in observable_contract
        assert "MTPA trend" in observable_contract
        market_brief = elf_python_motor_market_brief(
            target_market="robot_drone",
            motor_type="spm",
            rotor_topology="outer_rotor",
        )
        assert "ELF Python Motor Market Brief" in market_brief
        assert "Robotics / drone" in market_brief
        assert "outer_rotor" in market_brief
        assert "End users provide specifications" in market_brief
        design_agent = elf_python_motor_design_agent_handoff(
            goal="outer-rotor drone SPM motor",
            target_market="robot_drone",
            motor_type="spm",
            rotor_topology="outer_rotor",
            continuous_torque_nm=0.8,
            base_speed_rpm=3500,
            dc_bus_v=48,
            outer_diameter_mm=80,
            stack_length_mm=20,
        )
        assert "ELF Python Motor Design Agent Handoff" in design_agent
        assert "ngsolve_multiphysics" in design_agent
        assert "nvh" in design_agent
        assert "thermal" in design_agent
        assert "stress" in design_agent
        assert "required NGSolve" in design_agent
        assert "drawing_intent" in design_agent
        assert "prototype_gate" in design_agent
        assert "does not execute licensed software" in design_agent
        ngsolve_plan = elf_python_ngsolve_validation_plan(
            goal="outer-rotor drone SPM motor",
            lanes="all",
        )
        assert "ELF Python NGSolve Multiphysics Validation Plan" in ngsolve_plan
        assert "H1 scalar heat equation" in ngsolve_plan
        assert "VectorH1 linear elasticity" in ngsolve_plan
        assert "script-generation calls" in ngsolve_plan or "script call" in ngsolve_plan
        ngsolve_script = elf_python_ngsolve_validation_script(
            goal="outer-rotor drone SPM motor",
            lane="all",
        )
        assert "ELF Python NGSolve Validation Script" in ngsolve_script
        assert "from ngsolve import *" in ngsolve_script
        assert "def run_thermal" in ngsolve_script
        assert "def run_nvh" in ngsolve_script
        assert "def run_stress" in ngsolve_script
        assert "elf-ngsolve-runtime-result/v1" in ngsolve_script
        meg_plan = elf_python_meg_generation_plan(
            goal="2D SPM motor cross-section",
            dimension="2d",
        )
        assert "MEG Generation Plan" in meg_plan
        assert "netgen_2d" in meg_plan
        assert "llm_2d_template" in meg_plan
        template_2d = elf_python_2d_motor_template(
            motor_type="spm",
            pole_pairs=4,
            stator_slots=48,
        )
        assert "ELF Python 2D Motor Template" in template_2d
        assert "llm_2d_template_then_netgen_2d_remesh" in template_2d
        assert "template is a draft" in template_2d
        topics = [
            "overview", "mai_format", "mei_format", "meg_format",
            "magic", "elfin", "beam", "element_types", "bh_curves",
            "sol_commands", "mei_commands", "ipm_motor", "motor_radia_bridge",
            "inductance",
            "magnetization", "examples", "meg_export",
            "treasure_box", "sinusoidal", "anisotropy", "sted",
            "meshing", "convergence", "force_methods", "errors",
            "iemesh", "tools", "cln_extraction", "licensing", "python_api",
            "live_drive", "force_gap_contract",
        ]
        for t in topics:
            result = elf_usage(t)
            assert len(result) > 50, f"Topic '{t}' too short"
        print(f"  {len(topics)} topics OK")

        # 2. Help index
        print("[2/16] elf_help_index:")
        idx = elf_help_index()
        n_files = len(list_help_files())
        assert n_files > 1000, f"Expected >1000 files, got {n_files}"
        print(f"  {n_files} files indexed")
        idx_mrf1 = elf_help_index("m_rf1/")
        assert "m_rf1/index.htm" in idx_mrf1, "m_rf1/ filter missed index.htm"
        print(f"  m_rf1/ filter OK")

        # 3. Help search
        print("[3/16] elf_help_search:")
        for q in ["MOMC", "渦電流", "OHM2", "FORC"]:
            r = elf_help_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 4. Help get
        print("[4/16] elf_help_get:")
        for p in ["m_rf1/index.htm", "d_ken/MOMC.htm", "u_support/error.htm"]:
            r = elf_help_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert len(r) > 100, f"{p} returned too little"
        print(f"  3 files OK")

        # 5. Examples index
        print("[5/16] elf_examples_index:")
        all_idx = elf_examples_index()
        n_ex = len(list_examples())
        assert n_ex > 300, f"Expected >300 examples, got {n_ex}"
        magic_idx = elf_examples_index(solver="MAGIC")
        assert "magic/BASIC/" in magic_idx, "MAGIC filter missed BASIC/"
        mai_idx = elf_examples_index(ext="mai")
        n_mai = len(list_examples(ext="mai"))
        assert n_mai > 100, f"Expected >100 .mai files, got {n_mai}"
        print(f"  {n_ex} examples ({n_mai} .mai), filters OK")

        # 6. Examples search
        print("[6/16] elf_examples_search:")
        for q in ["MOMC", "OHM2", "FREQ", "PRE"]:
            r = elf_examples_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 7. Examples get
        print("[7/16] elf_examples_get:")
        for p in ["magic/BASIC/ABCL2.mai"]:
            r = elf_examples_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert "MOMC" in r or "PRE" in r, f"{p} missing expected MAGIC keyword"
        print(f"  1 file OK")

        print("[8/16] elf_examples_playbook:")
        pb = elf_examples_playbook()
        assert pb.count("\n## ") >= 100, "Expected >=100 playbook cards"
        magic_pb = elf_examples_playbook(limit=120, solver="MAGIC")
        assert "97 cards" in magic_pb, "Expected 97 bundled MAGIC .mai cards"
        force_pb = elf_examples_playbook(limit=20, feature="maxwell-force")
        assert "SOL FORT" in force_pb or "MCM" in force_pb, "Maxwell-force filter missed force examples"
        print("  100-card playbook + filters OK")

        # 9. Public sample decks
        print("[9/16] elf_sample_decks tools:")
        sd = elf_sample_decks_index()
        assert "application/motor/pm_cosine_pickup_72/pm001/pm001.mai" in sd
        assert "application/motor/pm_cosine_pickup_72/pm001/pm001.meg" in sd
        assert "application/motor/spm_surface_pm_10/spm001/spm001.mai" in sd
        assert "application/motor/srm_switched_reluctance_10/srm001/srm001.mai" in sd
        assert "application/motor/induction_cage_10/im001/im001.mai" in sd
        assert "application/motor/emdlab_bldc_spm_10/ebl001/ebl001.mai" in sd
        assert "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" in sd
        assert "application/motor/emdlab_induction_bar_10/eim001/eim001.mai" in sd
        assert "application/motor/emdlab_synrm_flux_barrier_10/esr001/esr001.mai" in sd
        assert "application/motor/emdlab_srm_pole_variants_10/esm001/esm001.mai" in sd
        assert "application/motor/emdlab_afpm_linearized_10/eaf001/eaf001.mai" in sd
        assert "application/motor/ipm_interior_pm_10/ipm001/ipm001.mai" in sd
        assert "application/motor/wound_field_sync_10/wfs001/wfs001.mai" in sd
        assert "application/motor/axial_flux_pm_10/afm001/afm001.mai" in sd
        assert "application/motor/linear_pm_motor_10/lpm001/lpm001.mai" in sd
        assert "application/motor/stepper_motor_10/stm001/stm001.mai" in sd
        assert "application/transformer_core_pickup_12/tf001/tf001.mai" in sd
        assert "application/mri_gradient_shield_12/mri001/mri001.mai" in sd
        assert "application/wpt_coupled_coils_10/wpt001/wpt001.mai" in sd
        assert "application/wpt_loop_10/wpl001/wpl001.mai" in sd
        assert "application/mri_loop_10/mrl001/mrl001.mai" in sd
        assert "application/motor/sr_motor_loop_10/srl001/srl001.mai" in sd
        assert "application/motor/spm_loop_10/spl001/spl001.mai" in sd
        assert "application/ih_induction_heating_10/ihl001/ihl001.mai" in sd
        assert "application/motor/reluctance_motor_10/ryl001/ryl001.mai" in sd
        assert "application/motor/hysteresis_motor_10/hyl001/hyl001.mai" in sd
        assert "application/transformer_loop_10/tfl001/tfl001.mai" in sd
        assert "application/accelerator_magnet_10/acl001/acl001.mai" in sd
        assert "application/actuator_plunger_10/atl001/atl001.mai" in sd
        assert "application/maglev_bearing_10/mvl001/mvl001.mai" in sd
        assert "application/magnetic_separator_10/msl001/msl001.mai" in sd
        assert "application/eddy_current_brake_10/ebl001/ebl001.mai" in sd
        assert "application/ndt_eddy_probe_10/ndl001/ndl001.mai" in sd
        assert "application/magnetic_gear_10/mgl001/mgl001.mai" in sd
        assert "application/voice_coil_10/vcl001/vcl001.mai" in sd
        assert "application/relay_solenoid_10/rsl001/rsl001.mai" in sd
        assert "application/hall_sensor_fixture_10/hsl001/hsl001.mai" in sd
        assert "application/electromagnetic_clutch_10/ecl001/ecl001.mai" in sd
        assert "application/wpt_misalignment_10/wpm001/wpm001.mai" in sd
        assert "application/mri_gradient_sequence_10/mgs001/mgs001.mai" in sd
        assert "application/transformer_leakage_10/tlg001/tlg001.mai" in sd
        assert "application/ih_susceptor_ring_10/ihr001/ihr001.mai" in sd
        assert "application/accelerator_corrector_10/acm001/acm001.mai" in sd
        assert "application/motor/emdlab_bldc_outer_rotor_10/ebo001/ebo001.mai" in sd
        assert "application/motor/emdlab_spmsm_static_torque_10/eptq001/eptq001.mai" in sd
        assert "application/motor/emdlab_srm1216_outer_rotor_10/ero001/ero001.mai" in sd
        assert "application/emdlab_1ph_transformer_static_10/ept001/ept001.mai" in sd
        assert "application/emdlab_benchmark_ccore_10/ecc001/ecc001.mai" in sd
        assert "application/numeric_validation_anchors_10/nva001/nva001.mai" in sd
        assert "application/numeric_flum_law_64/nfl001/nfl001.mai" in sd
        assert "application/numeric_inductance_energy_100/nie001/nie001.mai" in sd
        assert "application/numeric_force_torque_100/nft001/nft001.mai" in sd
        assert "application/numeric_ac_loss_100/nal001/nal001.mai" in sd
        assert "application/numeric_magnetic_circuit_100/nmc001/nmc001.mai" in sd
        assert "application/numeric_permanent_magnet_100/npm001/npm001.mai" in sd
        assert "application/numeric_transformer_coupling_100/ntc001/ntc001.mai" in sd
        sd_mai = elf_sample_decks_index(ext="mai")
        assert sd_mai.count(".mai") == 1600, "Expected 1600 public .mai decks"
        sd_search = elf_sample_decks_search("HBCN FLUM", top_k=5, ext="mai")
        assert "pm001.mai" in sd_search and "No sample deck matches" not in sd_search
        sd_spm_search = elf_sample_decks_search("SPM HBRM FLUM", top_k=5, ext="mai")
        assert "application/motor/spm_surface_pm_10" in sd_spm_search
        sd_srm_search = elf_sample_decks_search("SRM reluctance FLUM", top_k=5, ext="mai")
        assert "application/motor/srm_switched_reluctance_10" in sd_srm_search
        sd_im_search = elf_sample_decks_search("induction motor cage OHM2 FLUM", top_k=5, ext="mai")
        assert "application/motor/induction_cage_10" in sd_im_search
        sd_emdlab_ipm_search = elf_sample_decks_search("EMDLAB-style IPM hairpin FLUM", top_k=5, ext="mai")
        assert "application/motor/emdlab_ipm_hairpin_10" in sd_emdlab_ipm_search
        sd_emdlab_im_search = elf_sample_decks_search("induction-machine bar OHM2 FLUM", top_k=5, ext="mai")
        assert "application/motor/emdlab_induction_bar_10" in sd_emdlab_im_search
        sd_emdlab_synrm_search = elf_sample_decks_search("EMDLAB-style SynRM flux-barrier FLUM", top_k=5, ext="mai")
        assert "application/motor/emdlab_synrm_flux_barrier_10" in sd_emdlab_synrm_search
        sd_emdlab_srm_search = elf_sample_decks_search("EMDLAB-style SRM pole-variant FLUM", top_k=5, ext="mai")
        assert "application/motor/emdlab_srm_pole_variants_10" in sd_emdlab_srm_search
        sd_emdlab_afpm_search = elf_sample_decks_search("EMDLAB-style AFPM linearized-airgap FLUM", top_k=5, ext="mai")
        assert "application/motor/emdlab_afpm_linearized_10" in sd_emdlab_afpm_search
        sd_loop13_wound_search = elf_sample_decks_search("Loop13 wound-field synchronous FLUM", top_k=5, ext="mai")
        assert "application/motor/wound_field_sync_10" in sd_loop13_wound_search
        sd_loop13_stepper_search = elf_sample_decks_search("Loop13 stepper motor detent FLUM", top_k=5, ext="mai")
        assert "application/motor/stepper_motor_10" in sd_loop13_stepper_search
        sd_loop13_wpt_search = elf_sample_decks_search("Loop13 WPT misalignment OHM2", top_k=5, ext="mai")
        assert "application/wpt_misalignment_10" in sd_loop13_wpt_search
        sd_loop13_mri_search = elf_sample_decks_search("Loop13 MRI gradient sequence OHM2", top_k=5, ext="mai")
        assert "application/mri_gradient_sequence_10" in sd_loop13_mri_search
        sd_route = elf_sample_decks_route("IPM hairpin motor flux linkage", limit=3)
        assert "application/motor/emdlab_ipm_hairpin_10" in sd_route
        assert "elf_sample_decks_playbook" in sd_route
        sd_spm_route = elf_sample_decks_route("SPM motor flux linkage sweep", limit=3)
        assert "application/motor/spm_surface_pm_10" in sd_spm_route.split("## 2.", 1)[0]
        sd_wpt_route = elf_sample_decks_route("WPT misalignment with conducting shield", limit=2)
        assert "application/wpt_misalignment_10" in sd_wpt_route
        sd_outer_route = elf_sample_decks_route("BLDC outer rotor motor", limit=2)
        assert "application/motor/emdlab_bldc_outer_rotor_10" in sd_outer_route
        sd_transformer_static_route = elf_sample_decks_route("single phase transformer static", limit=2)
        assert "application/emdlab_1ph_transformer_static_10" in sd_transformer_static_route
        sd_ccore_route = elf_sample_decks_route("benchmark C-core magnet", limit=2)
        assert "application/emdlab_benchmark_ccore_10" in sd_ccore_route
        sd_numeric_route = elf_sample_decks_route("numeric validation anchor FLUM invariant", limit=2)
        assert "application/numeric_validation_anchors_10" in sd_numeric_route
        sd_flum_law_route = elf_sample_decks_route("FLUM law current linearity superposition", limit=2)
        assert "application/numeric_flum_law_64" in sd_flum_law_route
        sd_inductance_route = elf_sample_decks_route("inductance co-energy FLUM turn scaling", limit=2)
        assert "application/numeric_inductance_energy_100" in sd_inductance_route
        sd_force_route = elf_sample_decks_route("force torque co-energy gradient", limit=2)
        assert "application/numeric_force_torque_100" in sd_force_route
        sd_ac_loss_search = elf_sample_decks_search("AC loss frequency square OHM2", top_k=5, ext="mai")
        assert "application/numeric_ac_loss_100" in sd_ac_loss_search
        sd_ac_loss_route = elf_sample_decks_route("AC loss frequency square OHM2", limit=2)
        assert "application/numeric_ac_loss_100" in sd_ac_loss_route
        sd_magnetic_circuit_search = elf_sample_decks_search("magnetic circuit air gap HBCU", top_k=5, ext="mai")
        assert "application/numeric_magnetic_circuit_100" in sd_magnetic_circuit_search
        sd_magnetic_circuit_route = elf_sample_decks_route("magnetic circuit air gap HBCU", limit=2)
        assert "application/numeric_magnetic_circuit_100" in sd_magnetic_circuit_route
        sd_permanent_magnet_search = elf_sample_decks_search("permanent magnet HBRM polarity FLUM", top_k=5, ext="mai")
        assert "application/numeric_permanent_magnet_100" in sd_permanent_magnet_search
        sd_permanent_magnet_route = elf_sample_decks_route("permanent magnet HBRM polarity FLUM", limit=2)
        assert "application/numeric_permanent_magnet_100" in sd_permanent_magnet_route
        sd_transformer_coupling_search = elf_sample_decks_search("transformer coupling turns ratio HBCU FLUM", top_k=5, ext="mai")
        assert "application/numeric_transformer_coupling_100" in sd_transformer_coupling_search
        sd_transformer_coupling_route = elf_sample_decks_route("transformer coupling turns ratio HBCU FLUM", limit=2)
        assert "application/numeric_transformer_coupling_100" in sd_transformer_coupling_route
        sd_app_search = elf_sample_decks_search("MRI OHM2 FREQ", top_k=5, ext="mai")
        assert "application/mri" in sd_app_search
        sd_wpt_search = elf_sample_decks_search("WPT MOMC FLUM", top_k=5, ext="mai")
        assert "application/wpt" in sd_wpt_search
        sd_wpt_loop_search = elf_sample_decks_search("Loop10 WPT MOMC FLUM", top_k=5, ext="mai")
        assert "application/wpt_loop_10" in sd_wpt_loop_search
        sd_mri_loop_search = elf_sample_decks_search("Loop10 MRI OHM2 FREQ", top_k=5, ext="mai")
        assert "application/mri_loop_10" in sd_mri_loop_search
        sd_sr_loop_search = elf_sample_decks_search("SR-motor reluctance FLUM", top_k=5, ext="mai")
        assert "application/motor/sr_motor_loop_10" in sd_sr_loop_search
        sd_spm_loop_search = elf_sample_decks_search("Loop10 SPM HBRM FLUM", top_k=5, ext="mai")
        assert "application/motor/spm_loop_10" in sd_spm_loop_search
        sd_ih_search = elf_sample_decks_search("IH induction-heating MOMC", top_k=5, ext="mai")
        assert "application/ih_induction_heating_10" in sd_ih_search
        sd_reluctance_search = elf_sample_decks_search("reluctance motor synchronous saliency", top_k=5, ext="mai")
        assert "application/motor/reluctance_motor_10" in sd_reluctance_search
        sd_hysteresis_search = elf_sample_decks_search("hysteresis motor high-coercivity", top_k=5, ext="mai")
        assert "application/motor/hysteresis_motor_10" in sd_hysteresis_search
        sd_transformer_loop_search = elf_sample_decks_search("Loop10 transformer FLUM", top_k=5, ext="mai")
        assert "application/transformer_loop_10" in sd_transformer_loop_search
        sd_accelerator_search = elf_sample_decks_search("accelerator electromagnet FLUM", top_k=5, ext="mai")
        assert "application/accelerator_magnet_10" in sd_accelerator_search
        sd_actuator_search = elf_sample_decks_search("Loop11 actuator plunger FLUM", top_k=5, ext="mai")
        assert "application/actuator_plunger_10" in sd_actuator_search
        sd_maglev_search = elf_sample_decks_search("Loop11 maglev bearing FLUM", top_k=5, ext="mai")
        assert "application/maglev_bearing_10" in sd_maglev_search
        sd_separator_search = elf_sample_decks_search("Loop11 magnetic separator FLUM", top_k=5, ext="mai")
        assert "application/magnetic_separator_10" in sd_separator_search
        sd_brake_search = elf_sample_decks_search("Loop11 eddy-current brake OHM2", top_k=5, ext="mai")
        assert "application/eddy_current_brake_10" in sd_brake_search
        sd_ndt_search = elf_sample_decks_search("Loop11 NDT eddy-current probe OHM2", top_k=5, ext="mai")
        assert "application/ndt_eddy_probe_10" in sd_ndt_search
        sd_gear_search = elf_sample_decks_search("Loop12 magnetic gear HBCN FLUM", top_k=5, ext="mai")
        assert "application/magnetic_gear_10" in sd_gear_search
        sd_voice_search = elf_sample_decks_search("Loop12 voice-coil actuator FLUM", top_k=5, ext="mai")
        assert "application/voice_coil_10" in sd_voice_search
        sd_relay_search = elf_sample_decks_search("Loop12 relay solenoid FLUM", top_k=5, ext="mai")
        assert "application/relay_solenoid_10" in sd_relay_search
        sd_hall_search = elf_sample_decks_search("Loop12 Hall-sensor fixture FLUM", top_k=5, ext="mai")
        assert "application/hall_sensor_fixture_10" in sd_hall_search
        sd_clutch_search = elf_sample_decks_search("Loop12 electromagnetic clutch OHM2", top_k=5, ext="mai")
        assert "application/electromagnetic_clutch_10" in sd_clutch_search
        sd_get = elf_sample_decks_get("application/motor/pm_cosine_pickup_72/pm001/pm001.mai")
        assert "HBCN 1 0 1" in sd_get and "HBCN 2 0 2" in sd_get
        sd_get_legacy = elf_sample_decks_get("motor/pm_cosine_pickup_72/pm001/pm001.mai")
        assert "application/motor/pm_cosine_pickup_72/pm001/pm001.mai" in sd_get_legacy
        sd_pb = elf_sample_decks_playbook(limit=28, family="pm_square")
        assert sd_pb.count("\n## ") == 28, "Expected 28 sample deck playbook cards"
        sd_app_pb = elf_sample_decks_playbook(limit=20, family="transformer_core_pickup_12")
        assert sd_app_pb.count("\n## ") == 12, "Expected 12 transformer sample cards"
        sd_loop_pb = elf_sample_decks_playbook(limit=20, family="accelerator_magnet_10")
        assert sd_loop_pb.count("\n## ") == 10, "Expected 10 accelerator sample cards"
        sd_loop11_pb = elf_sample_decks_playbook(limit=20, family="actuator_plunger_10")
        assert sd_loop11_pb.count("\n## ") == 10, "Expected 10 actuator sample cards"
        sd_loop12_pb = elf_sample_decks_playbook(limit=20, family="magnetic_gear_10")
        assert sd_loop12_pb.count("\n## ") == 10, "Expected 10 magnetic-gear sample cards"
        sd_emdlab_pb = elf_sample_decks_playbook(limit=240, query="EMDLAB-style")
        assert sd_emdlab_pb.count("\n## ") == 240, "Expected EMDLAB-style sample cards"
        assert "emdlab_ipm_hairpin_10" in sd_emdlab_pb
        sd_numeric_pb = elf_sample_decks_playbook(limit=20, family="numeric_validation")
        assert sd_numeric_pb.count("\n## ") == 10, "Expected numeric validation anchor cards"
        sd_flum_law_pb = elf_sample_decks_playbook(limit=70, family="numeric_flum_law")
        assert sd_flum_law_pb.count("\n## ") == 64, "Expected numeric FLUM law cards"
        sd_inductance_pb = elf_sample_decks_playbook(limit=110, family="numeric_inductance_energy")
        assert sd_inductance_pb.count("\n## ") == 100, "Expected numeric inductance energy cards"
        sd_force_pb = elf_sample_decks_playbook(limit=110, family="numeric_force_torque")
        assert sd_force_pb.count("\n## ") == 100, "Expected numeric force torque cards"
        sd_ac_loss_pb = elf_sample_decks_playbook(limit=110, family="numeric_ac_loss")
        assert sd_ac_loss_pb.count("\n## ") == 100, "Expected numeric AC loss cards"
        sd_magnetic_circuit_pb = elf_sample_decks_playbook(limit=110, family="numeric_magnetic_circuit")
        assert sd_magnetic_circuit_pb.count("\n## ") == 100, "Expected numeric magnetic circuit cards"
        sd_permanent_magnet_pb = elf_sample_decks_playbook(limit=110, family="numeric_permanent_magnet")
        assert sd_permanent_magnet_pb.count("\n## ") == 100, "Expected numeric permanent magnet cards"
        sd_transformer_coupling_pb = elf_sample_decks_playbook(limit=110, family="numeric_transformer_coupling")
        assert sd_transformer_coupling_pb.count("\n## ") == 100, "Expected numeric transformer coupling cards"
        sd_validation = elf_sample_decks_validation()
        assert "1600 cases" in sd_validation
        assert "ngsolve_proxy_energy" in sd_validation
        assert "ngsolve_numeric_invariant" in sd_validation
        assert "not a full absolute field/force/torque/loss agreement suite" in sd_validation
        assert "100-case publication checkpoints" in sd_validation
        assert "100 additional validated cases would make the next optional increment" in sd_validation
        sd_numeric_validation = elf_sample_decks_validation(family="numeric_validation")
        assert "application/numeric_validation_anchors_10" in sd_numeric_validation
        assert "elf_flux_invariants_passed" in sd_numeric_validation
        sd_flum_law_validation = elf_sample_decks_validation(family="numeric_flum_law")
        assert "application/numeric_flum_law_64" in sd_flum_law_validation
        assert "64 cases" in sd_flum_law_validation
        sd_inductance_validation = elf_sample_decks_validation(family="numeric_inductance_energy")
        assert "application/numeric_inductance_energy_100" in sd_inductance_validation
        assert "100 cases" in sd_inductance_validation
        sd_force_validation = elf_sample_decks_validation(family="numeric_force_torque")
        assert "application/numeric_force_torque_100" in sd_force_validation
        assert "100 cases" in sd_force_validation
        sd_ac_loss_validation = elf_sample_decks_validation(family="numeric_ac_loss")
        assert "application/numeric_ac_loss_100" in sd_ac_loss_validation
        assert "100 cases" in sd_ac_loss_validation
        sd_magnetic_circuit_validation = elf_sample_decks_validation(family="numeric_magnetic_circuit")
        assert "application/numeric_magnetic_circuit_100" in sd_magnetic_circuit_validation
        assert "100 cases" in sd_magnetic_circuit_validation
        sd_permanent_magnet_validation = elf_sample_decks_validation(family="numeric_permanent_magnet")
        assert "application/numeric_permanent_magnet_100" in sd_permanent_magnet_validation
        assert "100 cases" in sd_permanent_magnet_validation
        sd_transformer_coupling_validation = elf_sample_decks_validation(family="numeric_transformer_coupling")
        assert "application/numeric_transformer_coupling_100" in sd_transformer_coupling_validation
        assert "100 cases" in sd_transformer_coupling_validation
        sd_quality = elf_sample_decks_quality()
        assert "Publication Quality Gates (PASS)" in sd_quality
        assert "paired_mai_meg" in sd_quality
        assert "manifest_matches_files" in sd_quality
        assert "gold_numeric_invariant" in sd_quality
        assert "silver_observable_contract" in sd_quality
        assert "silver_proxy_energy" in sd_quality
        sd_gold_quality = elf_sample_decks_quality(label="gold")
        assert "application/numeric_transformer_coupling_100" in sd_gold_quality
        sd_observable_quality = elf_sample_decks_quality(label="observable")
        assert "500 cases" in sd_observable_quality
        assert "application/motor/pm_square_2pole_pickup_100" in sd_observable_quality
        sd_observable_contracts = elf_sample_decks_observable_contracts()
        assert "Observable Contract Gates (PASS)" in sd_observable_contracts
        assert "public_observable_contract_passed" in sd_observable_contracts
        assert "application/wpt_misalignment_10" in sd_observable_contracts
        sd_physics = elf_sample_decks_physics()
        assert "Physical Quantity Gates (PASS)" in sd_physics
        assert "flux_linkage" in sd_physics
        assert "gold_physics_anchor_coverage" in sd_physics
        sd_force_physics = elf_sample_decks_physics(quantity="force")
        assert "force_torque_gradient" in sd_force_physics
        assert "application/numeric_force_torque_100" in sd_force_physics
        sd_validation_matrix = elf_sample_decks_validation_matrix()
        assert "Validation Matrix Gates (PASS)" in sd_validation_matrix
        assert "transformer_coupling" in sd_validation_matrix
        assert "application/numeric_transformer_coupling_100/ntc001/ntc001.mai" in sd_validation_matrix
        sd_transformer_matrix = elf_sample_decks_validation_matrix(quantity="transformer", label="gold")
        assert "application/numeric_transformer_coupling_100" in sd_transformer_matrix
        assert "ngsolve_numeric_invariants_passed" in sd_transformer_matrix
        sd_cross_validation = elf_sample_decks_cross_validation()
        assert "Cross-Validation Gates (PASS)" in sd_cross_validation
        assert "No family is missing independent NGSolve cross-validation" in sd_cross_validation
        assert "ngsolve_proxy_energy_positive" in sd_cross_validation
        assert "ngsolve_numeric_invariants_passed" in sd_cross_validation
        sd_gold_cross_validation = elf_sample_decks_cross_validation(level="ngsolve_numeric_invariant")
        assert "674 cases" in sd_gold_cross_validation
        assert "application/numeric_transformer_coupling_100" in sd_gold_cross_validation
        sd_motor_readiness = elf_motor_readiness(family="ipm")
        assert "ELF/MAGIC motor readiness" in sd_motor_readiness
        assert "IPM" in sd_motor_readiness
        assert "ld_lq" in sd_motor_readiness
        sd_hybrid_router = elf_motor_hybrid_router("induction motor slip loss and cage screening")
        assert "application/motor/emdlab_induction_bar_10" in sd_hybrid_router
        assert "elf_motor_mmm_quick_check" in sd_hybrid_router
        assert "ngsolve_usage(\"induction_machine\")" in sd_hybrid_router
        sd_duplicates = elf_sample_decks_duplicates()
        assert "Duplicate Gates (PASS)" in sd_duplicates
        assert "No exact pair duplicates were found" in sd_duplicates
        sd_handoff = elf_local_simulation_handoff(
            "SPM motor flux linkage sweep",
            family="spm",
            quantity="motor",
        )
        assert "ELF/MAGIC local simulation handoff" in sd_handoff
        assert "Runner Input Contract" in sd_handoff
        assert "application/motor/spm_surface_pm_10" in sd_handoff
        assert "does not execute ELF/MAGIC" in sd_handoff
        sd_representatives = elf_sample_decks_representatives()
        assert "why representative" in sd_representatives
        assert "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" in sd_representatives
        sd_motor_representatives = elf_sample_decks_representatives(area="motor")
        assert "application/motor/emdlab_ipm_hairpin_10" in sd_motor_representatives
        sd_promotion = elf_public_promotion(audience="ja")
        assert "1600" in sd_promotion and "品質ラベル" in sd_promotion
        sd_invariant_validation = elf_sample_decks_validation(level="ngsolve_numeric_invariant")
        assert "674 cases" in sd_invariant_validation
        assert "application/numeric_validation_anchors_10" in sd_invariant_validation
        assert "application/numeric_flum_law_64" in sd_invariant_validation
        assert "application/numeric_inductance_energy_100" in sd_invariant_validation
        assert "application/numeric_force_torque_100" in sd_invariant_validation
        assert "application/numeric_ac_loss_100" in sd_invariant_validation
        assert "application/numeric_magnetic_circuit_100" in sd_invariant_validation
        assert "application/numeric_permanent_magnet_100" in sd_invariant_validation
        assert "application/numeric_transformer_coupling_100" in sd_invariant_validation
        sd_loop13_motor_pb = elf_sample_decks_playbook(limit=50, query="Loop13 motor")
        assert sd_loop13_motor_pb.count("\n## ") == 50, "Expected Loop13 motor sample cards"
        assert "wound_field_sync_10" in sd_loop13_motor_pb
        sd_loop13_app_pb = elf_sample_decks_playbook(limit=20, query="Loop13 WPT misalignment")
        assert "wpt_misalignment_10" in sd_loop13_app_pb
        assert "Python-interface seed manifest" not in sd_pb, "Normal sample playbook must not claim team28"
        sample_corpus_text = (
            sd + sd_mai + sd_search + sd_spm_search + sd_srm_search
            + sd_im_search + sd_app_search + sd_wpt_search + sd_get + sd_pb + sd_app_pb
            + sd_emdlab_ipm_search + sd_emdlab_im_search + sd_emdlab_synrm_search
            + sd_emdlab_srm_search + sd_emdlab_afpm_search + sd_emdlab_pb
            + sd_loop13_wound_search + sd_loop13_stepper_search
            + sd_loop13_wpt_search + sd_loop13_mri_search
            + sd_route + sd_spm_route + sd_wpt_route + sd_outer_route
            + sd_transformer_static_route + sd_ccore_route + sd_numeric_route
            + sd_flum_law_route + sd_inductance_route + sd_force_route
            + sd_ac_loss_search + sd_ac_loss_route + sd_ac_loss_pb
            + sd_magnetic_circuit_search + sd_magnetic_circuit_route
            + sd_magnetic_circuit_pb
            + sd_permanent_magnet_search + sd_permanent_magnet_route
            + sd_permanent_magnet_pb
            + sd_transformer_coupling_search + sd_transformer_coupling_route
            + sd_transformer_coupling_pb
            + sd_validation + sd_numeric_validation + sd_flum_law_validation
            + sd_inductance_validation + sd_force_validation
            + sd_ac_loss_validation
            + sd_magnetic_circuit_validation
            + sd_permanent_magnet_validation
            + sd_transformer_coupling_validation
            + sd_quality + sd_gold_quality + sd_observable_quality
            + sd_observable_contracts + sd_physics + sd_force_physics
            + sd_validation_matrix + sd_transformer_matrix
            + sd_cross_validation + sd_gold_cross_validation
            + sd_motor_readiness + sd_hybrid_router
            + sd_duplicates
            + sd_representatives
            + sd_motor_representatives + sd_promotion
            + sd_invariant_validation
            + sd_loop13_motor_pb + sd_loop13_app_pb
            + sd_wpt_loop_search + sd_mri_loop_search + sd_sr_loop_search
            + sd_spm_loop_search + sd_ih_search + sd_reluctance_search
            + sd_hysteresis_search + sd_transformer_loop_search
            + sd_accelerator_search + sd_actuator_search + sd_maglev_search
            + sd_separator_search + sd_brake_search + sd_ndt_search
            + sd_gear_search + sd_voice_search + sd_relay_search
            + sd_hall_search + sd_clutch_search + sd_loop_pb + sd_loop11_pb
            + sd_loop12_pb + sd_numeric_pb + sd_flum_law_pb + sd_inductance_pb
            + sd_force_pb
        )
        handoff_text = sd_handoff
        sample_text = sample_corpus_text + handoff_text
        private_markers = (
            "C:" + "\\temp",
            "C:" + "\\tmp",
            "S:" + "\\",
            "W:" + "\\",
            "_cross" + "val",
        )
        forbidden_corpus_output_markers = (".mao", ".mat", ".mac")
        assert not any(marker in sample_text for marker in private_markers)
        assert not any(
            marker in sample_corpus_text
            for marker in forbidden_corpus_output_markers
        )
        assert "direct_solver_exe_no_gui" in handoff_text
        assert ".mao" in handoff_text
        assert ".mag" in handoff_text
        assert ".mei" in handoff_text
        print("  1600-case .mai/.meg sample deck corpus OK")

        # 10. Recipe tools
        print("[10/16] elf_recipe tools:")
        ri = elf_recipe_index()
        assert "passive_flum_pickup" in ri and "maxwell_torque_surface" in ri
        rs = elf_recipe_search("back EMF pickup", top_k=3)
        assert "passive_flum_pickup" in rs
        rg = elf_recipe_get("mutual_flux_current_pickup")
        assert "FLUM <pickup_mid>" in rg and "AMP1" in rg
        rp = elf_plan_workflow("cogging torque sweep")
        assert "maxwell_torque_surface" in rp
        recipe_text = ri + rs + rg + rp
        private_markers = ("C:" + "\\temp", "_cross" + "val")
        assert not any(marker in recipe_text for marker in private_markers)
        print("  recipe index/search/get/plan OK")

        # 11-13. Wiki tools
        print("[11/16] elf_wiki_index:")
        wi = elf_wiki_index()
        n_w = len(list_wiki_pages())
        assert n_w >= 50, f"Expected >=50 wiki pages, got {n_w}"
        print(f"  {n_w} wiki pages")

        print("[12/16] elf_wiki_search:")
        for q in ["磁場解析", "MAGIC", "渦電流"]:
            r = elf_wiki_search(q, top_k=3)
            assert "No matches" not in r, f"Wiki query '{q}' had no matches"
        print(f"  3 queries OK")

        print("[13/16] elf_wiki_get:")
        for p in ["FAQ", "磁場解析"]:
            r = elf_wiki_get(p)
            assert "Error reading" not in r, f"Failed to read wiki '{p}'"
            assert len(r) > 100
        print(f"  2 pages OK")

        # 14-16. Python interface tools
        print("[14/16] elf_python_index:")
        pi = elf_python_index()
        n_p = len(list_python_files())
        assert n_p >= 10, f"Expected >=10 bin files, got {n_p}"
        py_only = elf_python_index(ext="py")
        assert "elftypes.py" in py_only and "magtypes.py" in py_only
        print(f"  {n_p} files (py filter OK)")

        print("[15/16] elf_python_search:")
        for q in ["GET_FIEL", "SET_AMP1", "ctypes"]:
            r = elf_python_search(q, top_k=3)
            assert "No matches" not in r, f"Python query '{q}' had no matches"
        print(f"  3 queries OK")

        print("[16/16] elf_python_get:")
        for p in ["elftypes.py", "magtypes.py", "ELFERR.def"]:
            r = elf_python_get(p)
            assert "Error reading" not in r, f"Failed to read python '{p}'"
        team28 = elf_python_team28()
        assert "Python-interface seed manifest" in team28
        assert "normal ELF GUI/CLI" in team28
        assert "outside this documentation MCP server" in team28
        assert team28.count("\n## ") == 28, "Expected 28 Python-interface team28 cards"
        print(f"  3 files + Python-interface team28 OK")

        print("PASSED")
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
