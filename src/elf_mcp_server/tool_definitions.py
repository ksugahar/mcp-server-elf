"""Explicit safety contracts for every public tool.

Every registered tool, including the local product execution bridge, is
classified here instead of inferring safety from its name or prose.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContract:
    name: str
    title: str
    read_only: bool
    destructive: bool
    idempotent: bool
    open_world: bool


READ_ONLY_TOOL_NAMES = (
    "elf_overview",
    "elf_agentic_profile",
    "elf_product_detect",
    "elf_product_case_check",
    "elf_catalog_page",
    "elf_search",
    "elf_read",
    "elf_contract_gate",
    "elf_usage",
    "elf_mcp_readiness",
    "elf_motor_readiness",
    "elf_motor_hybrid_router",
    "elf_motor_mmm_quick_check",
    "elf_help_index",
    "elf_help_search",
    "elf_examples_index",
    "elf_examples_search",
    "elf_examples_get",
    "elf_examples_playbook",
    "elf_sample_decks_index",
    "elf_sample_decks_search",
    "elf_sample_decks_route",
    "elf_local_simulation_handoff",
    "elf_sample_decks_get",
    "elf_sample_decks_playbook",
    "elf_sample_decks_representatives",
    "elf_sample_decks_validation",
    "elf_sample_decks_quality",
    "elf_sample_decks_physics",
    "elf_sample_decks_validation_matrix",
    "elf_sample_decks_observable_contracts",
    "elf_sample_decks_cross_validation",
    "elf_motor_dual_solver_review_packet",
    "elf_sample_decks_duplicates",
    "elf_public_promotion",
    "elf_python_team28",
    "elf_python_interface_design",
    "elf_python_api_manual",
    "elf_python_api_schema",
    "elf_python_motor_spec_lint",
    "elf_python_deck_lint",
    "elf_python_pm_demag_step_lint",
    "elf_python_run_contract",
    "elf_python_run_result_parse",
    "elf_python_run_result_parse_path",
    "elf_python_motor_design_plan",
    "elf_python_motor_sweep_matrix",
    "elf_python_motor_dq_axis_map_plan",
    "elf_python_motor_mtpa_search_plan",
    "elf_python_reluctance_motor_design_plan",
    "elf_python_motor_winding_layout_plan",
    "elf_python_motor_topology_parameter_plan",
    "elf_python_motor_demag_margin_plan",
    "elf_python_motor_drive_cycle_plan",
    "elf_python_motor_optimization_study_plan",
    "elf_python_motor_optimization_loop",
    "elf_python_motor_voltage_field_weakening_plan",
    "elf_python_motor_cogging_ripple_plan",
    "elf_python_motor_airgap_harmonics_nvh_plan",
    "elf_python_motor_thermal_network_plan",
    "elf_python_motor_manufacturing_tolerance_plan",
    "elf_python_motor_material_variation_plan",
    "elf_python_motor_feasibility_study",
    "elf_python_motor_efficiency_map_plan",
    "elf_python_motor_efficiency_map_from_results",
    "elf_python_motor_operating_point_run_queue",
    "elf_python_motor_inverter_pwm_harmonic_plan",
    "elf_python_motor_saturation_inductance_map_plan",
    "elf_python_motor_loss_model_contract",
    "elf_python_motor_torque_speed_envelope",
    "elf_python_induction_slip_sweep_plan",
    "elf_python_motor_observable_contract",
    "elf_python_motor_market_brief",
    "elf_python_motor_design_agent_handoff",
    "elf_python_motor_ngsolve_result_crosscheck",
    "elf_python_motor_drawing_bom_handoff",
    "elf_python_motor_rotor_stress_retention_plan",
    "elf_python_motor_validation_scorecard",
    "elf_python_ngsolve_validation_plan",
    "elf_python_ngsolve_validation_script",
    "elf_python_meg_generation_plan",
    "elf_python_2d_motor_template",
    "elf_python_phase_flux_run_contract_gate",
    "elf_ipm_two_run_ldlq_contract_gate",
    "elf_mesh_solver_pipeline_gate",
    "elf_magnet_model_producer_contract_gate",
    "elf_magnetization_group_handoff_contract_gate",
    "elf_demagnetization_run_contract_gate",
    "elf_transient_induced_current_contract_gate",
    "elf_source_off_relaxation_contract_gate",
    "elf_flux_linkage_inductance_contract_gate",
    "elf_leakage_inductance_contract_gate",
    "elf_emfm_star_power_balance_gate",
    "elf_complex_field_run_contract_gate",
    "elf_force_pair_run_contract_gate",
    "elf_material_force_contrast_contract_gate",
    "elf_force_method_profile_contract_gate",
    "elf_momc_force_triplet_contract_gate",
    "elf_rotating_conductor_periodic_contract_gate",
    "elf_two_winding_frequency_contract_gate",
    "elf_conductive_shield_frequency_contract_gate",
    "elf_project_feature_inventory_contract_gate",
    "elf_nonlinear_magnetic_conductor_validation_gate",
    "elf_recipe_index",
    "elf_recipe_search",
    "elf_recipe_get",
    "elf_plan_workflow",
    "elf_help_get",
    "elf_wiki_index",
    "elf_wiki_search",
    "elf_wiki_get",
    "elf_python_index",
    "elf_python_search",
    "elf_python_get",
)


def _title(name: str) -> str:
    return " ".join(part.upper() if part in {"elf", "mcp", "api", "ipm"} else part.capitalize() for part in name.split("_"))


TOOL_CONTRACTS = {
    name: ToolContract(
        name=name,
        title=_title(name),
        read_only=True,
        destructive=False,
        idempotent=True,
        open_world=name in {
            "elf_python_run_result_parse_path",
            "elf_product_detect",
            "elf_product_case_check",
        },
    )
    for name in READ_ONLY_TOOL_NAMES
}

TOOL_CONTRACTS["elf_product_run"] = ToolContract(
    name="elf_product_run",
    title="ELF Product Run",
    read_only=False,
    destructive=True,
    idempotent=False,
    open_world=True,
)


if len(TOOL_CONTRACTS) != len(READ_ONLY_TOOL_NAMES) + 1:
    raise RuntimeError("duplicate public tool name in explicit contract registry")
