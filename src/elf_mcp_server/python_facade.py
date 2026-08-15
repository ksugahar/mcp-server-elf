"""Public ELF/MAGIC Python facade contracts and dry-run lints.

The functions in this module are deliberately solver-free. They define the
public API vocabulary, validate typed request dictionaries, and lint .mai text
before a user-local backend receives a run request.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from math import atan2, cos, degrees, gcd, hypot, pi, radians, sin
from typing import Any, Mapping, Sequence
import csv
import json
import os
import re

from .guards import positive_float


MOTOR_TYPES = (
    "spm",
    "ipm",
    "pm_assisted_synrm",
    "bldc",
    "line_start_pm",
    "induction",
    "deep_bar_induction",
    "srm",
    "synrm",
    "hysteresis",
    "wound_field_sync",
    "axial_flux_pm",
    "linear_pm",
    "stepper",
    "flux_switching_pm",
    "vernier_pm",
    "transverse_flux_pm",
    "slotless_pm",
    "claw_pole",
    "commutator_dc",
)

PM_MOTOR_TYPES = {
    "spm",
    "ipm",
    "pm_assisted_synrm",
    "bldc",
    "line_start_pm",
    "flux_switching_pm",
    "vernier_pm",
    "transverse_flux_pm",
    "slotless_pm",
    "axial_flux_pm",
    "linear_pm",
    "stepper",
}

RELUCTANCE_MOTOR_TYPES = {
    "ipm",
    "pm_assisted_synrm",
    "synrm",
    "srm",
    "flux_switching_pm",
    "vernier_pm",
}

INDUCTION_MOTOR_TYPES = {
    "induction",
    "deep_bar_induction",
    "line_start_pm",
}

STUDY_TYPES = (
    "static_flux_linkage",
    "static_torque_angle",
    "back_emf_speed_sweep",
    "dq_inductance",
    "force_gap_sweep",
    "cogging_torque",
    "induction_slip_loss",
    "ac_loss_frequency_sweep",
    "thermal_loss_export",
)

OBSERVABLES = (
    "flux_linkage",
    "back_emf_constant",
    "torque",
    "torque_ripple",
    "cogging_torque",
    "ld_lq",
    "field_probe",
    "force",
    "loss_proxy",
    "convergence_status",
)

RUN_MODES = (
    "copy_public_deck_and_run",
    "mutate_public_deck_then_run",
    "generate_new_deck_from_recipe_then_run",
    "dry_run_validate_inputs_only",
)


OBSERVABLE_MARKERS = {
    "flux_linkage": ("SOL FIXA", "FLUM"),
    "back_emf_constant": ("SOL FIXA", "FLUM"),
    "ld_lq": ("SOL FIXA", "FLUM"),
    "field_probe": ("SOL FIEL",),
    "torque": ("SOL FORC|SOL FORT|SOL FIXB|FLUM",),
    "torque_ripple": ("SOL FORC|SOL FORT|SOL FIXB|FLUM",),
    "cogging_torque": ("SOL FORC|SOL FORT|SOL FIXB|FLUM",),
    "force": ("SOL FORC|SOL FORT|SOL FIXB",),
    "loss_proxy": ("OHM2|FREQ|SOL MOMC",),
}


MOTOR_DEFAULT_OBSERVABLES = {
    "spm": ("flux_linkage", "back_emf_constant", "torque", "cogging_torque"),
    "ipm": ("flux_linkage", "torque", "ld_lq", "back_emf_constant"),
    "pm_assisted_synrm": ("flux_linkage", "torque", "ld_lq", "back_emf_constant"),
    "bldc": ("back_emf_constant", "torque", "torque_ripple", "cogging_torque"),
    "line_start_pm": ("flux_linkage", "loss_proxy", "torque", "back_emf_constant"),
    "induction": ("flux_linkage", "loss_proxy", "torque"),
    "deep_bar_induction": ("flux_linkage", "loss_proxy", "torque"),
    "srm": ("flux_linkage", "torque", "ld_lq"),
    "synrm": ("flux_linkage", "torque", "ld_lq"),
    "hysteresis": ("torque", "loss_proxy", "field_probe"),
    "wound_field_sync": ("flux_linkage", "torque", "field_probe"),
    "axial_flux_pm": ("flux_linkage", "back_emf_constant", "torque"),
    "linear_pm": ("force", "flux_linkage", "field_probe"),
    "stepper": ("cogging_torque", "torque", "flux_linkage"),
    "flux_switching_pm": ("flux_linkage", "back_emf_constant", "torque", "torque_ripple"),
    "vernier_pm": ("flux_linkage", "back_emf_constant", "torque", "torque_ripple"),
    "transverse_flux_pm": ("flux_linkage", "back_emf_constant", "torque", "field_probe"),
    "slotless_pm": ("flux_linkage", "back_emf_constant", "torque", "field_probe"),
    "claw_pole": ("flux_linkage", "torque", "field_probe", "loss_proxy"),
    "commutator_dc": ("torque", "loss_proxy", "field_probe", "convergence_status"),
}

MOTOR_DESIGN_VARIABLES: dict[str, tuple[dict[str, Any], ...]] = {
    "spm": (
        {"name": "magnet_arc_fraction", "unit": "1", "default": 0.75, "range": (0.55, 0.90), "affects": ("back_emf_constant", "cogging_torque", "torque_ripple")},
        {"name": "magnet_thickness_m", "unit": "m", "default": 0.003, "range": (0.0015, 0.006), "affects": ("flux_linkage", "back_emf_constant", "magnet_volume")},
        {"name": "airgap_m", "unit": "m", "default": 0.001, "range": (0.0006, 0.0018), "affects": ("torque", "cogging_torque", "manufacturability")},
        {"name": "turns_per_phase", "unit": "turn", "default": 50.0, "range": (20.0, 90.0), "affects": ("back_emf_constant", "copper_loss_proxy")},
        {"name": "skew_fraction", "unit": "slot_pitch", "default": 0.0, "range": (0.0, 1.0), "affects": ("cogging_torque", "torque_ripple", "average_torque")},
    ),
    "ipm": (
        {"name": "magnet_v_angle_deg", "unit": "deg", "default": 120.0, "range": (90.0, 150.0), "affects": ("ld_lq", "reluctance_torque", "bridge_stress_proxy")},
        {"name": "bridge_thickness_m", "unit": "m", "default": 0.0012, "range": (0.0006, 0.0025), "affects": ("leakage_flux", "mechanical_margin_proxy")},
        {"name": "barrier_depth_fraction", "unit": "1", "default": 0.45, "range": (0.25, 0.70), "affects": ("ld_lq", "torque_ripple")},
        {"name": "current_angle_deg", "unit": "deg_e", "default": 35.0, "range": (0.0, 70.0), "affects": ("torque", "mtpa", "field_weakening")},
        {"name": "turns_per_phase", "unit": "turn", "default": 50.0, "range": (20.0, 90.0), "affects": ("flux_linkage", "back_emf_constant")},
    ),
    "pm_assisted_synrm": (
        {"name": "barrier_count", "unit": "count", "default": 3, "range": (1, 5), "affects": ("ld_lq", "reluctance_torque")},
        {"name": "assist_magnet_volume_fraction", "unit": "1", "default": 0.18, "range": (0.02, 0.35), "affects": ("back_emf_constant", "demag_margin", "material_reduction")},
        {"name": "barrier_arc_fraction", "unit": "1", "default": 0.55, "range": (0.25, 0.85), "affects": ("saliency", "torque_ripple")},
        {"name": "current_angle_deg", "unit": "deg_e", "default": 50.0, "range": (0.0, 85.0), "affects": ("mtpa", "field_weakening")},
    ),
    "bldc": (
        {"name": "magnet_arc_fraction", "unit": "1", "default": 0.80, "range": (0.55, 0.95), "affects": ("trapezoidal_back_emf", "cogging_torque")},
        {"name": "commutation_advance_deg", "unit": "deg_e", "default": 0.0, "range": (-20.0, 30.0), "affects": ("six_step_torque", "torque_ripple")},
        {"name": "phase_conduction_deg", "unit": "deg_e", "default": 120.0, "range": (90.0, 150.0), "affects": ("torque", "copper_loss_proxy")},
        {"name": "skew_fraction", "unit": "slot_pitch", "default": 0.0, "range": (0.0, 1.0), "affects": ("cogging_torque", "torque_ripple")},
    ),
    "line_start_pm": (
        {"name": "cage_bar_depth_m", "unit": "m", "default": 0.006, "range": (0.002, 0.014), "affects": ("starting_torque", "rotor_loss_proxy")},
        {"name": "pm_flux_fraction", "unit": "1", "default": 0.45, "range": (0.10, 0.80), "affects": ("pull_in_torque", "back_emf_constant")},
        {"name": "synchronizing_torque_angle_deg", "unit": "deg_e", "default": 25.0, "range": (5.0, 60.0), "affects": ("pull_in_margin", "torque_ripple")},
        {"name": "slip_hz", "unit": "Hz", "default": 5.0, "range": (0.5, 25.0), "affects": ("acceleration", "cage_loss_proxy")},
    ),
    "induction": (
        {"name": "slip_hz", "unit": "Hz", "default": 5.0, "range": (0.5, 20.0), "affects": ("torque", "rotor_loss_proxy")},
        {"name": "rotor_bar_depth_m", "unit": "m", "default": 0.008, "range": (0.003, 0.018), "affects": ("starting_torque", "skin_effect_proxy")},
        {"name": "bar_conductivity_scale", "unit": "1", "default": 1.0, "range": (0.4, 1.4), "affects": ("rotor_loss_proxy", "pullout_torque")},
        {"name": "stator_current_a_peak", "unit": "A", "default": 10.0, "range": (2.0, 30.0), "affects": ("torque", "copper_loss_proxy")},
        {"name": "frequency_hz", "unit": "Hz", "default": 50.0, "range": (10.0, 400.0), "affects": ("skin_effect_proxy", "loss_proxy")},
    ),
    "deep_bar_induction": (
        {"name": "outer_bar_depth_m", "unit": "m", "default": 0.004, "range": (0.0015, 0.010), "affects": ("starting_torque", "skin_effect_proxy")},
        {"name": "inner_bar_depth_m", "unit": "m", "default": 0.012, "range": (0.004, 0.030), "affects": ("rated_efficiency", "rotor_loss_proxy")},
        {"name": "bar_neck_width_fraction", "unit": "1", "default": 0.35, "range": (0.15, 0.70), "affects": ("leakage_reactance", "breakdown_torque")},
        {"name": "slip_hz", "unit": "Hz", "default": 7.5, "range": (0.5, 35.0), "affects": ("torque", "rotor_loss_proxy")},
    ),
    "srm": (
        {"name": "turn_on_deg", "unit": "deg_e", "default": -10.0, "range": (-30.0, 5.0), "affects": ("average_torque", "torque_ripple")},
        {"name": "turn_off_deg", "unit": "deg_e", "default": 25.0, "range": (5.0, 50.0), "affects": ("average_torque", "negative_torque")},
        {"name": "rotor_pole_arc_fraction", "unit": "1", "default": 0.45, "range": (0.25, 0.70), "affects": ("aligned_inductance", "torque_ripple")},
        {"name": "airgap_m", "unit": "m", "default": 0.001, "range": (0.0005, 0.002), "affects": ("aligned_inductance", "force_margin")},
    ),
    "synrm": (
        {"name": "barrier_count", "unit": "count", "default": 3, "range": (1, 5), "affects": ("ld_lq", "torque_ripple")},
        {"name": "barrier_arc_fraction", "unit": "1", "default": 0.55, "range": (0.25, 0.80), "affects": ("ld_lq", "mechanical_margin_proxy")},
        {"name": "current_angle_deg", "unit": "deg_e", "default": 45.0, "range": (10.0, 80.0), "affects": ("reluctance_torque", "mtpa")},
        {"name": "airgap_m", "unit": "m", "default": 0.001, "range": (0.0006, 0.0018), "affects": ("torque", "power_factor_proxy")},
    ),
    "hysteresis": (
        {"name": "frequency_hz", "unit": "Hz", "default": 50.0, "range": (5.0, 400.0), "affects": ("loss_proxy", "synchronous_torque_proxy")},
        {"name": "hysteresis_loss_tangent", "unit": "1", "default": 0.08, "range": (0.01, 0.25), "affects": ("loss_proxy", "torque")},
        {"name": "rotor_shell_thickness_m", "unit": "m", "default": 0.003, "range": (0.001, 0.010), "affects": ("loss_proxy", "thermal_margin_proxy")},
        {"name": "airgap_m", "unit": "m", "default": 0.001, "range": (0.0006, 0.002), "affects": ("field_probe", "torque")},
    ),
    "wound_field_sync": (
        {"name": "field_current_a", "unit": "A", "default": 2.0, "range": (0.0, 12.0), "affects": ("flux_linkage", "voltage_regulation")},
        {"name": "field_turns", "unit": "turn", "default": 80.0, "range": (20.0, 200.0), "affects": ("field_loss_proxy", "thermal")},
        {"name": "salient_pole_arc_fraction", "unit": "1", "default": 0.55, "range": (0.25, 0.85), "affects": ("torque", "airgap_harmonics")},
        {"name": "damper_bar_conductivity_scale", "unit": "1", "default": 1.0, "range": (0.2, 1.5), "affects": ("transient_damping", "loss_proxy")},
    ),
    "axial_flux_pm": (
        {"name": "magnet_arc_fraction", "unit": "1", "default": 0.75, "range": (0.50, 0.95), "affects": ("back_emf_constant", "cogging_torque")},
        {"name": "airgap_m", "unit": "m", "default": 0.0012, "range": (0.0005, 0.003), "affects": ("torque", "manufacturing")},
        {"name": "disc_radius_ratio", "unit": "1", "default": 0.55, "range": (0.25, 0.85), "affects": ("torque_density", "mass")},
        {"name": "magnet_thickness_m", "unit": "m", "default": 0.004, "range": (0.0015, 0.010), "affects": ("flux_linkage", "demag_margin")},
    ),
    "linear_pm": (
        {"name": "pole_pitch_m", "unit": "m", "default": 0.024, "range": (0.006, 0.080), "affects": ("force", "back_emf_constant")},
        {"name": "magnet_height_m", "unit": "m", "default": 0.004, "range": (0.001, 0.012), "affects": ("flux_linkage", "normal_force")},
        {"name": "translator_gap_m", "unit": "m", "default": 0.001, "range": (0.0004, 0.003), "affects": ("force", "manufacturing")},
        {"name": "coil_pitch_fraction", "unit": "1", "default": 0.85, "range": (0.45, 1.0), "affects": ("force_ripple", "copper_loss_proxy")},
    ),
    "stepper": (
        {"name": "tooth_count", "unit": "count", "default": 50, "range": (12, 200), "affects": ("step_angle", "detent_torque")},
        {"name": "pm_flux_scale", "unit": "1", "default": 1.0, "range": (0.3, 1.5), "affects": ("holding_torque", "demag_margin")},
        {"name": "tooth_pitch_fraction", "unit": "1", "default": 0.50, "range": (0.25, 0.75), "affects": ("torque_ripple", "detent")},
        {"name": "phase_current_a_peak", "unit": "A", "default": 2.0, "range": (0.1, 15.0), "affects": ("holding_torque", "copper_loss_proxy")},
    ),
    "flux_switching_pm": (
        {"name": "stator_pm_arc_fraction", "unit": "1", "default": 0.45, "range": (0.20, 0.70), "affects": ("flux_linkage", "torque_ripple")},
        {"name": "rotor_pole_arc_fraction", "unit": "1", "default": 0.50, "range": (0.25, 0.75), "affects": ("switching_flux", "cogging_torque")},
        {"name": "slot_opening_fraction", "unit": "1", "default": 0.22, "range": (0.05, 0.45), "affects": ("leakage_flux", "manufacturability")},
        {"name": "current_advance_deg", "unit": "deg_e", "default": 15.0, "range": (-20.0, 60.0), "affects": ("torque", "mtpa")},
    ),
    "vernier_pm": (
        {"name": "modulation_pole_count", "unit": "count", "default": 18, "range": (6, 72), "affects": ("gear_ratio", "torque_density")},
        {"name": "pm_pole_pair_count", "unit": "count", "default": 10, "range": (2, 40), "affects": ("flux_modulation", "back_emf_constant")},
        {"name": "modulation_tooth_width_fraction", "unit": "1", "default": 0.45, "range": (0.20, 0.75), "affects": ("airgap_harmonics", "torque_ripple")},
        {"name": "magnet_arc_fraction", "unit": "1", "default": 0.75, "range": (0.45, 0.95), "affects": ("torque", "cogging_torque")},
    ),
    "transverse_flux_pm": (
        {"name": "module_count", "unit": "count", "default": 3, "range": (1, 12), "affects": ("torque_density", "3d_flux_path")},
        {"name": "claw_tooth_overlap_fraction", "unit": "1", "default": 0.55, "range": (0.20, 0.85), "affects": ("leakage_flux", "torque")},
        {"name": "magnet_thickness_m", "unit": "m", "default": 0.004, "range": (0.0015, 0.010), "affects": ("flux_linkage", "demag_margin")},
        {"name": "axial_gap_m", "unit": "m", "default": 0.001, "range": (0.0005, 0.003), "affects": ("torque", "manufacturing")},
    ),
    "slotless_pm": (
        {"name": "airgap_m", "unit": "m", "default": 0.002, "range": (0.0008, 0.006), "affects": ("torque", "cogging_torque")},
        {"name": "coil_span_fraction", "unit": "1", "default": 0.80, "range": (0.45, 0.98), "affects": ("winding_factor", "copper_loss_proxy")},
        {"name": "magnet_arc_fraction", "unit": "1", "default": 0.85, "range": (0.55, 0.98), "affects": ("back_emf_constant", "ripple")},
        {"name": "support_tube_thickness_m", "unit": "m", "default": 0.001, "range": (0.0002, 0.003), "affects": ("thermal", "mechanical_gap")},
    ),
    "claw_pole": (
        {"name": "field_current_a", "unit": "A", "default": 2.0, "range": (0.0, 10.0), "affects": ("flux_linkage", "voltage_regulation")},
        {"name": "claw_overlap_fraction", "unit": "1", "default": 0.55, "range": (0.25, 0.85), "affects": ("leakage_flux", "torque_ripple")},
        {"name": "pole_tip_taper_fraction", "unit": "1", "default": 0.25, "range": (0.0, 0.60), "affects": ("airgap_harmonics", "noise")},
        {"name": "rotor_field_turns", "unit": "turn", "default": 80.0, "range": (20.0, 200.0), "affects": ("field_loss_proxy", "thermal")},
    ),
    "commutator_dc": (
        {"name": "brush_advance_deg", "unit": "deg_e", "default": 0.0, "range": (-20.0, 30.0), "affects": ("commutation", "torque_ripple")},
        {"name": "series_field_turns", "unit": "turn", "default": 40.0, "range": (5.0, 120.0), "affects": ("starting_torque", "field_loss_proxy")},
        {"name": "armature_current_a", "unit": "A", "default": 10.0, "range": (0.5, 80.0), "affects": ("torque", "copper_loss_proxy")},
        {"name": "supply_mode_ac_fraction", "unit": "1", "default": 0.0, "range": (0.0, 1.0), "affects": ("universal_motor_loss", "reactive_voltage_drop")},
    ),
}

MOTOR_DESIGN_OBJECTIVES = {
    "torque_density": {
        "primary_observables": ("torque", "flux_linkage"),
        "secondary_observables": ("torque_ripple", "loss_proxy"),
        "acceptance": "positive torque trend with bounded ripple and no convergence warnings",
    },
    "back_emf_target": {
        "primary_observables": ("back_emf_constant", "flux_linkage"),
        "secondary_observables": ("cogging_torque", "torque_ripple"),
        "acceptance": "target back-EMF within tolerance while keeping cogging/ripple labels acceptable",
    },
    "efficiency_map": {
        "primary_observables": ("torque", "loss_proxy"),
        "secondary_observables": ("field_probe", "convergence_status"),
        "acceptance": "loss trend is monotone/plausible over current, speed, frequency, or slip sweeps",
    },
    "ripple_reduction": {
        "primary_observables": ("torque_ripple", "cogging_torque"),
        "secondary_observables": ("torque", "flux_linkage"),
        "acceptance": "ripple decreases without unacceptable average torque loss",
    },
    "material_reduction": {
        "primary_observables": ("torque", "back_emf_constant"),
        "secondary_observables": ("flux_linkage", "field_probe"),
        "acceptance": "magnet or copper reduction keeps target observable above threshold",
    },
}

TARGET_MARKET_PROFILES: dict[str, dict[str, Any]] = {
    "robot_drone": {
        "display": "Robotics / drone drive motor",
        "default_motor_type": "spm",
        "default_rotor_topology": "outer_rotor",
        "spec_fields": [
            "continuous_torque_nm",
            "peak_torque_nm",
            "base_speed_rpm",
            "max_speed_rpm",
            "dc_bus_v",
            "phase_current_limit_a_peak",
            "outer_diameter_mm",
            "stack_length_mm",
            "mass_limit_g",
            "cooling_mode",
            "acoustic_priority",
            "manufacturing_volume",
        ],
        "design_priorities": [
            "torque_density",
            "low_cogging",
            "low_ripple",
            "thermal_margin",
            "manufacturable_magnet_and_slot_geometry",
        ],
        "preferred_topologies": ["outer_rotor_spm", "inner_rotor_spm"],
    },
    "industrial_servo": {
        "display": "Industrial servo motor",
        "default_motor_type": "ipm",
        "default_rotor_topology": "inner_rotor",
        "spec_fields": [
            "rated_torque_nm",
            "peak_torque_nm",
            "rated_speed_rpm",
            "max_speed_rpm",
            "dc_bus_v",
            "encoder_space_mm",
            "thermal_class",
            "torque_ripple_limit_percent",
        ],
        "design_priorities": [
            "torque_density",
            "field_weakening",
            "low_ripple",
            "thermal_margin",
        ],
        "preferred_topologies": ["inner_rotor_ipm", "inner_rotor_spm"],
    },
}

DESIGN_AGENT_DELIVERABLES = [
    {
        "name": "spec_intake",
        "public": True,
        "description": "Normalized user requirements with explicit units and missing-field questions.",
    },
    {
        "name": "motor_spec",
        "public": True,
        "description": "MotorSpec plus design variables, objectives, studies, and requested observables.",
    },
    {
        "name": "geometry_template",
        "public": True,
        "description": "2D radial/slot/magnet template or 3D mesh-generation plan.",
    },
    {
        "name": "deck_bundle",
        "public": True,
        "description": "Public .mai/.meg seed or generated input-deck contract with lint status.",
    },
    {
        "name": "local_run_contract",
        "public": True,
        "description": "RunRequest contract for a user-local product backend.",
    },
    {
        "name": "normalized_result",
        "public": False,
        "description": "RunResult from a local/private backend; raw product outputs stay local.",
    },
    {
        "name": "manufacturing_handoff",
        "public": True,
        "description": "Drawing/BOM/procurement intent: material roles, dimensions, magnet/coil notes, and validation labels.",
    },
]

FEASIBILITY_LANES: list[dict[str, Any]] = [
    {
        "lane": "electromagnetic_performance",
        "question": "Does the motor meet torque, speed, voltage, flux-linkage, and efficiency targets?",
        "observables": ["torque", "back_emf_constant", "flux_linkage", "ld_lq", "loss_proxy"],
        "mcp_support": [
            "motor design plan",
            "sweep matrix",
            "observable contract",
            "local ELF/MAGIC backend contract",
            "independent AGE/MMM validation routing",
        ],
    },
    {
        "lane": "thermal_feasibility",
        "question": "Can losses and duty cycle be cooled in the requested package?",
        "observables": ["loss_proxy", "current_density_proxy", "duty_cycle", "cooling_mode"],
        "mcp_support": [
            "loss-oriented observable contract",
            "efficiency-map objective",
            "required NGSolve thermal validation after RunResult parsing",
        ],
    },
    {
        "lane": "nvh_feasibility",
        "question": "Are cogging, torque ripple, slot/pole harmonics, and magnetic force orders acceptable?",
        "observables": ["cogging_torque", "torque_ripple", "airgap_harmonics", "force_order_proxy"],
        "mcp_support": [
            "ripple-reduction objective",
            "torque-angle sweep",
            "required NGSolve harmonic/structural-acoustic validation after electromagnetic observables are parsed",
        ],
    },
    {
        "lane": "mechanical_stress_feasibility",
        "question": "Can rotor, magnet retention, bridges, sleeve, shaft, and hub survive speed and assembly loads?",
        "observables": ["max_speed_rpm", "rotor_radius", "magnet_retention_proxy", "bridge_stress_proxy"],
        "mcp_support": [
            "spec intake",
            "manufacturing handoff",
            "required NGSolve mechanical stress validation for rotor, bridge, sleeve, and magnet retention risks",
        ],
    },
    {
        "lane": "manufacturing_and_supply",
        "question": "Can materials, magnets, laminations, winding, and tolerances be procured and built in small lots?",
        "observables": ["material_role", "magnet_grade", "lamination_grade", "wire_gauge", "tolerance_stack"],
        "mcp_support": [
            "drawing/BOM/prototype handoff",
            "material variation plan",
            "public validation labels attached to design intent",
        ],
    },
]

MATERIAL_VARIATION_CATALOG: dict[str, tuple[dict[str, Any], ...]] = {
    "magnet": (
        {"name": "br_t", "unit": "T", "default": 1.2, "range": (0.9, 1.45), "affects": ("back_emf_constant", "torque", "demag_margin_proxy")},
        {"name": "recoil_mu_r", "unit": "1", "default": 1.05, "range": (1.02, 1.20), "affects": ("flux_linkage", "field_probe")},
        {"name": "temperature_coefficient_pct_per_k", "unit": "%/K", "default": -0.11, "range": (-0.15, -0.08), "affects": ("thermal_margin", "back_emf_hot")},
    ),
    "electrical_steel": (
        {"name": "bh_knee_flux_density_t", "unit": "T", "default": 1.6, "range": (1.35, 1.9), "affects": ("saturation", "torque", "loss_proxy")},
        {"name": "lamination_stack_factor", "unit": "1", "default": 0.95, "range": (0.88, 0.98), "affects": ("effective_area", "loss_proxy")},
        {"name": "core_loss_scale", "unit": "1", "default": 1.0, "range": (0.5, 2.0), "affects": ("thermal_feasibility", "efficiency_map")},
    ),
    "conductor": (
        {"name": "conductivity_scale", "unit": "1", "default": 1.0, "range": (0.55, 1.05), "affects": ("copper_loss_proxy", "thermal_margin")},
        {"name": "slot_fill_factor", "unit": "1", "default": 0.45, "range": (0.25, 0.65), "affects": ("current_density", "manufacturability")},
        {"name": "turns_per_phase", "unit": "turn", "default": 50.0, "range": (20.0, 90.0), "affects": ("back_emf_constant", "resistance_proxy")},
    ),
}

LICENSE_GOVERNANCE_TOPICS = [
    {
        "topic": "product_license_boundary",
        "rule": (
            "A user-local product license enables local backend execution. "
            "The public MCP package does not grant, sublicense, redistribute, "
            "or emulate that product license."
        ),
    },
    {
        "topic": "mcp_server_rights",
        "rule": (
            "The public MCP server license covers public code, schemas, docs, "
            "and public input-deck contracts only. It does not change the "
            "rights of product binaries, product DLLs, or private run outputs."
        ),
    },
    {
        "topic": "joint_research_governance",
        "rule": (
            "Before a feasibility or prototype business uses a licensed backend, "
            "the parties should agree who may run the backend, who owns generated "
            "design data, which logs stay private, and which scrubbed knowledge "
            "may return to public MCP docs."
        ),
    },
    {
        "topic": "customer_workflow",
        "rule": (
            "End users can provide specifications and receive drawings, decks, "
            "validation labels, and prototype handoff without directly operating "
            "the analysis software."
        ),
    },
]


@dataclass(frozen=True)
class MaterialSpec:
    name: str
    role: str
    model: str = "linear"
    mu_r: float | None = None
    conductivity_s_per_m: float | None = None
    br_t: float | None = None


@dataclass(frozen=True)
class WindingSpec:
    name: str
    phase: str
    turns: float
    current_a_peak: float = 0.0
    slot_group: str = ""


@dataclass(frozen=True)
class StudySpec:
    name: str
    observables: tuple[str, ...] = ("flux_linkage",)
    sweep_parameter: str = ""
    sweep_values: tuple[float, ...] = ()


@dataclass(frozen=True)
class MotorSpec:
    motor_type: str
    pole_pairs: int
    stator_slots: int
    rotor_topology: str
    airgap_m: float
    stack_length_m: float
    materials: tuple[MaterialSpec, ...]
    windings: tuple[WindingSpec, ...]
    studies: tuple[StudySpec, ...]


@dataclass(frozen=True)
class DeckBundle:
    case_id: str
    mai_text: str
    meg_text: str = ""
    source_public_deck_paths: tuple[str, ...] = ()
    validation_label: str = ""
    requested_observables: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunRequest:
    goal: str
    run_mode: str
    deck: DeckBundle
    requested_observables: tuple[str, ...]
    timeout_seconds: int = 300
    keep_outputs: bool = True
    privacy_policy: str = "keep_raw_outputs_user_local"


@dataclass(frozen=True)
class RunResult:
    case_id: str
    status: str
    generated_files: tuple[str, ...] = ()
    parsed_observables: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    validation_labels: tuple[str, ...] = ()


def _issue(severity: str, field: str, message: str) -> dict[str, str]:
    return {"severity": severity, "field": field, "message": message}


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _positive_number(spec: Mapping[str, Any], field_name: str) -> bool:
    try:
        return float(spec.get(field_name, 0.0)) > 0.0
    except (TypeError, ValueError):
        return False


def build_motor_spec_template(motor_type: str = "spm") -> dict[str, Any]:
    """Return a JSON-compatible MotorSpec template."""
    family = motor_type.strip().lower() or "spm"
    if family not in MOTOR_TYPES:
        family = "spm"
    observables = MOTOR_DEFAULT_OBSERVABLES.get(family, MOTOR_DEFAULT_OBSERVABLES["spm"])
    study_name = "induction_slip_loss" if family in INDUCTION_MOTOR_TYPES else "static_flux_linkage"
    if family in PM_MOTOR_TYPES:
        study_name = "back_emf_speed_sweep"
    if family in {"srm", "synrm", "pm_assisted_synrm", "stepper", "commutator_dc"}:
        study_name = "static_torque_angle"
    spec = MotorSpec(
        motor_type=family,
        pole_pairs=4,
        stator_slots=48,
        rotor_topology=f"{family}_reference_topology",
        airgap_m=1.0e-3,
        stack_length_m=0.05,
        materials=(
            MaterialSpec(name="stator_core", role="laminated_iron", model="bh_curve", mu_r=1000.0),
            MaterialSpec(name="rotor_core", role="rotor_iron", model="bh_curve", mu_r=1000.0),
            MaterialSpec(name="airgap", role="air", model="linear", mu_r=1.0),
        ),
        windings=(
            WindingSpec(name="phase_a", phase="A", turns=50.0, current_a_peak=10.0),
            WindingSpec(name="phase_b", phase="B", turns=50.0, current_a_peak=-5.0),
            WindingSpec(name="phase_c", phase="C", turns=50.0, current_a_peak=-5.0),
        ),
        studies=(StudySpec(name=study_name, observables=tuple(observables)),),
    )
    data = asdict(spec)
    data["recommended_observables"] = list(observables)
    data["design_variables"] = list(MOTOR_DESIGN_VARIABLES.get(family, MOTOR_DESIGN_VARIABLES["spm"]))
    return data


def python_api_schema() -> dict[str, Any]:
    """Return the public facade vocabulary as a JSON-compatible schema."""
    return {
        "schema_version": "elf-python-facade-schema/v1",
        "policy": {
            "product_python_required": False,
            "product_python_role": "reference",
            "vendor_dll_mutable_by_public_package": False,
            "public_facade_can_extend_api": True,
            "solver_execution": "user_local_backend_only",
        },
        "enums": {
            "motor_types": list(MOTOR_TYPES),
            "study_types": list(STUDY_TYPES),
            "observables": list(OBSERVABLES),
            "run_modes": list(RUN_MODES),
            "design_objectives": list(MOTOR_DESIGN_OBJECTIVES),
        },
        "objects": {
            "DesignVariable": [
                "name",
                "unit",
                "default",
                "range",
                "affects",
            ],
            "MotorSpec": [
                "motor_type",
                "pole_pairs",
                "stator_slots",
                "rotor_topology",
                "airgap_m",
                "stack_length_m",
                "materials",
                "windings",
                "studies",
            ],
            "DeckBundle": [
                "case_id",
                "mai_text",
                "meg_text",
                "source_public_deck_paths",
                "validation_label",
                "requested_observables",
            ],
            "RunRequest": [
                "goal",
                "run_mode",
                "deck",
                "requested_observables",
                "timeout_seconds",
                "keep_outputs",
                "privacy_policy",
            ],
            "RunResult": [
                "case_id",
                "status",
                "generated_files",
                "parsed_observables",
                "warnings",
                "validation_labels",
            ],
            "RunResultParser": [
                "case_id",
                "status",
                "parsed_observables",
                "warnings",
                "missing_requested_observables",
            ],
            "RunResultPathParser": [
                "source_label",
                "files_scanned",
                "parsed_results",
                "combined_observables",
                "warnings",
            ],
            "EfficiencyMapResult": [
                "map_axes",
                "eta_grid",
                "total_loss_w_grid",
                "torque_error_nm_grid",
                "best_efficiency_point",
                "coverage",
                "quality_gate_results",
            ],
            "OptimizationLoop": [
                "ranked_candidates",
                "best_candidate",
                "next_run_rows",
                "promotion_rules",
            ],
            "NGSolveResultCrosscheck": [
                "overall_status",
                "run_result_status",
                "lane_checks",
                "next_actions",
            ],
            "DrawingBOMHandoff": [
                "drawing_views",
                "key_dimensions",
                "bom",
                "winding_summary",
                "quality_gates",
            ],
            "OperatingPointRunQueue": [
                "run_rows",
                "requested_observables",
                "parser_keys",
                "quality_gates",
            ],
            "InverterPWMHarmonicPlan": [
                "modulation",
                "switching_frequency_hz",
                "harmonic_rows",
                "required_observables",
                "validation_routes",
            ],
            "SaturationInductanceMapPlan": [
                "current_axis_a_peak",
                "angle_axis_deg_from_q_axis",
                "map_rows",
                "parser_keys",
                "quality_gates",
            ],
            "RotorStressRetentionPlan": [
                "max_speed_rpm",
                "tip_speed_m_s",
                "hoop_stress_mpa_proxy",
                "retention_margin_proxy",
                "ngsolve_follow_up",
            ],
            "MotorValidationScorecard": [
                "overall_status",
                "score",
                "gate_results",
                "promotion_decision",
                "next_actions",
            ],
            "MotorDesignPlan": [
                "goal",
                "motor_type",
                "objective",
                "design_variables",
                "primary_observables",
                "recommended_studies",
                "validation_gates",
            ],
            "SweepMatrix": [
                "active_variables",
                "observables",
                "rows",
                "postprocess_rules",
            ],
            "ObservableContract": [
                "observables",
                "elf_markers",
                "run_result_keys",
                "parser_observable_keys",
                "validation_checks",
                "age_targets",
            ],
        },
    }


def validate_motor_spec_dict(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a MotorSpec-like mapping without needing product code."""
    issues: list[dict[str, str]] = []
    required = python_api_schema()["objects"]["MotorSpec"]
    for field_name in required:
        if field_name not in spec:
            issues.append(_issue("ERROR", field_name, "missing required MotorSpec field"))

    motor_type = str(spec.get("motor_type", "")).strip().lower()
    if motor_type and motor_type not in MOTOR_TYPES:
        issues.append(_issue("ERROR", "motor_type", f"unknown motor type {motor_type!r}"))
    for field_name in ("pole_pairs", "stator_slots", "airgap_m", "stack_length_m"):
        if field_name in spec and not _positive_number(spec, field_name):
            issues.append(_issue("ERROR", field_name, "must be a positive number"))

    studies = _as_sequence(spec.get("studies"))
    if not studies:
        issues.append(_issue("ERROR", "studies", "at least one StudySpec is required"))
    for index, study in enumerate(studies):
        if not isinstance(study, Mapping):
            issues.append(_issue("ERROR", f"studies[{index}]", "study must be an object"))
            continue
        name = str(study.get("name", "")).strip()
        if name and name not in STUDY_TYPES:
            issues.append(_issue("WARN", f"studies[{index}].name", "study is not in the public vocabulary"))
        for obs in _as_sequence(study.get("observables")):
            obs_name = str(obs).strip()
            if obs_name and obs_name not in OBSERVABLES:
                issues.append(
                    _issue("WARN", f"studies[{index}].observables", f"unknown observable {obs_name!r}")
                )

    recommended = MOTOR_DEFAULT_OBSERVABLES.get(motor_type, ())
    return {
        "schema_version": "elf-python-motor-spec-lint/v1",
        "status": "FAIL" if any(i["severity"] == "ERROR" for i in issues) else "PASS",
        "motor_type": motor_type or "unspecified",
        "recommended_observables": list(recommended),
        "issues": issues,
    }


def _active_upper_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("*"):
            continue
        lines.append(re.sub(r"\s+", " ", stripped.upper()))
    return lines


def lint_mai_text(mai_text: str, requested_observables: Sequence[str] = ()) -> dict[str, Any]:
    """Dry-run lint public .mai text against requested observables."""
    upper_text = "\n".join(_active_upper_lines(mai_text))
    issues: list[dict[str, str]] = []
    if "USE MAGIC" not in upper_text:
        issues.append(_issue("ERROR", "mai_text", "expected USE MAGIC for motor/product magnetics deck"))
    if not re.search(r"(^|\n)PRE\b", upper_text):
        issues.append(_issue("ERROR", "mai_text", "missing PRE block"))
    if not re.search(r"(^|\n)SOL MOM[EC]\b", upper_text):
        issues.append(_issue("ERROR", "mai_text", "missing primary SOL MOME or SOL MOMC block"))
    if "DMEG" not in upper_text:
        issues.append(_issue("WARN", "mai_text", "DMEG marker not found; generated .meg/.mag linkage may be unclear"))

    normalized_observables = [str(o).strip().lower() for o in requested_observables if str(o).strip()]
    for observable in normalized_observables:
        if observable not in OBSERVABLES:
            issues.append(_issue("WARN", "requested_observables", f"unknown observable {observable!r}"))
            continue
        markers = OBSERVABLE_MARKERS.get(observable, ())
        for pattern in markers:
            if not re.search(pattern, upper_text):
                issues.append(
                    _issue(
                        "WARN",
                        observable,
                        f"observable may need marker matching {pattern!r}",
                    )
                )

    return {
        "schema_version": "elf-python-mai-lint/v1",
        "status": "FAIL" if any(i["severity"] == "ERROR" for i in issues) else "PASS",
        "requested_observables": normalized_observables,
        "detected": {
            "sol_blocks": re.findall(r"(^|\n)SOL\s+([A-Z0-9]+)", upper_text),
            "has_flum": "FLUM" in upper_text,
            "has_field_output": "SOL FIEL" in upper_text,
            "has_force_output": any(token in upper_text for token in ("SOL FORC", "SOL FORT", "SOL FIXB")),
            "has_ac_markers": any(token in upper_text for token in ("FREQ", "OHM2", "SOL MOMC")),
            "has_hbrm": "HBRM" in upper_text,
            "has_hbcn": "HBCN" in upper_text,
        },
        "issues": issues,
    }


def lint_pm_demag_step_contract(mai_text: str) -> dict[str, Any]:
    """Lint the ELF/MAGIC PM demagnetization 3-step HBRM/HBCN contract.

    This is a public, solver-free preflight.  It checks whether active `.mai`
    lines declare recoil data with `HBRM` and whether at least one material id
    has `HBCN` assignments for steps 0, 1, and 2.
    """

    upper_lines = _active_upper_lines(mai_text)
    hbrm_rows: list[dict[str, Any]] = []
    hbcn_rows: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for line in upper_lines:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "HBRM" and len(parts) >= 4:
            try:
                hbrm_rows.append({
                    "curve_id": int(float(parts[1])),
                    "recoil_mu": float(parts[2]),
                    "bmax_t": float(parts[3]),
                })
            except ValueError:
                issues.append(_issue("ERROR", "HBRM", f"could not parse HBRM line: {line}"))
        elif parts[0] == "HBRM":
            issues.append(_issue("ERROR", "HBRM", f"HBRM requires curve_id recoil_mu Bmax: {line}"))
        if parts[0] == "HBCN" and len(parts) >= 4:
            try:
                hbcn_rows.append({
                    "mid": int(float(parts[1])),
                    "step": int(float(parts[2])),
                    "curve_id": int(float(parts[3])),
                })
            except ValueError:
                issues.append(_issue("ERROR", "HBCN", f"could not parse HBCN line: {line}"))
        elif parts[0] == "HBCN":
            issues.append(_issue("ERROR", "HBCN", f"HBCN requires MID STEP curve_id: {line}"))

    steps_by_mid: dict[int, set[int]] = {}
    curves_by_mid_step: dict[str, int] = {}
    for row in hbcn_rows:
        steps_by_mid.setdefault(row["mid"], set()).add(row["step"])
        curves_by_mid_step[f"{row['mid']}:{row['step']}"] = row["curve_id"]
    complete_mids = [
        mid for mid, steps in sorted(steps_by_mid.items())
        if {0, 1, 2}.issubset(steps)
    ]
    hbrm_curves = {row["curve_id"] for row in hbrm_rows}
    hbcn_curves = {row["curve_id"] for row in hbcn_rows}
    missing_recoil_curves = sorted(curve for curve in hbcn_curves if curve not in hbrm_curves)
    if not hbrm_rows:
        issues.append(_issue("ERROR", "HBRM", "missing HBRM recoil definition for PM demagnetization"))
    if not hbcn_rows:
        issues.append(_issue("ERROR", "HBCN", "missing HBCN per-step B-H curve assignment"))
    if not complete_mids:
        issues.append(_issue("ERROR", "HBCN", "no material id has all steps 0, 1, and 2 assigned"))
    if missing_recoil_curves:
        issues.append(
            _issue(
                "WARN",
                "HBRM/HBCN",
                "HBCN references curves without HBRM recoil rows: "
                + ", ".join(str(curve) for curve in missing_recoil_curves),
            )
        )

    return {
        "schema_version": "elf-python-pm-demag-step-lint/v1",
        "status": "FAIL" if any(i["severity"] == "ERROR" for i in issues) else "PASS",
        "detected": {
            "hbrm_rows": hbrm_rows,
            "hbcn_rows": hbcn_rows,
            "complete_three_step_mids": complete_mids,
            "missing_recoil_curves": missing_recoil_curves,
            "curves_by_mid_step": curves_by_mid_step,
        },
        "contract": [
            "step 0: nominal/no opposing field",
            "step 1: opposing field or shifted temperature curve applied",
            "step 2: field/temperature removed and recoil remanence ratio inherited",
            "HBRM supplies recoil_mu and Bmax for the B-H curve",
            "HBCN maps material id and step to the B-H curve used by that step",
            "map steps 0/1/2 to radia-ngsolve pm_recoil_demag_step_summary before claiming recovery",
        ],
        "issues": issues,
    }


def build_run_request_contract(
    goal: str,
    motor_type: str = "spm",
    source_public_deck_path: str = "",
    requested_observables: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a JSON-compatible public contract for a user-local backend."""
    family = motor_type.strip().lower() or "spm"
    if family not in MOTOR_TYPES:
        family = "spm"
    observables = [str(o).strip().lower() for o in requested_observables if str(o).strip()]
    if not observables:
        observables = list(MOTOR_DEFAULT_OBSERVABLES.get(family, MOTOR_DEFAULT_OBSERVABLES["spm"]))
    return {
        "schema_version": "elf-python-run-request-contract/v1",
        "goal": goal,
        "policy": python_api_schema()["policy"],
        "motor_spec_template": build_motor_spec_template(family),
        "run_request": {
            "goal": goal,
            "run_mode": "copy_public_deck_and_run" if source_public_deck_path else "dry_run_validate_inputs_only",
            "source_public_deck_paths": [source_public_deck_path] if source_public_deck_path else [],
            "requested_observables": observables,
            "timeout_seconds": 300,
            "keep_outputs": True,
            "privacy_policy": "keep_raw_outputs_user_local",
        },
        "backend_requirements": [
            "discover product runtime without hard-coded public paths",
            "validate .mai/.meg pair before execution",
            "capture structured status and warnings",
            "parse observables into RunResult",
            "keep raw outputs local unless explicitly scrubbed",
        ],
    }


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _try_json_loads(payload: Any) -> Any:
    if not isinstance(payload, str):
        return payload
    stripped = payload.strip()
    if not stripped:
        return {}
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return payload


def _normalize_observable_key(key: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")
    aliases = {
        "torque": "torque_value",
        "torque_nm": "torque_value",
        "torque_z_nm": "torque_value",
        "moment_nm": "torque_value",
        "moment_z_nm": "torque_value",
        "mome_nm": "torque_value",
        "mome_z_nm": "torque_value",
        "average_torque_nm": "torque_value",
        "avg_torque_nm": "torque_value",
        "torque_ripple": "torque_ripple_value",
        "torque_ripple_percent": "torque_ripple_value",
        "cogging": "cogging_torque_value",
        "cogging_torque": "cogging_torque_value",
        "cogging_torque_nm": "cogging_torque_value",
        "flux": "flux_linkage_value",
        "flux_linkage": "flux_linkage_value",
        "flux_linkage_wb": "flux_linkage_value",
        "back_emf": "back_emf_constant_value",
        "back_emf_constant": "back_emf_constant_value",
        "back_emf_constant_v_per_krpm": "back_emf_constant_value",
        "bemf": "back_emf_constant_value",
        "ld": "ld_value_h",
        "ld_h": "ld_value_h",
        "l_d_h": "ld_value_h",
        "lq": "lq_value_h",
        "lq_h": "lq_value_h",
        "l_q_h": "lq_value_h",
        "loss": "loss_proxy_value",
        "loss_w": "loss_proxy_value",
        "loss_total_w": "loss_proxy_value",
        "total_loss": "loss_proxy_value",
        "total_loss_w": "loss_proxy_value",
        "loss_proxy": "loss_proxy_value",
        "copper_loss_w": "copper_loss_w",
        "iron_loss_w": "iron_loss_w",
        "magnet_loss_w": "magnet_loss_w",
        "rotor_loss_w": "rotor_loss_w",
        "inverter_loss_w": "inverter_loss_w",
        "mechanical_loss_w": "mechanical_loss_w",
        "mech_loss_w": "mechanical_loss_w",
        "efficiency": "efficiency_value",
        "efficiency_percent": "efficiency_value",
        "eta": "efficiency_value",
        "eta_percent": "efficiency_value",
        "cycle_efficiency": "cycle_efficiency_value",
        "case": "case_id",
        "case_id": "case_id",
        "id": "case_id",
        "point": "point_id",
        "point_id": "point_id",
        "operating_point": "point_id",
        "speed_rpm": "speed_rpm",
        "rotor_speed_rpm": "speed_rpm",
        "target_speed_rpm": "requested_speed_rpm",
        "requested_speed_rpm": "requested_speed_rpm",
        "command_speed_rpm": "requested_speed_rpm",
        "target_torque_nm": "requested_torque_nm",
        "requested_torque_nm": "requested_torque_nm",
        "command_torque_nm": "requested_torque_nm",
        "mechanical_power_w": "mechanical_power_w",
        "output_power_w": "mechanical_power_w",
        "shaft_power_w": "mechanical_power_w",
        "input_power_w": "input_power_w",
        "power_in_w": "input_power_w",
        "pin_w": "input_power_w",
        "electrical_input_power_w": "input_power_w",
        "force_x_n": "force_x_n",
        "force_y_n": "force_y_n",
        "force_z_n": "force_z_n",
        "force_x_n_per_m": "force_x_n_per_m",
        "force_y_n_per_m": "force_y_n_per_m",
        "force_z_n_per_m": "force_z_n_per_m",
        "radial_force_n_per_m": "radial_force_n_per_m",
        "force_unit": "force_unit",
        "force_units": "force_unit",
        "quantity_dimension": "quantity_dimension",
        "phase_current_a_peak": "phase_current_a_peak",
        "phase_current_a_rms": "phase_current_a_rms",
        "voltage_margin": "voltage_margin_value",
        "voltage_margin_v": "voltage_margin_value",
        "current_margin": "current_margin_value",
        "current_margin_a": "current_margin_value",
        "peak_temperature_c": "peak_temperature_c",
        "temperature_rise_c": "temperature_rise_c",
        "peak_stress_mpa": "peak_stress_mpa",
        "yield_margin": "yield_margin_proxy",
        "yield_margin_proxy": "yield_margin_proxy",
        "relative_order_separation": "relative_order_separation",
    }
    return aliases.get(cleaned, cleaned)


FORCE_PER_LENGTH_KEYS = (
    "force_x_n_per_m",
    "force_y_n_per_m",
    "force_z_n_per_m",
    "radial_force_n_per_m",
)
FORCE_TOTAL_KEYS = (
    "force_x_n",
    "force_y_n",
    "force_z_n",
)

RUN_RESULT_ALLOWED_KEYS = {
    "torque_value",
    "torque_ripple_value",
    "cogging_torque_value",
    "flux_linkage_value",
    "back_emf_constant_value",
    "ld_value_h",
    "lq_value_h",
    "ld_lq_value",
    "loss_proxy_value",
    "copper_loss_w",
    "iron_loss_w",
    "magnet_loss_w",
    "rotor_loss_w",
    "inverter_loss_w",
    "mechanical_loss_w",
    "efficiency_value",
    "cycle_efficiency_value",
    "case_id",
    "point_id",
    "speed_rpm",
    "requested_speed_rpm",
    "requested_torque_nm",
    "mechanical_power_w",
    "input_power_w",
    "force_x_n",
    "force_y_n",
    "force_z_n",
    "force_x_n_per_m",
    "force_y_n_per_m",
    "force_z_n_per_m",
    "radial_force_n_per_m",
    "force_unit",
    "quantity_dimension",
    "phase_current_a_peak",
    "phase_current_a_rms",
    "voltage_margin_value",
    "current_margin_value",
    "peak_temperature_c",
    "temperature_rise_c",
    "peak_stress_mpa",
    "yield_margin_proxy",
    "relative_order_separation",
    "field_probe_value",
    "convergence_status_value",
}


def _normalize_force_unit(value: Any) -> str:
    unit = str(value or "").strip().lower()
    unit = unit.replace(" ", "").replace("-", "_")
    unit = unit.replace("newtons", "n").replace("newton", "n")
    unit = unit.replace("per_meter", "per_m")
    return unit


def _force_metadata_checks(parsed: Mapping[str, Any], require_explicit: bool = False) -> dict[str, Any]:
    """Check whether normalized force rows keep dimensional meaning explicit."""

    per_length_keys = [key for key in FORCE_PER_LENGTH_KEYS if key in parsed]
    total_keys = [key for key in FORCE_TOTAL_KEYS if key in parsed]
    has_force_keys = bool(per_length_keys or total_keys)
    quantity_dimension = str(parsed.get("quantity_dimension") or "").strip().lower()
    force_unit = _normalize_force_unit(parsed.get("force_unit"))
    allowed_units = {
        "2d_per_length": {"n/m", "n_per_m"},
        "3d_total": {"n"},
    }
    issues = []
    if (require_explicit and has_force_keys) or quantity_dimension or force_unit:
        if not quantity_dimension:
            issues.append("missing quantity_dimension for force observable")
        elif quantity_dimension not in allowed_units:
            issues.append(f"unsupported quantity_dimension: {quantity_dimension}")
        if not force_unit:
            issues.append("missing force_unit for force observable")
        if quantity_dimension in allowed_units and force_unit and force_unit not in allowed_units[quantity_dimension]:
            issues.append(
                f"force_unit {force_unit} does not match quantity_dimension {quantity_dimension}"
            )
        if per_length_keys and quantity_dimension == "3d_total":
            issues.append("per-length force keys cannot be marked as 3d_total")
        if total_keys and quantity_dimension == "2d_per_length":
            issues.append("total-force keys cannot be marked as 2d_per_length")
        if per_length_keys and total_keys:
            issues.append("do not mix per-length and total-force keys in one observable row")

    return {
        "schema_version": "elf-python-force-unit-dimension-check/v1",
        "per_length_keys": per_length_keys,
        "total_force_keys": total_keys,
        "quantity_dimension": quantity_dimension or None,
        "force_unit": force_unit or None,
        "unit_dimension_consistent": not issues,
        "issues": issues,
        "allowed_quantity_dimensions": sorted(allowed_units),
    }


def parse_run_result_payload(
    payload: str | Mapping[str, Any],
    case_id: str = "",
    motor_type: str = "spm",
    requested_observables: Sequence[str] = (),
) -> dict[str, Any]:
    """Parse a public-safe normalized RunResult from JSON or key-value text."""
    data = _try_json_loads(payload)
    family = _infer_motor_type(motor_type, "spm")
    parsed: dict[str, Any] = {}
    warnings: list[str] = []
    generated_files: list[str] = []
    ignored_field_count = 0
    status = "PASS"
    resolved_case_id = case_id or "local_case"

    if isinstance(data, Mapping):
        resolved_case_id = str(data.get("case_id") or data.get("id") or resolved_case_id)
        status = str(data.get("status") or status).upper()
        raw_generated = data.get("generated_files", ())
        if isinstance(raw_generated, str):
            generated_files = [raw_generated]
        elif isinstance(raw_generated, Sequence):
            generated_files = [str(item) for item in raw_generated]
        raw_warnings = data.get("warnings", ())
        if isinstance(raw_warnings, str):
            warnings.append(raw_warnings)
        elif isinstance(raw_warnings, Sequence):
            warnings.extend(str(item) for item in raw_warnings)
        raw_observables = data.get("parsed_observables", data.get("observables", data))
        if isinstance(raw_observables, Mapping):
            for key, value in raw_observables.items():
                if key in {"schema_version", "case_id", "status", "generated_files", "warnings", "validation_labels"}:
                    continue
                norm_key = _normalize_observable_key(str(key))
                if norm_key not in RUN_RESULT_ALLOWED_KEYS:
                    ignored_field_count += 1
                    continue
                parsed[norm_key] = value
    else:
        text = str(data)
        for line in text.splitlines():
            if re.search(r"\b(warn|warning|failed|convergence)\b", line, re.IGNORECASE):
                warnings.append(line.strip())
            match = re.match(
                r"\s*([A-Za-z][A-Za-z0-9_ ./%+-]*)\s*[:=]\s*"
                r"([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)",
                line,
            )
            if not match:
                continue
            key = _normalize_observable_key(match.group(1))
            if key not in RUN_RESULT_ALLOWED_KEYS:
                ignored_field_count += 1
                continue
            parsed[key] = _safe_float(match.group(2))

    if ignored_field_count:
        warnings.append(
            f"ignored {ignored_field_count} non-observable field(s) from local result payload"
        )

    if "ld_value_h" in parsed and "lq_value_h" in parsed:
        parsed["ld_lq_value"] = {
            "ld_h": _safe_float(parsed["ld_value_h"]),
            "lq_h": _safe_float(parsed["lq_value_h"]),
            "saliency_ratio": _safe_float(parsed["lq_value_h"]) / max(_safe_float(parsed["ld_value_h"]), 1.0e-18),
        }
    if "efficiency_value" in parsed and _safe_float(parsed["efficiency_value"]) > 1.0:
        parsed["efficiency_value"] = _safe_float(parsed["efficiency_value"]) / 100.0
    if "cycle_efficiency_value" in parsed and _safe_float(parsed["cycle_efficiency_value"]) > 1.0:
        parsed["cycle_efficiency_value"] = _safe_float(parsed["cycle_efficiency_value"]) / 100.0
    if warnings and status == "PASS":
        status = "WARN"

    requested = [str(item).strip().lower() for item in requested_observables if str(item).strip()]
    missing = []
    for observable in requested:
        expected_key = f"{observable}_value"
        if observable == "ld_lq":
            expected_key = "ld_lq_value"
        if observable == "force":
            if not any(key in parsed for key in FORCE_PER_LENGTH_KEYS + FORCE_TOTAL_KEYS):
                missing.append(observable)
            continue
        if observable == "loss_proxy":
            expected_key = "loss_proxy_value"
            if not any(
                key in parsed
                for key in (
                    "loss_proxy_value",
                    "copper_loss_w",
                    "iron_loss_w",
                    "magnet_loss_w",
                    "rotor_loss_w",
                    "inverter_loss_w",
                    "mechanical_loss_w",
                    "input_power_w",
                )
            ):
                missing.append(observable)
            continue
        if expected_key not in parsed:
            missing.append(observable)
    if missing:
        warnings.append("missing requested observables: " + ", ".join(missing))
        if status == "PASS":
            status = "WARN"
    force_metadata = _force_metadata_checks(parsed, require_explicit="force" in requested)
    if force_metadata["issues"]:
        warnings.extend(force_metadata["issues"])
        if status == "PASS":
            status = "WARN"

    return {
        "schema_version": "elf-python-run-result-parse/v1",
        "case_id": resolved_case_id,
        "motor_type": family,
        "status": status,
        "generated_files": generated_files,
        "parsed_observables": parsed,
        "warnings": warnings,
        "validation_labels": [
            "local_private_payload_normalized",
            "public_observable_contract_parser",
        ],
        "missing_requested_observables": missing,
        "force_metadata_checks": force_metadata,
        "public_boundary": (
            "Parsed normalized observables only. Raw product output text and "
            "private run directories remain user-local."
        ),
    }


RESULT_FILE_SUFFIXES = {".json", ".csv", ".txt", ".log", ".out", ".mah", ".maf"}
RESULT_TEXT_MAX_BYTES = 2_000_000
RESULT_PATH_MAX_FILES = 100
RESULT_PATH_MAX_DIRECTORIES = 200
RESULT_PATH_ROOT_ENV = "ELF_MCP_RUN_ROOT"


def _is_number_like(value: Any) -> bool:
    try:
        float(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False


def _coerce_result_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return ""
    if _is_number_like(stripped):
        return _safe_float(stripped)
    return stripped


def _split_result_table_lines(text: str, source_name: str) -> list[dict[str, Any]]:
    """Extract row dictionaries from simple CSV or whitespace result tables."""
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "*", "//"))
    ]
    if not lines:
        return []

    if any("," in line for line in lines[:5]):
        rows = [row for row in csv.reader(lines) if row]
    else:
        rows = [re.split(r"\s+", line) for line in lines]
    rows = [[cell.strip() for cell in row] for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return []

    key_value_rows = []
    key_value_candidate = all(
        len(row) == 2 and re.search(r"[A-Za-z]", row[0]) and not _is_number_like(row[0])
        for row in rows
    )
    if key_value_candidate and rows[0][0].lower() in {"key", "name", "observable"}:
        rows_for_key_values = rows[1:]
    else:
        rows_for_key_values = rows
    if key_value_candidate:
        for row in rows_for_key_values:
            key_value_rows.append((row[0], row[1]))
    if key_value_rows:
        return [{key: _coerce_result_scalar(value) for key, value in key_value_rows}]

    header_index = -1
    for index, row in enumerate(rows[:10]):
        if len(row) >= 2 and any(re.search(r"[A-Za-z]", cell) for cell in row):
            header_index = index
            break
    if header_index < 0:
        return []

    headers = [cell or f"col_{index}" for index, cell in enumerate(rows[header_index])]
    parsed_rows = []
    for row_index, row in enumerate(rows[header_index + 1 :], start=1):
        if len(row) < 2:
            continue
        values = {}
        for col_index, header in enumerate(headers):
            if col_index >= len(row):
                continue
            value = row[col_index].strip()
            if not value:
                continue
            values[header] = _coerce_result_scalar(value)
        if values:
            values.setdefault("case_id", f"{Path(source_name).stem}_row_{row_index:03d}")
            parsed_rows.append(values)
    return parsed_rows


def _parse_run_result_text_records(text: str, source_name: str) -> list[Any]:
    data = _try_json_loads(text)
    if isinstance(data, Mapping):
        for key in ("results", "run_results", "cases", "rows"):
            nested = data.get(key)
            if isinstance(nested, Sequence) and not isinstance(nested, str):
                return list(nested)
        schema = str(data.get("schema_version", "")).strip().lower()
        if schema.startswith("elf-python-run-result") or "parsed_observables" in data:
            return [data]
        return []
    if isinstance(data, Sequence) and not isinstance(data, str):
        safe_records = [
            item
            for item in data
            if isinstance(item, Mapping)
            and (
                str(item.get("schema_version", "")).strip().lower().startswith("elf-python-run-result")
                or "parsed_observables" in item
            )
        ]
        return safe_records if len(safe_records) == len(data) else []
    table_rows = _split_result_table_lines(text, source_name)
    if table_rows:
        return table_rows
    return [text]


def _read_result_text(path: Path) -> tuple[str, str]:
    size = path.stat().st_size
    if size > RESULT_TEXT_MAX_BYTES:
        return "", f"{path.name}: skipped because file is larger than {RESULT_TEXT_MAX_BYTES} bytes"
    return path.read_text(encoding="utf-8", errors="replace"), ""


def _path_parse_failure(motor_type: str, warning: str) -> dict[str, Any]:
    return {
        "schema_version": "elf-python-run-result-path-parse/v1",
        "source_label": "run_path",
        "motor_type": _infer_motor_type(motor_type, "spm"),
        "status": "FAIL",
        "files_scanned": [],
        "parsed_results": [],
        "combined_observables": {},
        "warnings": [warning],
        "validation_labels": ["local_result_path_parse_denied"],
        "public_boundary": (
            "Local file parsing is disabled unless the server owner configures "
            f"{RESULT_PATH_ROOT_ENV}; paths outside that root are denied."
        ),
    }


def _resolve_allowed_run_path(run_path: str, motor_type: str) -> tuple[Path | None, dict[str, Any] | None]:
    root_text = os.environ.get(RESULT_PATH_ROOT_ENV, "").strip()
    if not root_text:
        return None, _path_parse_failure(
            motor_type,
            f"local path parsing is disabled; configure {RESULT_PATH_ROOT_ENV} before starting the server",
        )
    try:
        root = Path(root_text).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None, _path_parse_failure(
            motor_type,
            f"configured {RESULT_PATH_ROOT_ENV} is unavailable",
        )
    if not root.is_dir():
        return None, _path_parse_failure(
            motor_type,
            f"configured {RESULT_PATH_ROOT_ENV} is not a directory",
        )

    raw_path = Path(run_path).expanduser()
    candidate = raw_path if raw_path.is_absolute() else root / raw_path
    try:
        path = candidate.resolve(strict=False)
        path.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return None, _path_parse_failure(
            motor_type,
            f"run_path is outside configured {RESULT_PATH_ROOT_ENV}",
        )
    return path, None


def parse_run_result_path(
    run_path: str,
    motor_type: str = "spm",
    requested_observables: Sequence[str] = (),
    max_files: int = 20,
) -> dict[str, Any]:
    """Parse files below the server-owner configured result root."""
    family = _infer_motor_type(motor_type, "spm")
    path, denied = _resolve_allowed_run_path(run_path, family)
    if denied is not None:
        return denied
    assert path is not None
    warnings: list[str] = []
    if not path.exists():
        return {
            "schema_version": "elf-python-run-result-path-parse/v1",
            "source_label": path.name or "run_path",
            "motor_type": family,
            "status": "FAIL",
            "files_scanned": [],
            "parsed_results": [],
            "combined_observables": {},
            "warnings": ["run_path does not exist"],
            "validation_labels": ["local_result_path_parse_failed"],
            "public_boundary": "No raw local path or product output text is returned.",
        }

    try:
        limit = min(max(int(max_files), 1), RESULT_PATH_MAX_FILES)
    except (TypeError, ValueError):
        limit = 20

    if path.is_file():
        candidates = [path]
    else:
        candidates = []
        directories_seen = 0
        for directory, directory_names, file_names in os.walk(path, followlinks=False):
            directories_seen += 1
            if directories_seen > RESULT_PATH_MAX_DIRECTORIES:
                warnings.append(
                    f"directory scan stopped at {RESULT_PATH_MAX_DIRECTORIES} directories"
                )
                break
            directory_names.sort()
            file_names.sort()
            for file_name in file_names:
                item = (Path(directory) / file_name).resolve(strict=False)
                try:
                    item.relative_to(path)
                except ValueError:
                    continue
                if item.is_file() and item.suffix.lower() in RESULT_FILE_SUFFIXES:
                    candidates.append(item)
                    if len(candidates) >= limit:
                        break
            if len(candidates) >= limit:
                break
    candidates = candidates[:limit]

    parsed_results: list[dict[str, Any]] = []
    files_scanned: list[str] = []
    for candidate in candidates:
        files_scanned.append(candidate.name)
        text, warning = _read_result_text(candidate)
        if warning:
            warnings.append(warning)
            continue
        records = _parse_run_result_text_records(text, candidate.name)
        if (
            not records
            and candidate.suffix.lower() == ".json"
            and _try_json_loads(text) is not None
        ):
            warnings.append(
                f"{candidate.name}: ignored JSON file without RunResult schema or result container"
            )
            continue
        for index, record in enumerate(records, start=1):
            parsed = parse_run_result_payload(
                record,
                case_id=f"{candidate.stem}_{index:03d}",
                motor_type=family,
                requested_observables=requested_observables,
            )
            parsed["source_file"] = candidate.name
            for warning in parsed.get("warnings", []):
                warnings.append(f"{candidate.name}: {warning}")
            parsed_results.append(parsed)

    combined_observables: dict[str, Any] = {}
    for parsed in parsed_results:
        for key, value in parsed.get("parsed_observables", {}).items():
            combined_observables.setdefault(key, value)

    if any(result["status"] == "FAIL" for result in parsed_results):
        status = "FAIL"
    elif warnings or any(result["status"] == "WARN" for result in parsed_results):
        status = "WARN"
    elif parsed_results:
        status = "PASS"
    else:
        status = "WARN"
        warnings.append("no parseable result records found")

    return {
        "schema_version": "elf-python-run-result-path-parse/v1",
        "source_label": path.name or "run_path",
        "motor_type": family,
        "status": status,
        "files_scanned": files_scanned,
        "parsed_results": parsed_results,
        "combined_observables": combined_observables,
        "warnings": warnings,
        "validation_labels": [
            "local_result_files_scanned",
            "raw_output_text_withheld",
            "public_observable_contract_parser",
        ],
        "public_boundary": (
            "The parser reads user-local files but returns only normalized "
            "observables, file basenames, and warnings. Raw paths and raw "
            "product output text stay local."
        ),
    }


def _coerce_run_result_payloads(payloads: str | Sequence[Any] | Mapping[str, Any]) -> list[Any]:
    data = _try_json_loads(payloads)
    if isinstance(data, Mapping) and isinstance(data.get("parsed_results"), Sequence):
        return list(data["parsed_results"])
    if isinstance(data, Mapping):
        return [data]
    if isinstance(data, Sequence) and not isinstance(data, str):
        return list(data)
    text = str(data).strip()
    if not text:
        return []
    return [part for part in re.split(r"\n\s*---+\s*\n", text) if part.strip()]


def _score_parsed_observables(parsed: Mapping[str, Any], objective: str, target_back_emf: float = 0.0) -> float:
    torque = _safe_float(parsed.get("torque_value"))
    loss = _safe_float(parsed.get("loss_proxy_value"))
    ripple = _safe_float(parsed.get("torque_ripple_value"))
    cogging = _safe_float(parsed.get("cogging_torque_value"))
    efficiency = _safe_float(parsed.get("cycle_efficiency_value"), _safe_float(parsed.get("efficiency_value")))
    back_emf = _safe_float(parsed.get("back_emf_constant_value"))
    objective_key = _infer_objective(objective, "torque_density")
    if objective_key == "efficiency_map" or objective == "cycle_efficiency":
        return 100.0 * efficiency + 0.10 * torque - 0.02 * loss - 0.20 * ripple
    if objective_key == "back_emf_target" and target_back_emf > 0.0:
        return -abs(back_emf - target_back_emf) - 0.10 * ripple - 0.05 * cogging
    if objective_key == "ripple_reduction":
        return torque - 2.0 * ripple - 5.0 * cogging
    if objective_key == "material_reduction":
        return torque + 0.25 * back_emf - 0.02 * loss
    return torque + 0.10 * back_emf - 0.05 * loss - 0.20 * ripple


def build_motor_optimization_loop(
    motor_type: str = "spm",
    objective: str = "torque_density",
    result_payloads: str | Sequence[Any] | Mapping[str, Any] = (),
    budget: int = 9,
    target_back_emf: float = 0.0,
) -> dict[str, Any]:
    """Rank parsed RunResults and propose the next optimization loop actions."""
    family = _infer_motor_type(motor_type, "spm")
    payload_list = _coerce_run_result_payloads(result_payloads)
    parsed_results = [
        parse_run_result_payload(item, case_id=f"candidate_{index + 1}", motor_type=family)
        for index, item in enumerate(payload_list)
    ]
    ranked = []
    for result in parsed_results:
        score = _score_parsed_observables(result["parsed_observables"], objective, target_back_emf)
        penalty = 5.0 * len(result["warnings"])
        if result["status"] == "FAIL":
            penalty += 100.0
        ranked.append(
            {
                "case_id": result["case_id"],
                "status": result["status"],
                "score": round(score - penalty, 8),
                "raw_score_proxy": round(score, 8),
                "warning_count": len(result["warnings"]),
                "parsed_observables": result["parsed_observables"],
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    sweep = build_motor_sweep_matrix(family, objective=objective, budget=budget)
    completed = {item["case_id"] for item in ranked}
    next_rows = [
        row for row in sweep["rows"]
        if row["case"] not in completed
    ][: max(int(budget) - len(parsed_results), 0)]
    best = ranked[0] if ranked else {}
    return {
        "schema_version": "elf-python-motor-optimization-loop/v1",
        "motor_type": family,
        "objective": objective,
        "budget": max(int(budget), 1),
        "completed_results": len(parsed_results),
        "ranked_candidates": ranked,
        "best_candidate": best,
        "next_run_rows": next_rows,
        "loop_status": "ready_for_validation" if ranked and not next_rows else "needs_more_runs",
        "promotion_rules": [
            "only PASS/WARN parsed RunResults are ranked",
            "best candidate must pass observable-contract checks before promotion",
            "promote best candidate to NGSolve thermal/NVH/stress crosscheck",
            "do not publish raw product outputs or private run directories",
        ],
        "public_boundary": "Optimization loop ranks normalized observables only; execution remains user-local.",
    }


def build_motor_ngsolve_result_crosscheck(
    run_result_payload: str | Mapping[str, Any],
    ngsolve_result_payload: str | Mapping[str, Any],
    thermal_limit_c: float = 155.0,
    min_nvh_separation: float = 0.15,
    min_stress_margin: float = 1.5,
) -> dict[str, Any]:
    """Cross-check parsed electromagnetic RunResult against NGSolve runtime JSON."""
    run_result = parse_run_result_payload(run_result_payload)
    ngsolve = _try_json_loads(ngsolve_result_payload)
    lane_results = []
    if isinstance(ngsolve, Mapping):
        raw_results = ngsolve.get("results", [])
        if isinstance(raw_results, Mapping):
            raw_results = [raw_results]
        if isinstance(raw_results, Sequence):
            lane_results = [item for item in raw_results if isinstance(item, Mapping)]
    lane_checks = []
    for result in lane_results:
        lane = str(result.get("lane", "")).lower()
        label = "WARN"
        reason = "lane result parsed"
        if lane == "thermal":
            peak = _safe_float(result.get("peak_temperature_c"))
            label = "PASS" if peak <= thermal_limit_c else "FAIL"
            reason = f"peak_temperature_c={peak} limit={thermal_limit_c}"
        elif lane == "nvh":
            separation = _safe_float(result.get("relative_order_separation"))
            label = "PASS" if separation >= min_nvh_separation else "WARN"
            reason = f"relative_order_separation={separation} threshold={min_nvh_separation}"
        elif lane == "stress":
            margin = _safe_float(result.get("yield_margin_proxy"))
            label = "PASS" if margin >= min_stress_margin else "FAIL"
            reason = f"yield_margin_proxy={margin} threshold={min_stress_margin}"
        lane_checks.append(
            {
                "lane": lane,
                "label": label,
                "reason": reason,
                "ngsolve_result": dict(result),
            }
        )
    if not lane_checks:
        overall = "WARN"
    elif any(item["label"] == "FAIL" for item in lane_checks):
        overall = "FAIL"
    elif any(item["label"] == "WARN" for item in lane_checks) or run_result["status"] != "PASS":
        overall = "WARN"
    else:
        overall = "PASS"
    return {
        "schema_version": "elf-python-motor-ngsolve-crosscheck/v1",
        "overall_status": overall,
        "run_result_status": run_result["status"],
        "case_id": run_result["case_id"],
        "parsed_observables": run_result["parsed_observables"],
        "lane_checks": lane_checks,
        "next_actions": [
            "fix any FAIL lane before prototype handoff",
            "route WARN NVH separation back to cogging/ripple and harmonic-order plans",
            "attach PASS lane labels to drawing/BOM handoff without publishing raw private outputs",
        ],
        "public_boundary": "Crosscheck uses normalized RunResult plus NGSolve runtime JSON only.",
    }


def build_motor_drawing_bom_handoff(
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    stator_slots: int = 48,
    pole_pairs: int = 4,
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
    validation_label: str = "needs_local_run",
    run_result_payload: str | Mapping[str, Any] = "",
) -> dict[str, Any]:
    """Build public-safe drawing and BOM handoff content for motor prototypes."""
    family = _infer_motor_type(motor_type, "spm")
    run_result = parse_run_result_payload(run_result_payload, motor_type=family) if run_result_payload else {}
    slots = max(int(stator_slots), 3)
    pp = max(int(pole_pairs), 1)
    topology = build_motor_topology_parameter_plan(
        motor_type=family,
        pole_pairs=pp,
        stator_slots=slots,
        rotor_topology=rotor_topology,
        outer_diameter_mm=outer_diameter_mm,
        stack_length_mm=stack_length_mm,
    )
    winding = build_motor_winding_layout_plan(stator_slots=slots, pole_pairs=pp)
    bom = [
        {"item": "stator_lamination_stack", "quantity": 1, "role": "laminated magnetic core", "spec": "material grade and stack factor TBD by procurement"},
        {"item": "rotor_core_or_hub", "quantity": 1, "role": "rotor magnetic/mechanical path", "spec": rotor_topology},
        {"item": "phase_winding_set", "quantity": 3, "role": "three-phase copper winding", "spec": f"{slots} slots, q={winding['slots_per_pole_per_phase']}"},
        {"item": "shaft_or_mounting_hub", "quantity": 1, "role": "mechanical interface", "spec": "dimension from assembly drawing"},
        {"item": "insulation_and_potting", "quantity": 1, "role": "electrical and thermal support", "spec": "thermal class TBD"},
        {"item": "housing_or_fixture", "quantity": 1, "role": "prototype assembly", "spec": "cooling and mounting mode TBD"},
    ]
    if family in PM_MOTOR_TYPES:
        bom.insert(2, {"item": "permanent_magnets", "quantity": 2 * pp, "role": "field source", "spec": "Br/Hcj grade TBD; demag plan required"})
    if family in INDUCTION_MOTOR_TYPES:
        bom.insert(2, {"item": "rotor_bars_and_end_rings", "quantity": 1, "role": "secondary conductor", "spec": "conductivity and bar geometry TBD"})
    drawing_views = [
        {"view": "assembly_cross_section", "contents": ["stator_yoke", "slots", "airgap", "rotor", "shaft_or_hub"]},
        {"view": "rotor_detail", "contents": ["magnet_or_barrier_or_bar", "retention_or_bridge", "balance_reference"]},
        {"view": "stator_slot_detail", "contents": ["slot_opening", "tooth_width", "winding_layers", "insulation"]},
        {"view": "winding_layout", "contents": ["slot_table", "phase_belts", "coil_pitch"]},
        {"view": "validation_stamp", "contents": ["validation_label", "RunResult status", "NGSolve crosscheck status"]},
    ]
    dimensions = [
        {"name": "outer_diameter_mm", "value": float(outer_diameter_mm), "tolerance": "TBD"},
        {"name": "stack_length_mm", "value": float(stack_length_mm), "tolerance": "TBD"},
        {"name": "stator_slots", "value": slots, "tolerance": "exact count"},
        {"name": "pole_pairs", "value": pp, "tolerance": "exact count"},
        {"name": "airgap_mm", "value": 0.8, "tolerance": "from tolerance plan"},
    ]
    return {
        "schema_version": "elf-python-motor-drawing-bom-handoff/v1",
        "motor_type": family,
        "rotor_topology": rotor_topology,
        "validation_label": validation_label,
        "drawing_views": drawing_views,
        "key_dimensions": dimensions,
        "bom": bom,
        "topology_parameters": topology["parameters"],
        "winding_summary": {
            "slots_per_pole_per_phase": winding["slots_per_pole_per_phase"],
            "coil_pitch_slots": winding["coil_pitch_slots"],
            "winding_factor_proxy": winding["winding_factors"]["fundamental_winding_factor_proxy"],
        },
        "attached_result_summary": {
            "case_id": run_result.get("case_id", ""),
            "status": run_result.get("status", "not_attached"),
            "parsed_observable_keys": sorted(run_result.get("parsed_observables", {}).keys()) if run_result else [],
        },
        "export_intent": [
            "2D DXF sketch from drawing_views",
            "CSV or JSON BOM table",
            "inspection dimension table",
            "validation summary page",
        ],
        "quality_gates": [
            "all dimensions have units and tolerance ownership",
            "BOM material grades are procurement placeholders until approved",
            "drawing package carries validation labels and missing-result warnings",
            "prototype release requires local RunResult and NGSolve crosscheck attachments",
        ],
        "public_boundary": "Drawing/BOM handoff contains design intent only; no private CAD, raw outputs, or supplier-confidential data.",
    }


def _axis_values(low: float, high: float, points: int) -> list[float]:
    count = max(int(points), 1)
    if count == 1:
        return [round(float(low), 8)]
    step = (float(high) - float(low)) / float(count - 1)
    return [round(float(low) + step * index, 8) for index in range(count)]


def build_motor_operating_point_run_queue(
    motor_type: str = "spm",
    objective: str = "efficiency_map",
    torque_min_nm: float = 0.05,
    torque_max_nm: float = 1.0,
    torque_points: int = 4,
    speed_min_rpm: float = 500.0,
    speed_max_rpm: float = 12000.0,
    speed_points: int = 5,
    max_rows: int = 20,
) -> dict[str, Any]:
    """Build concrete local-run rows from an efficiency-map style grid."""
    family = _infer_motor_type(motor_type, "spm")
    torque_axis = _axis_values(torque_min_nm, torque_max_nm, torque_points)
    speed_axis = _axis_values(speed_min_rpm, speed_max_rpm, speed_points)
    requested = ["torque", "loss_proxy", "field_probe", "convergence_status"]
    if family in PM_MOTOR_TYPES or family in {"wound_field_sync", "claw_pole"}:
        requested.append("back_emf_constant")
    if family in RELUCTANCE_MOTOR_TYPES:
        requested.append("ld_lq")
    if family in INDUCTION_MOTOR_TYPES:
        requested.extend(["flux_linkage", "loss_proxy"])
    rows = []
    for speed in speed_axis:
        region = "base_speed_or_below" if speed <= max((speed_min_rpm + speed_max_rpm) / 3.0, speed_min_rpm) else "high_speed"
        for torque in torque_axis:
            rows.append(
                {
                    "case_id": f"op_{len(rows) + 1:03d}",
                    "motor_type": family,
                    "objective": objective,
                    "speed_rpm": speed,
                    "torque_nm": torque,
                    "region": region,
                    "requested_observables": requested,
                    "run_mode": "mutate_public_deck_then_run",
                    "parse_into": [
                        "torque_value",
                        "loss_proxy_value",
                        "efficiency_value",
                        "voltage_margin_value",
                        "current_margin_value",
                    ],
                }
            )
            if len(rows) >= max(int(max_rows), 1):
                break
        if len(rows) >= max(int(max_rows), 1):
            break
    return {
        "schema_version": "elf-python-motor-operating-point-run-queue/v1",
        "motor_type": family,
        "objective": objective,
        "torque_axis_nm": torque_axis,
        "speed_axis_rpm": speed_axis,
        "run_rows": rows,
        "requested_observables": requested,
        "parser_keys": [
            "torque_value",
            "loss_proxy_value",
            "efficiency_value",
            "copper_loss_w",
            "iron_loss_w",
            "magnet_loss_w",
            "rotor_loss_w",
            "voltage_margin_value",
            "current_margin_value",
        ],
        "quality_gates": [
            "every run row has explicit speed, torque, objective, and requested observables",
            "do not rank rows with missing torque or loss observables",
            "promote representative low/base/high speed rows to NGSolve thermal/NVH/stress checks",
            "store raw solver outputs only in the user-local workspace",
        ],
        "public_boundary": "Run queue is a public contract only; execution and raw outputs remain user-local.",
    }


def build_motor_inverter_pwm_harmonic_plan(
    motor_type: str = "spm",
    modulation: str = "svpwm",
    switching_frequency_hz: float = 20000.0,
    fundamental_frequency_hz: float = 400.0,
    dc_bus_v: float = 48.0,
    phase_current_a_rms: float = 10.0,
    max_sideband_order: int = 3,
) -> dict[str, Any]:
    """Plan PWM/current harmonic rows for loss and NVH follow-up."""
    family = _infer_motor_type(motor_type, "spm")
    modulation_key = (modulation or "svpwm").strip().lower()
    current_peak = _safe_float(phase_current_a_rms) * (2.0 ** 0.5)
    base_orders = [1, 5, 7, 11, 13]
    rows = []
    for order in base_orders:
        attenuation = 1.0 if order == 1 else 1.0 / float(order)
        rows.append(
            {
                "kind": "time_harmonic_current",
                "order": order,
                "frequency_hz": round(float(fundamental_frequency_hz) * order, 8),
                "phase_current_a_rms_proxy": round(float(phase_current_a_rms) * attenuation, 8),
                "expected_effect": "fundamental torque" if order == 1 else "torque ripple and AC loss",
            }
        )
    for sideband in range(1, max(int(max_sideband_order), 1) + 1):
        for sign in (-1, 1):
            frequency = float(switching_frequency_hz) + sign * sideband * float(fundamental_frequency_hz)
            if frequency <= 0:
                continue
            rows.append(
                {
                    "kind": "switching_sideband",
                    "order": f"fsw{sign:+d}{sideband}fe",
                    "frequency_hz": round(frequency, 8),
                    "phase_current_a_rms_proxy": round(float(phase_current_a_rms) / (10.0 * sideband), 8),
                    "expected_effect": "eddy-current, magnet, and acoustic sideband screening",
                }
            )
    return {
        "schema_version": "elf-python-motor-inverter-pwm-harmonic-plan/v1",
        "motor_type": family,
        "modulation": modulation_key,
        "switching_frequency_hz": float(switching_frequency_hz),
        "fundamental_frequency_hz": float(fundamental_frequency_hz),
        "dc_bus_v": float(dc_bus_v),
        "phase_current_a_rms": float(phase_current_a_rms),
        "phase_current_a_peak_proxy": round(current_peak, 8),
        "harmonic_rows": rows,
        "required_observables": [
            "loss_proxy",
            "torque_ripple",
            "field_probe",
            "convergence_status",
        ],
        "parser_keys": [
            "copper_loss_w",
            "iron_loss_w",
            "magnet_loss_w",
            "inverter_loss_w",
            "torque_ripple_value",
        ],
        "validation_routes": [
            "AC loss frequency sweep for high-frequency rows",
            "air-gap harmonic NVH plan for torque/force orders",
            "thermal network update with separated inverter and electromagnetic losses",
        ],
        "quality_gates": [
            "separate sinusoidal fundamental results from PWM sideband screening",
            "report switching frequency, modulation, bus voltage, and current units with every row",
            "do not merge inverter loss into electromagnetic loss without an explicit loss term",
        ],
        "public_boundary": "PWM plan contains public operating contracts only; waveform files and raw outputs remain local.",
    }


def build_motor_saturation_inductance_map_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    current_limit_a_peak: float = 60.0,
    current_points: int = 4,
    angle_points: int = 7,
    ld_unsat_h: float | None = None,
    lq_unsat_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> dict[str, Any]:
    """Build a current-amplitude and angle map for saturated Ld/Lq tracking."""
    family = _infer_motor_type(motor_type, "ipm")
    pp = max(int(pole_pairs), 1)
    limit = max(float(current_limit_a_peak), 1.0e-9)
    current_axis = _axis_values(limit / max(int(current_points), 1), limit, current_points)
    angle_axis = _axis_values(-70.0, 70.0, angle_points)
    ld0 = float(ld_unsat_h) if ld_unsat_h is not None else (0.00075 if family in RELUCTANCE_MOTOR_TYPES else 0.0012)
    lq0 = float(lq_unsat_h) if lq_unsat_h is not None else (0.00155 if family in RELUCTANCE_MOTOR_TYPES else 0.0012)
    psi = float(pm_flux_wb) if pm_flux_wb is not None else (0.045 if family in PM_MOTOR_TYPES else 0.0)
    rows = []
    for current in current_axis:
        saturation = min((current / limit) ** 1.4, 1.0)
        ld = ld0 * (1.0 - 0.22 * saturation)
        lq = lq0 * (1.0 - 0.10 * saturation)
        for angle in angle_axis:
            id_axis = -current * sin(radians(angle))
            iq_axis = current * cos(radians(angle))
            torque = 1.5 * pp * (psi * iq_axis + (ld - lq) * id_axis * iq_axis)
            rows.append(
                {
                    "case_id": f"sat_{len(rows) + 1:03d}",
                    "current_a_peak": round(current, 8),
                    "angle_deg_from_q_axis": round(angle, 8),
                    "id_axis_a_peak": round(id_axis, 8),
                    "iq_axis_a_peak": round(iq_axis, 8),
                    "ld_h_proxy": round(ld, 12),
                    "lq_h_proxy": round(lq, 12),
                    "saliency_ratio_proxy": round(lq / max(ld, 1.0e-18), 8),
                    "torque_nm_proxy": round(torque, 8),
                }
            )
    return {
        "schema_version": "elf-python-motor-saturation-inductance-map-plan/v1",
        "motor_type": family,
        "pole_pairs": pp,
        "current_limit_a_peak": limit,
        "current_axis_a_peak": current_axis,
        "angle_axis_deg_from_q_axis": angle_axis,
        "unsaturated_reference": {
            "ld_h": ld0,
            "lq_h": lq0,
            "pm_flux_wb": psi,
        },
        "map_rows": rows,
        "parser_keys": [
            "ld_value_h",
            "lq_value_h",
            "ld_lq_value",
            "torque_value",
            "flux_linkage_value",
            "field_probe",
        ],
        "quality_gates": [
            "track Ld and Lq as functions of current amplitude, not only one nominal point",
            "separate PM torque and reluctance torque in postprocessing",
            "flag any row with missing convergence status before MTPA or field-weakening use",
            "promote high-current negative-Id rows to demagnetization checks",
        ],
        "public_boundary": "Saturation map is a planning and parsing contract; nonlinear solve outputs remain local.",
    }


def build_motor_rotor_stress_retention_plan(
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    max_speed_rpm: float = 12000.0,
    rotor_outer_radius_mm: float = 36.0,
    bridge_thickness_mm: float = 1.0,
    sleeve_thickness_mm: float = 0.0,
    rotor_density_kg_m3: float = 7800.0,
    yield_strength_mpa: float = 450.0,
) -> dict[str, Any]:
    """Build high-speed rotor stress and retention screening gates."""
    family = _infer_motor_type(motor_type, "spm")
    radius_m = max(float(rotor_outer_radius_mm), 1.0e-9) / 1000.0
    omega = 2.0 * pi * max(float(max_speed_rpm), 0.0) / 60.0
    tip_speed = omega * radius_m
    hoop = float(rotor_density_kg_m3) * omega * omega * radius_m * radius_m / 1.0e6
    bridge_factor = max(float(bridge_thickness_mm), 0.1) / 1.0
    sleeve_factor = 1.0 + max(float(sleeve_thickness_mm), 0.0) / 2.0
    margin = float(yield_strength_mpa) * bridge_factor * sleeve_factor / max(hoop, 1.0e-9)
    if margin >= 2.0:
        label = "green"
    elif margin >= 1.2:
        label = "amber"
    else:
        label = "red"
    return {
        "schema_version": "elf-python-motor-rotor-stress-retention-plan/v1",
        "motor_type": family,
        "rotor_topology": rotor_topology,
        "max_speed_rpm": float(max_speed_rpm),
        "rotor_outer_radius_mm": float(rotor_outer_radius_mm),
        "bridge_thickness_mm": float(bridge_thickness_mm),
        "sleeve_thickness_mm": float(sleeve_thickness_mm),
        "tip_speed_m_s": round(tip_speed, 8),
        "hoop_stress_mpa_proxy": round(hoop, 8),
        "retention_margin_proxy": round(margin, 8),
        "risk_label": label,
        "required_observables": [
            "speed_rpm",
            "peak_stress_mpa",
            "yield_margin_proxy",
            "convergence_status",
        ],
        "ngsolve_follow_up": [
            "axisymmetric or 3D rotor stress solve at max_speed_rpm",
            "bridge and magnet-retention stress concentration check",
            "thermal expansion sensitivity if sleeve or adhesive is present",
        ],
        "quality_gates": [
            "do not approve high-speed operation from electromagnetic results alone",
            "red or amber margin must update topology parameters before prototype handoff",
            "attach NGSolve stress lane PASS label to drawing/BOM validation stamp",
        ],
        "public_boundary": "Stress plan is a screening contract; detailed CAD, material certs, and solver outputs remain local.",
    }


def build_motor_validation_scorecard(
    run_result_payload: str | Mapping[str, Any],
    ngsolve_result_payload: str | Mapping[str, Any] = "{}",
    required_observables: Sequence[str] = ("torque", "loss_proxy", "efficiency"),
    drawing_bom_payload: str | Mapping[str, Any] = "",
) -> dict[str, Any]:
    """Combine normalized results and validation lanes into one promotion scorecard."""
    run_result = parse_run_result_payload(
        run_result_payload,
        requested_observables=required_observables,
    )
    crosscheck = build_motor_ngsolve_result_crosscheck(run_result, ngsolve_result_payload)
    drawing = _try_json_loads(drawing_bom_payload) if drawing_bom_payload else {}
    parsed_keys = set(run_result["parsed_observables"].keys())
    required = [str(item).strip().lower() for item in required_observables if str(item).strip()]
    gate_results = []

    def add_gate(name: str, label: str, detail: str, points: int) -> None:
        gate_results.append({"gate": name, "label": label, "detail": detail, "points": points})

    add_gate(
        "run_result_status",
        run_result["status"],
        f"RunResult status is {run_result['status']}",
        20 if run_result["status"] == "PASS" else 8 if run_result["status"] == "WARN" else 0,
    )
    missing = run_result["missing_requested_observables"]
    add_gate(
        "required_observables",
        "PASS" if not missing else "WARN",
        "all required observables parsed" if not missing else "missing: " + ", ".join(missing),
        20 if not missing else 8,
    )
    lane_labels = [item["label"] for item in crosscheck["lane_checks"]]
    if not lane_labels:
        add_gate("ngsolve_lanes", "WARN", "no NGSolve lane results attached", 5)
    elif any(label == "FAIL" for label in lane_labels):
        add_gate("ngsolve_lanes", "FAIL", "one or more NGSolve lanes failed", 0)
    elif any(label == "WARN" for label in lane_labels):
        add_gate("ngsolve_lanes", "WARN", "one or more NGSolve lanes need attention", 14)
    else:
        add_gate("ngsolve_lanes", "PASS", "all attached NGSolve lanes passed", 25)
    has_loss_split = any(key in parsed_keys for key in {"copper_loss_w", "iron_loss_w", "magnet_loss_w", "rotor_loss_w"})
    add_gate(
        "loss_separation",
        "PASS" if has_loss_split else "WARN",
        "loss terms are separated" if has_loss_split else "only aggregate loss parsed",
        12 if has_loss_split else 5,
    )
    drawing_status = "not_attached"
    if isinstance(drawing, Mapping):
        drawing_status = str(drawing.get("validation_label") or drawing.get("status") or drawing_status)
    add_gate(
        "prototype_handoff",
        "PASS" if drawing_status not in {"", "not_attached", "needs_local_run"} else "WARN",
        f"drawing/BOM status: {drawing_status}",
        10 if drawing_status not in {"", "not_attached", "needs_local_run"} else 3,
    )
    score = sum(item["points"] for item in gate_results)
    if any(item["label"] == "FAIL" for item in gate_results):
        overall = "FAIL"
    elif score >= 75 and all(item["label"] == "PASS" for item in gate_results[:3]):
        overall = "PASS"
    else:
        overall = "WARN"
    promotion = "promote_to_release_candidate" if overall == "PASS" else "continue_validation_loop"
    return {
        "schema_version": "elf-python-motor-validation-scorecard/v1",
        "overall_status": overall,
        "score": score,
        "promotion_decision": promotion,
        "case_id": run_result["case_id"],
        "parsed_observable_keys": sorted(parsed_keys),
        "gate_results": gate_results,
        "crosscheck_status": crosscheck["overall_status"],
        "next_actions": [
            "fill missing observables before ranking" if missing else "rank candidate against objective",
            "attach NGSolve thermal/NVH/stress lanes before prototype release" if not lane_labels else "review any WARN/FAIL NGSolve lane",
            "separate losses for efficiency-map and thermal claims" if not has_loss_split else "propagate separated losses to thermal network",
            "attach drawing/BOM validation label before external handoff",
        ],
        "public_boundary": "Scorecard uses normalized labels and observables only; raw solver output and private provenance stay local.",
    }


def build_meg_generation_plan(
    goal: str,
    dimension: str = "auto",
    geometry_complexity: str = "auto",
) -> dict[str, Any]:
    """Plan a public-safe .meg generation path without running a mesher."""
    goal_l = goal.lower()
    dim = dimension.strip().lower() or "auto"
    complexity = geometry_complexity.strip().lower() or "auto"
    wants_3d = dim in {"3d", "solid"} or any(
        token in goal_l for token in (
            "3d",
            "axial",
            "transverse flux",
            "tfpm",
            "claw pole",
            "lundell",
            "mri",
            "wpt",
            "shield",
            "end winding",
        )
    )
    wants_simple_2d = dim in {"2d", "planar", "cross_section"} or any(
        token in goal_l for token in (
            "2d",
            "cross-section",
            "cross section",
            "spm",
            "ipm",
            "bldc",
            "srm",
            "synrm",
            "vernier",
            "slotless",
            "line-start",
            "line start",
            "deep-bar",
            "deep bar",
            "flux-switching",
            "flux switching",
            "commutator",
        )
    )
    if complexity == "high" or wants_3d:
        primary = "cubit_mesh_export"
        alternatives = ["netgen_2d", "llm_2d_template"] if wants_simple_2d else ["netgen_2d"]
    elif wants_simple_2d and complexity in {"low", "template", "simple"}:
        primary = "llm_2d_template"
        alternatives = ["netgen_2d", "cubit_mesh_export"]
    elif wants_simple_2d:
        primary = "netgen_2d"
        alternatives = ["llm_2d_template", "cubit_mesh_export"]
    else:
        primary = "netgen_2d"
        alternatives = ["cubit_mesh_export", "llm_2d_template"]

    strategy_details = {
        "cubit_mesh_export": {
            "strength": "robust for 3D, curved, CAD-like, and high-order geometry",
            "minimum_contract": [
                "geometry script",
                "material and region labels",
                "element-family labels mapped to ELF/MAGIC",
                ".meg export plus paired .mai lint",
            ],
        },
        "netgen_2d": {
            "strength": "deterministic 2D meshing for motor cross-sections and polygonal templates",
            "minimum_contract": [
                "2D region polygons",
                "air-gap and symmetry labels",
                "coil/magnet/core material regions",
                ".meg export plus observable lint",
            ],
        },
        "llm_2d_template": {
            "strength": "fast MCP prompt-to-geometry drafting for constrained 2D cases",
            "minimum_contract": [
                "typed 2D template schema",
                "bounded dimensions and units",
                "region overlap/gap checks",
                "Netgen or equivalent deterministic remesh before validation claim",
            ],
        },
    }
    return {
        "schema_version": "elf-python-meg-generation-plan/v1",
        "goal": goal,
        "dimension": dim,
        "geometry_complexity": complexity,
        "primary_strategy": primary,
        "alternative_strategies": alternatives,
        "strategies": strategy_details,
        "validation_gates": [
            "geometry_schema_lint",
            "region_label_lint",
            "mai_meg_pair_lint",
            "observable_contract_lint",
            "mmm_sign_scale_check_for_motor_2d",
            "age_or_numeric_invariant_cross_check_before_public_validation_claim",
        ],
        "public_boundary": (
            "This plan selects a .meg generation path only. It does not run a "
            "mesher, execute ELF/MAGIC, or publish solver outputs."
        ),
    }


def _infer_motor_type(goal: str, fallback: str = "spm") -> str:
    goal_l = goal.lower()
    normalized_goal = re.sub(r"[^a-z0-9]+", "_", goal_l).strip("_")
    for name in sorted(MOTOR_TYPES, key=len, reverse=True):
        if re.search(rf"(?:^|_){re.escape(name)}(?:_|$)", normalized_goal):
            return name
    aliases = {
        "pm-assisted": "pm_assisted_synrm",
        "pm assisted": "pm_assisted_synrm",
        "pma synrm": "pm_assisted_synrm",
        "pmasynrm": "pm_assisted_synrm",
        "bldc": "bldc",
        "six-step": "bldc",
        "six step": "bldc",
        "trapezoidal": "bldc",
        "line-start": "line_start_pm",
        "line start": "line_start_pm",
        "lspm": "line_start_pm",
        "deep-bar": "deep_bar_induction",
        "deep bar": "deep_bar_induction",
        "double-cage": "deep_bar_induction",
        "double cage": "deep_bar_induction",
        "flux switching": "flux_switching_pm",
        "switched flux": "flux_switching_pm",
        "vernier": "vernier_pm",
        "flux modulation": "vernier_pm",
        "transverse flux": "transverse_flux_pm",
        "tfpm": "transverse_flux_pm",
        "slotless": "slotless_pm",
        "coreless": "slotless_pm",
        "claw pole": "claw_pole",
        "lundell": "claw_pole",
        "commutator": "commutator_dc",
        "brushed dc": "commutator_dc",
        "universal motor": "commutator_dc",
        "surface": "spm",
        "pm motor": "spm",
        "permanent magnet": "spm",
        "hairpin": "ipm",
        "buried": "ipm",
        "cage": "induction",
        "slip": "induction",
        "reluctance": "synrm",
        "switched": "srm",
    }
    for token, family in aliases.items():
        if token in goal_l:
            return family
    return fallback if fallback in MOTOR_TYPES else "spm"


def _infer_objective(goal: str, fallback: str = "torque_density") -> str:
    goal_l = goal.lower()
    if any(token in goal_l for token in ("back emf", "bemf", "emf", "voltage constant")):
        return "back_emf_target"
    if any(token in goal_l for token in ("efficiency", "loss", "map")):
        return "efficiency_map"
    if any(token in goal_l for token in ("ripple", "cogging", "noise")):
        return "ripple_reduction"
    if any(token in goal_l for token in ("magnet volume", "cost", "material", "reduce")):
        return "material_reduction"
    return fallback if fallback in MOTOR_DESIGN_OBJECTIVES else "torque_density"


def build_motor_design_plan(
    goal: str,
    motor_type: str = "",
    objective: str = "",
) -> dict[str, Any]:
    """Build a motor-design API plan around variables, studies, and gates."""
    family = _infer_motor_type(goal, motor_type or "spm") if not motor_type else _infer_motor_type(motor_type, "spm")
    obj = _infer_objective(goal, objective or "torque_density") if not objective else _infer_objective(objective, "torque_density")
    variables = list(MOTOR_DESIGN_VARIABLES.get(family, MOTOR_DESIGN_VARIABLES["spm"]))
    objective_data = MOTOR_DESIGN_OBJECTIVES[obj]
    observables = list(dict.fromkeys(objective_data["primary_observables"] + objective_data["secondary_observables"]))
    studies = []
    if "back_emf_constant" in observables:
        studies.append("back_emf_speed_sweep")
    if "torque" in observables or "torque_ripple" in observables or "cogging_torque" in observables:
        studies.append("static_torque_angle")
    if "ld_lq" in MOTOR_DEFAULT_OBSERVABLES.get(family, ()):
        studies.append("dq_inductance")
    if family in INDUCTION_MOTOR_TYPES or "loss_proxy" in observables:
        studies.append("induction_slip_loss" if family in INDUCTION_MOTOR_TYPES else "ac_loss_frequency_sweep")
    if not studies:
        studies.append("static_flux_linkage")
    return {
        "schema_version": "elf-python-motor-design-plan/v1",
        "goal": goal,
        "motor_type": family,
        "objective": obj,
        "design_variables": variables,
        "primary_observables": list(objective_data["primary_observables"]),
        "secondary_observables": list(objective_data["secondary_observables"]),
        "recommended_studies": list(dict.fromkeys(studies)),
        "acceptance_rule": objective_data["acceptance"],
        "python_api_sequence": [
            'elf_python_api_schema(motor_type="{motor_type}")',
            'elf_python_meg_generation_plan(goal="{goal}", dimension="auto")',
            'elf_python_deck_lint(mai_path="<selected .mai>", requested_observables="{observables}")',
            'elf_python_motor_sweep_matrix(motor_type="{motor_type}", objective="{objective}")',
            'elf_python_run_contract(goal="{goal}", motor_type="{motor_type}", source_public_deck_path="<selected .mai>")',
            'elf_python_motor_observable_contract(motor_type="{motor_type}", study="<study>")',
        ],
        "validation_gates": [
            "MotorSpec lint PASS",
            "MEG generation path selected",
            "MAI deck lint PASS or WARN-only with explicit mitigation",
            "MMM quick-check sign/scale plausible for 2D motor studies",
            "AGE or numeric invariant target selected before public validation claim",
        ],
    }


def _levels_for_variable(variable: Mapping[str, Any], budget: int) -> list[Any]:
    low, high = variable["range"]
    default = variable["default"]
    if isinstance(default, int) and not isinstance(default, bool):
        values = [int(low), int(default), int(high)]
    else:
        values = [low, default, high]
    if budget <= 3:
        return [default]
    return values


def _linspace(low: float, high: float, count: int) -> list[float]:
    count = max(1, min(int(count), 31))
    low_f = float(low)
    high_f = float(high)
    if count == 1:
        return [0.5 * (low_f + high_f)]
    step = (high_f - low_f) / (count - 1)
    return [low_f + step * index for index in range(count)]


def build_motor_sweep_matrix(
    motor_type: str = "spm",
    objective: str = "torque_density",
    budget: int = 9,
) -> dict[str, Any]:
    """Build a deterministic public DOE/sweep matrix for motor design."""
    family = _infer_motor_type(motor_type, "spm")
    obj = _infer_objective(objective, "torque_density")
    variables = list(MOTOR_DESIGN_VARIABLES.get(family, MOTOR_DESIGN_VARIABLES["spm"]))
    active_variables = variables[: max(1, min(3, len(variables)))]
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "case": "baseline",
            "changes": {var["name"]: var["default"] for var in active_variables},
            "purpose": "nominal reference",
        }
    )
    max_rows = max(1, min(int(budget), 27))
    for var in active_variables:
        if len(rows) >= max_rows:
            break
        low, high = var["range"]
        for label, value in (("low", low), ("high", high)):
            if len(rows) >= max_rows:
                break
            changes = {v["name"]: v["default"] for v in active_variables}
            changes[var["name"]] = value
            rows.append(
                {
                    "case": f"{var['name']}_{label}",
                    "changes": changes,
                    "purpose": f"screen sensitivity to {var['name']}",
                }
            )
    while len(rows) < max_rows and len(active_variables) >= 2:
        idx = len(rows)
        changes = {v["name"]: v["default"] for v in active_variables}
        for v_index, var in enumerate(active_variables):
            low, high = var["range"]
            changes[var["name"]] = high if (idx + v_index) % 2 == 0 else low
        rows.append({"case": f"interaction_{idx}", "changes": changes, "purpose": "interaction screen"})
    objective_data = MOTOR_DESIGN_OBJECTIVES[obj]
    return {
        "schema_version": "elf-python-motor-sweep-matrix/v1",
        "motor_type": family,
        "objective": obj,
        "budget": max_rows,
        "active_variables": active_variables,
        "observables": list(dict.fromkeys(objective_data["primary_observables"] + objective_data["secondary_observables"])),
        "rows": rows[:max_rows],
        "postprocess_rules": [
            "parse RunResult status before physics interpretation",
            "discard or quarantine cases with solver/convergence warnings",
            "rank only after observable units and signs are confirmed",
            "promote best candidate to AGE/numeric-invariant validation route",
        ],
    }


def build_motor_loss_model_contract(
    motor_type: str = "spm",
    map_type: str = "efficiency",
    include_inverter: bool = True,
) -> dict[str, Any]:
    """Build the loss terms and parser contract for motor efficiency maps."""
    family = _infer_motor_type(motor_type, "spm")
    terms = [
        {
            "name": "copper_loss_w",
            "formula": "3 * phase_resistance_ohm * phase_current_rms_a**2 * temperature_factor",
            "required_inputs": ["phase_resistance_ohm", "phase_current_rms_a", "winding_temperature_c"],
            "source": "local RunResult parser or user-supplied winding model",
        },
        {
            "name": "iron_loss_w",
            "formula": "kh * frequency_hz * b_peak_t**alpha + ke * frequency_hz**2 * b_peak_t**2",
            "required_inputs": ["frequency_hz", "b_peak_t", "kh", "ke", "alpha"],
            "source": "loss_proxy, field_probe, or calibrated material model",
        },
        {
            "name": "magnet_loss_w",
            "formula": "magnet_loss_scale * frequency_hz**2 * b_harmonic_t**2",
            "required_inputs": ["frequency_hz", "b_harmonic_t", "magnet_loss_scale"],
            "source": "harmonic field proxy or local calibrated loss parser",
        },
        {
            "name": "mechanical_loss_w",
            "formula": "bearing_loss_w + windage_coeff * speed_rpm**2",
            "required_inputs": ["speed_rpm", "bearing_loss_w", "windage_coeff"],
            "source": "user-supplied mechanical loss model",
        },
    ]
    if family in INDUCTION_MOTOR_TYPES:
        terms.insert(
            2,
            {
                "name": "rotor_loss_w",
                "formula": "slip_power_w - mechanical_airgap_power_w",
                "required_inputs": ["slip", "airgap_power_w", "mechanical_airgap_power_w"],
                "source": "induction slip-loss RunResult parser",
            },
        )
    if include_inverter:
        terms.append(
            {
                "name": "inverter_loss_w",
                "formula": "switching_loss_w + conduction_loss_w",
                "required_inputs": ["dc_bus_v", "phase_current_rms_a", "switching_frequency_hz"],
                "source": "drive model, not ELF/MAGIC field solve",
            }
        )
    return {
        "schema_version": "elf-python-motor-loss-model-contract/v1",
        "motor_type": family,
        "map_type": map_type,
        "loss_terms": terms,
        "total_loss_formula": "sum(enabled loss_terms)",
        "efficiency_formula": (
            "eta = mechanical_power_w / (mechanical_power_w + total_loss_w) "
            "for motoring points with mechanical_power_w > 0"
        ),
        "required_runresult_keys": [
            "point_id",
            "speed_rpm",
            "torque_nm",
            "mechanical_power_w",
            "phase_current_rms_a",
            "voltage_ll_rms",
            "flux_linkage_value",
            "torque_value",
            "loss_proxy_value",
            "warnings",
        ],
        "quality_gates": [
            "loss terms are non-negative",
            "zero or near-zero mechanical power points are labeled, not used for peak efficiency",
            "efficiency is clamped only after raw numerator and denominator are retained",
            "hot and cold resistance assumptions are recorded separately",
            "inverter and mechanical loss assumptions are separated from field-solver losses",
        ],
        "public_boundary": "Contract only; raw product outputs and calibrated customer loss tables stay local.",
    }


def build_motor_torque_speed_envelope(
    motor_type: str = "spm",
    peak_torque_nm: float = 1.0,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
    dc_bus_v: float = 48.0,
    phase_current_limit_a_peak: float = 40.0,
    speed_points: int = 9,
) -> dict[str, Any]:
    """Build a torque-speed envelope for map clipping and field-weakening."""
    family = _infer_motor_type(motor_type, "spm")
    peak_torque = max(float(peak_torque_nm), 0.0)
    base_speed = max(float(base_speed_rpm), 1.0)
    max_speed = max(float(max_speed_rpm), base_speed)
    speeds = _linspace(0.0, max_speed, speed_points)
    base_power = peak_torque * 2.0 * pi * base_speed / 60.0
    rows = []
    for speed in speeds:
        if speed <= base_speed:
            torque_limit = peak_torque
            region = "constant_torque"
        else:
            torque_limit = peak_torque * base_speed / speed
            region = "field_weakening_constant_power"
        rows.append(
            {
                "speed_rpm": round(speed, 6),
                "torque_limit_nm": round(torque_limit, 6),
                "mechanical_power_limit_w": round(torque_limit * 2.0 * pi * speed / 60.0, 6),
                "region": region,
            }
        )
    return {
        "schema_version": "elf-python-motor-torque-speed-envelope/v1",
        "motor_type": family,
        "peak_torque_nm": peak_torque,
        "base_speed_rpm": base_speed,
        "max_speed_rpm": max_speed,
        "constant_power_w": base_power,
        "dc_bus_v": float(dc_bus_v),
        "phase_current_limit_a_peak": float(phase_current_limit_a_peak),
        "rows": rows,
        "constraints": [
            "current limit sets the constant-torque region",
            "DC bus voltage and back-EMF set the field-weakening region",
            "thermal limit may reduce continuous torque below peak torque",
            "efficiency-map points above the envelope must be clipped or labeled infeasible",
        ],
    }


def build_motor_efficiency_map_plan(
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
) -> dict[str, Any]:
    """Build an efficiency-map operating grid and local-run contract."""
    family = _infer_motor_type(motor_type, "spm")
    torques = _linspace(max(float(torque_min_nm), 0.0), max(float(torque_max_nm), 0.0), torque_points)
    speeds = _linspace(max(float(speed_min_rpm), 0.0), max(float(speed_max_rpm), 0.0), speed_points)
    envelope = build_motor_torque_speed_envelope(
        motor_type=family,
        peak_torque_nm=max(float(torque_max_nm), 0.0),
        base_speed_rpm=base_speed_rpm,
        max_speed_rpm=speed_max_rpm,
        dc_bus_v=dc_bus_v,
        phase_current_limit_a_peak=phase_current_limit_a_peak,
        speed_points=speed_points,
    )
    points = []
    for speed_index, speed in enumerate(speeds):
        if speed <= 0.0:
            torque_limit = max(float(torque_max_nm), 0.0)
        elif speed <= base_speed_rpm:
            torque_limit = max(float(torque_max_nm), 0.0)
        else:
            torque_limit = max(float(torque_max_nm), 0.0) * float(base_speed_rpm) / speed
        for torque_index, torque in enumerate(torques):
            omega = 2.0 * pi * speed / 60.0
            feasible = torque <= torque_limit + 1.0e-12
            points.append(
                {
                    "point_id": f"s{speed_index:02d}_t{torque_index:02d}",
                    "speed_rpm": round(speed, 6),
                    "torque_nm": round(torque, 6),
                    "mechanical_power_w": round(torque * omega, 6),
                    "region": "constant_torque" if speed <= base_speed_rpm else "field_weakening",
                    "feasible_by_envelope": feasible,
                    "requested_observables": [
                        "torque",
                        "flux_linkage",
                        "back_emf_constant",
                        "loss_proxy",
                        "convergence_status",
                    ],
                }
            )
    studies = ["static_torque_angle", "back_emf_speed_sweep", "ac_loss_frequency_sweep"]
    if family in INDUCTION_MOTOR_TYPES:
        studies = ["induction_slip_loss", "ac_loss_frequency_sweep"]
    return {
        "schema_version": "elf-python-motor-efficiency-map-plan/v1",
        "motor_type": family,
        "map_axes": {
            "torque_nm": [round(value, 6) for value in torques],
            "speed_rpm": [round(value, 6) for value in speeds],
        },
        "base_speed_rpm": float(base_speed_rpm),
        "dc_bus_v": float(dc_bus_v),
        "phase_current_limit_a_peak": float(phase_current_limit_a_peak),
        "recommended_studies": studies,
        "operating_points": points,
        "torque_speed_envelope": envelope,
        "loss_model_contract": build_motor_loss_model_contract(family, map_type="efficiency"),
        "local_runner_sequence": [
            "select or generate .mai/.meg seed deck",
            "for each operating point, solve or interpolate current angle/current magnitude to hit torque",
            "run field/loss observable extraction",
            "parse RunResult into required efficiency-map keys",
            "compute total_loss_w and eta per point",
            "attach infeasible, interpolated, and convergence labels before plotting",
        ],
        "postprocess_outputs": [
            "eta_grid",
            "total_loss_w_grid",
            "copper_loss_w_grid",
            "iron_loss_w_grid",
            "torque_error_nm_grid",
            "voltage_margin_grid",
            "current_margin_grid",
            "best_efficiency_point",
            "continuous_operating_region_label",
        ],
        "quality_gates": [
            "all operating points have explicit feasible/interpolated/failed labels",
            "torque error is checked before efficiency is trusted",
            "loss terms are non-negative and separated by source",
            "efficiency never hides raw mechanical_power_w or total_loss_w",
            "map resolution is recorded with axes and units",
        ],
    }


LOSS_OBSERVABLE_KEYS = (
    "loss_proxy_value",
    "copper_loss_w",
    "iron_loss_w",
    "magnet_loss_w",
    "rotor_loss_w",
    "inverter_loss_w",
    "mechanical_loss_w",
)


def _nearest_axis_index(axis: Sequence[float], value: float) -> int:
    if not axis:
        return 0
    return min(range(len(axis)), key=lambda index: abs(float(axis[index]) - value))


def _loss_terms_from_observables(observables: Mapping[str, Any]) -> dict[str, float]:
    """Return non-proxy separated loss terms from normalized observables."""
    return {
        key: _safe_float(observables.get(key), 0.0)
        for key in LOSS_OBSERVABLE_KEYS
        if key != "loss_proxy_value" and key in observables
    }


def _total_loss_from_observables(observables: Mapping[str, Any]) -> tuple[float, str]:
    explicit = _safe_float(observables.get("loss_proxy_value"), -1.0)
    if explicit >= 0.0:
        return explicit, "loss_proxy_value"
    terms = list(_loss_terms_from_observables(observables).values())
    if terms:
        return sum(max(value, 0.0) for value in terms), "summed_loss_terms"
    input_power = _safe_float(observables.get("input_power_w"), -1.0)
    mechanical_power = _safe_float(observables.get("mechanical_power_w"), -1.0)
    if input_power >= 0.0 and mechanical_power >= 0.0:
        return max(input_power - mechanical_power, 0.0), "input_minus_output_power"
    return 0.0, "missing_loss"


def _efficiency_from_observables(
    observables: Mapping[str, Any],
    planned_speed_rpm: float,
    planned_torque_nm: float,
) -> dict[str, Any]:
    speed = _safe_float(
        observables.get("speed_rpm"),
        _safe_float(observables.get("requested_speed_rpm"), planned_speed_rpm),
    )
    measured_torque = _safe_float(
        observables.get("torque_value"),
        _safe_float(observables.get("requested_torque_nm"), planned_torque_nm),
    )
    requested_torque = _safe_float(observables.get("requested_torque_nm"), planned_torque_nm)
    omega = 2.0 * pi * max(speed, 0.0) / 60.0
    mechanical_power = _safe_float(observables.get("mechanical_power_w"), measured_torque * omega)
    loss_terms = _loss_terms_from_observables(observables)
    loss_terms_total = sum(max(value, 0.0) for value in loss_terms.values())
    total_loss, loss_source = _total_loss_from_observables(observables)
    input_power = _safe_float(observables.get("input_power_w"), -1.0)
    eta = _safe_float(observables.get("efficiency_value"), -1.0)
    if eta < 0.0:
        if input_power > 0.0:
            eta = mechanical_power / input_power
        elif mechanical_power > 0.0 and total_loss >= 0.0 and loss_source != "missing_loss":
            eta = mechanical_power / max(mechanical_power + total_loss, 1.0e-18)
    if eta > 1.0:
        eta /= 100.0
    eta = max(min(eta, 1.0), 0.0) if eta >= 0.0 else None
    torque_error = measured_torque - requested_torque
    dominant_loss_term = max(loss_terms, key=lambda key: loss_terms[key]) if loss_terms else None
    loss_bucket_balance_rel_error = None
    if loss_terms and loss_source != "missing_loss":
        loss_bucket_balance_rel_error = abs(total_loss - loss_terms_total) / max(abs(total_loss), abs(loss_terms_total), 1.0)
    input_power_balance_rel_error = None
    if input_power > 0.0 and loss_source != "missing_loss":
        input_power_balance_rel_error = abs(input_power - mechanical_power - total_loss) / max(abs(input_power), abs(mechanical_power), abs(total_loss), 1.0)
    return {
        "speed_rpm": round(speed, 6),
        "torque_nm": round(requested_torque, 6),
        "measured_torque_nm": round(measured_torque, 6),
        "mechanical_power_w": round(mechanical_power, 6),
        "input_power_w": round(input_power, 6) if input_power >= 0.0 else None,
        "total_loss_w": round(total_loss, 6) if loss_source != "missing_loss" else None,
        "loss_terms_w": {key: round(value, 6) for key, value in loss_terms.items()},
        "dominant_loss_term": dominant_loss_term,
        "loss_bucket_balance_rel_error": (
            round(loss_bucket_balance_rel_error, 12)
            if loss_bucket_balance_rel_error is not None
            else None
        ),
        "input_power_balance_rel_error": (
            round(input_power_balance_rel_error, 12)
            if input_power_balance_rel_error is not None
            else None
        ),
        "efficiency": round(eta, 8) if eta is not None else None,
        "loss_source": loss_source,
        "torque_error_nm": round(torque_error, 8),
        "voltage_margin_v": (
            round(_safe_float(observables["voltage_margin_value"]), 6)
            if "voltage_margin_value" in observables
            else None
        ),
        "current_margin_a": (
            round(_safe_float(observables["current_margin_value"]), 6)
            if "current_margin_value" in observables
            else None
        ),
    }


def _gate_status(condition: bool, warn_condition: bool = False) -> str:
    if condition:
        return "PASS"
    return "WARN" if warn_condition else "FAIL"


def _efficiency_map_quality_gate_results(
    ok_points: Sequence[Mapping[str, Any]],
    warnings: Sequence[str],
    filled_points: int,
    total_points: int,
    feasible_filled: int,
    feasible_total: int,
    min_filled_fraction: float,
    max_abs_torque_error_nm: float,
) -> list[dict[str, Any]]:
    filled_fraction = filled_points / max(total_points, 1)
    feasible_fraction = feasible_filled / max(feasible_total, 1)
    eta_values = [point.get("efficiency") for point in ok_points if point.get("efficiency") is not None]
    loss_values = [point.get("total_loss_w") for point in ok_points if point.get("total_loss_w") is not None]
    torque_errors = [
        abs(_safe_float(point.get("torque_error_nm")))
        for point in ok_points
        if point.get("torque_error_nm") is not None
    ]
    voltage_margins = [
        _safe_float(point.get("voltage_margin_v"))
        for point in ok_points
        if point.get("voltage_margin_v") is not None
    ]
    loss_fraction = len(loss_values) / max(len(ok_points), 1)
    voltage_margin_fraction = len(voltage_margins) / max(len(ok_points), 1)
    max_torque_error = max(torque_errors, default=None)
    min_voltage_margin = min(voltage_margins, default=None)
    source_failures = sum(1 for point in ok_points if point.get("source_status") == "FAIL")
    gates = [
        {
            "gate": "coverage_fraction",
            "status": _gate_status(filled_fraction >= min_filled_fraction, filled_fraction >= 0.5 * min_filled_fraction),
            "metric": round(filled_fraction, 8),
            "threshold": min_filled_fraction,
            "reason": f"{filled_points}/{total_points} map cells have usable efficiency values",
        },
        {
            "gate": "feasible_region_coverage",
            "status": _gate_status(feasible_fraction >= min_filled_fraction, feasible_fraction >= 0.5 * min_filled_fraction),
            "metric": round(feasible_fraction, 8),
            "threshold": min_filled_fraction,
            "reason": f"{feasible_filled}/{feasible_total} feasible-envelope cells are filled",
        },
        {
            "gate": "efficiency_range_0_to_1",
            "status": _gate_status(bool(eta_values) and all(0.0 <= float(value) <= 1.0 for value in eta_values)),
            "metric": {
                "min_eta": round(min(eta_values), 8) if eta_values else None,
                "max_eta": round(max(eta_values), 8) if eta_values else None,
            },
            "threshold": "0 <= eta <= 1",
            "reason": "all filled efficiency values are bounded physical fractions",
        },
        {
            "gate": "loss_nonnegative",
            "status": _gate_status(bool(loss_values) and all(float(value) >= 0.0 for value in loss_values)),
            "metric": {
                "loss_filled_fraction": round(loss_fraction, 8),
                "min_loss_w": round(min(loss_values), 8) if loss_values else None,
            },
            "threshold": "all filled loss values >= 0 W and present for filled eta cells",
            "reason": "loss grid is present and no filled loss term is negative",
        },
        {
            "gate": "torque_error_within_limit",
            "status": _gate_status(
                max_torque_error is not None and max_torque_error <= max_abs_torque_error_nm,
                max_torque_error is not None and max_torque_error <= 2.0 * max_abs_torque_error_nm,
            ),
            "metric": round(max_torque_error, 8) if max_torque_error is not None else None,
            "threshold": max_abs_torque_error_nm,
            "reason": "measured torque matches requested map torque before efficiency is trusted",
        },
        {
            "gate": "voltage_margin_nonnegative_when_present",
            "status": _gate_status(
                min_voltage_margin is None or min_voltage_margin >= 0.0,
                min_voltage_margin is not None,
            ),
            "metric": {
                "present_fraction": round(voltage_margin_fraction, 8),
                "min_voltage_margin_v": round(min_voltage_margin, 8) if min_voltage_margin is not None else None,
            },
            "threshold": "if present, min voltage_margin_v >= 0 V",
            "reason": "drive voltage-limit handoff stays explicit when RunResults include voltage margin",
        },
        {
            "gate": "source_status",
            "status": _gate_status(source_failures == 0),
            "metric": source_failures,
            "threshold": 0,
            "reason": "no filled map cell came from a failed RunResult",
        },
        {
            "gate": "parser_warnings",
            "status": "PASS" if not warnings else "WARN",
            "metric": len(warnings),
            "threshold": 0,
            "reason": "warnings are surfaced and prevent silent promotion",
        },
    ]
    return gates


def build_motor_efficiency_map_from_results(
    motor_type: str = "spm",
    result_payloads: str | Sequence[Any] | Mapping[str, Any] = (),
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
) -> dict[str, Any]:
    """Build a numeric efficiency map from normalized local RunResults."""
    family = _infer_motor_type(motor_type, "spm")
    plan = build_motor_efficiency_map_plan(
        motor_type=family,
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
    torque_axis = [float(value) for value in plan["map_axes"]["torque_nm"]]
    speed_axis = [float(value) for value in plan["map_axes"]["speed_rpm"]]
    point_by_id = {point["point_id"]: point for point in plan["operating_points"]}
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    result_points = []
    warnings = []

    parsed_results = []
    for index, payload in enumerate(_coerce_run_result_payloads(result_payloads), start=1):
        if isinstance(payload, Mapping) and payload.get("schema_version") == "elf-python-run-result-parse/v1":
            parsed = dict(payload)
        else:
            parsed = parse_run_result_payload(payload, case_id=f"map_result_{index:03d}", motor_type=family)
        parsed_results.append(parsed)
        observables = parsed.get("parsed_observables", {})
        if not isinstance(observables, Mapping):
            warnings.append(f"{parsed.get('case_id', index)}: parsed_observables is not a mapping")
            continue

        point_id = str(observables.get("point_id") or parsed.get("case_id") or "")
        if point_id in point_by_id:
            planned = point_by_id[point_id]
            speed_index = speed_axis.index(float(planned["speed_rpm"]))
            torque_index = torque_axis.index(float(planned["torque_nm"]))
        else:
            speed_value = _safe_float(
                observables.get("requested_speed_rpm"),
                _safe_float(observables.get("speed_rpm"), speed_axis[0] if speed_axis else 0.0),
            )
            torque_value = _safe_float(
                observables.get("requested_torque_nm"),
                _safe_float(observables.get("torque_value"), torque_axis[0] if torque_axis else 0.0),
            )
            speed_index = _nearest_axis_index(speed_axis, speed_value)
            torque_index = _nearest_axis_index(torque_axis, torque_value)
            planned = point_by_id.get(
                f"s{speed_index:02d}_t{torque_index:02d}",
                {"point_id": f"s{speed_index:02d}_t{torque_index:02d}", "speed_rpm": speed_axis[speed_index], "torque_nm": torque_axis[torque_index], "feasible_by_envelope": True},
            )
            point_id = str(planned["point_id"])

        numeric = _efficiency_from_observables(
            observables,
            planned_speed_rpm=float(planned["speed_rpm"]),
            planned_torque_nm=float(planned["torque_nm"]),
        )
        cell = {
            "point_id": point_id,
            "case_id": parsed.get("case_id", f"map_result_{len(result_points) + 1:03d}"),
            "source_status": parsed.get("status", "PASS"),
            "feasible_by_envelope": bool(planned.get("feasible_by_envelope", True)),
            **numeric,
        }
        cell["map_status"] = (
            "ok"
            if cell["source_status"] != "FAIL" and cell["efficiency"] is not None
            else "missing_efficiency"
        )
        if cell["loss_source"] == "missing_loss" and cell["efficiency"] is None:
            warnings.append(f"{cell['case_id']}: no efficiency, input power, or loss terms were available")
        key = (speed_index, torque_index)
        previous = cells.get(key)
        if previous is None or (
            cell["map_status"] == "ok"
            and (previous.get("map_status") != "ok" or (cell["efficiency"] or 0.0) > (previous.get("efficiency") or 0.0))
        ):
            cells[key] = cell
        result_points.append(cell)

    eta_grid: list[list[float | None]] = []
    total_loss_w_grid: list[list[float | None]] = []
    torque_error_nm_grid: list[list[float | None]] = []
    status_grid: list[list[str]] = []
    for speed_index, _speed in enumerate(speed_axis):
        eta_row = []
        loss_row = []
        error_row = []
        status_row = []
        for torque_index, _torque in enumerate(torque_axis):
            cell = cells.get((speed_index, torque_index))
            eta_row.append(cell.get("efficiency") if cell else None)
            loss_row.append(cell.get("total_loss_w") if cell else None)
            error_row.append(cell.get("torque_error_nm") if cell else None)
            status_row.append(cell.get("map_status") if cell else "missing")
        eta_grid.append(eta_row)
        total_loss_w_grid.append(loss_row)
        torque_error_nm_grid.append(error_row)
        status_grid.append(status_row)

    ok_points = [cell for cell in cells.values() if cell.get("map_status") == "ok"]
    feasible_total = sum(1 for point in plan["operating_points"] if point["feasible_by_envelope"])
    feasible_filled = sum(1 for cell in ok_points if cell["feasible_by_envelope"])
    best = max(ok_points, key=lambda cell: cell.get("efficiency") or -1.0, default={})
    total_points = len(plan["operating_points"])
    filled_points = len(ok_points)
    missing_point_ids = [
        point["point_id"]
        for point in plan["operating_points"]
        if point["point_id"] not in {cell["point_id"] for cell in ok_points}
    ]
    min_fraction = max(min(float(min_filled_fraction), 1.0), 0.0)
    torque_error_limit = max(float(max_abs_torque_error_nm), 0.0)
    quality_gate_results = _efficiency_map_quality_gate_results(
        ok_points=ok_points,
        warnings=warnings,
        filled_points=filled_points,
        total_points=total_points,
        feasible_filled=feasible_filled,
        feasible_total=feasible_total,
        min_filled_fraction=min_fraction,
        max_abs_torque_error_nm=torque_error_limit,
    )
    if any(gate["status"] == "FAIL" for gate in quality_gate_results):
        overall_status = "FAIL"
    elif any(gate["status"] == "WARN" for gate in quality_gate_results):
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    return {
        "schema_version": "elf-python-motor-efficiency-map-result/v1",
        "motor_type": family,
        "status": overall_status,
        "map_axes": plan["map_axes"],
        "eta_grid": eta_grid,
        "total_loss_w_grid": total_loss_w_grid,
        "torque_error_nm_grid": torque_error_nm_grid,
        "status_grid": status_grid,
        "result_points": result_points,
        "best_efficiency_point": best,
        "coverage": {
            "parsed_results": len(parsed_results),
            "filled_points": filled_points,
            "total_points": total_points,
            "filled_fraction": round(filled_points / max(total_points, 1), 8),
            "feasible_filled_points": feasible_filled,
            "feasible_total_points": feasible_total,
            "missing_point_ids": missing_point_ids[:50],
            "missing_point_count": len(missing_point_ids),
            "min_filled_fraction": min_fraction,
            "max_abs_torque_error_nm": torque_error_limit,
        },
        "warnings": warnings,
        "quality_gate_results": quality_gate_results,
        "quality_gates": [
            "every filled cell is derived from a normalized RunResult",
            "efficiency is computed from parsed efficiency, input/output power, or mechanical power plus loss",
            "missing loss/efficiency cells remain explicitly missing",
            "coverage, feasible-region coverage, eta range, loss nonnegativity, and torque error are machine-checked",
            "voltage margin is preserved and checked when local RunResults provide it",
            "best point is a map result only and still needs validation promotion before design claims",
            "raw local output text and local paths are not returned",
        ],
        "public_boundary": "Numeric grid is computed from normalized local RunResult values only.",
    }


def build_induction_motor_slip_sweep_plan(
    pole_pairs: int = 2,
    supply_frequency_hz: float = 50.0,
    slip_min: float = 0.005,
    slip_max: float = 0.20,
    slip_points: int = 9,
    phase_current_limit_a_peak: float = 40.0,
    dc_bus_v: float = 200.0,
) -> dict[str, Any]:
    """Build an induction-motor slip sweep for torque/loss/efficiency maps."""
    pp = max(int(pole_pairs), 1)
    freq = max(float(supply_frequency_hz), 1.0e-9)
    sync_speed_rpm = 60.0 * freq / pp
    slips = _linspace(max(float(slip_min), 0.0), max(float(slip_max), 0.0), slip_points)
    points = []
    for index, slip in enumerate(slips):
        rotor_speed = (1.0 - slip) * sync_speed_rpm
        points.append(
            {
                "point_id": f"slip_{index:02d}",
                "slip": round(slip, 8),
                "supply_frequency_hz": round(freq, 6),
                "slip_frequency_hz": round(slip * freq, 6),
                "synchronous_speed_rpm": round(sync_speed_rpm, 6),
                "rotor_speed_rpm": round(rotor_speed, 6),
                "requested_observables": [
                    "torque",
                    "loss_proxy",
                    "field_probe",
                    "convergence_status",
                ],
                "derived_quantities": [
                    "airgap_power_w = torque_nm * synchronous_omega_rad_s",
                    "rotor_copper_loss_w = slip * airgap_power_w",
                    "converted_mechanical_power_w = (1 - slip) * airgap_power_w",
                    "shaft_power_w = torque_nm * rotor_omega_rad_s",
                ],
            }
        )
    return {
        "schema_version": "elf-python-induction-slip-sweep-plan/v1",
        "motor_type": "induction",
        "pole_pairs": pp,
        "supply_frequency_hz": freq,
        "synchronous_speed_rpm": sync_speed_rpm,
        "phase_current_limit_a_peak": float(phase_current_limit_a_peak),
        "dc_bus_v": float(dc_bus_v),
        "slip_axis": [point["slip"] for point in points],
        "operating_points": points,
        "recommended_studies": ["induction_slip_loss", "ac_loss_frequency_sweep"],
        "run_contract": {
            "sweep_parameter": "slip",
            "parser_keys": [
                "torque_value",
                "loss_proxy_value",
                "field_probe_value",
                "convergence_status",
                "warnings",
            ],
            "control_inputs": [
                "supply_frequency_hz",
                "slip",
                "stator_current_a_peak or voltage command",
                "rotor_bar_conductivity_scale",
            ],
        },
        "quality_gates": [
            "near-zero slip torque has the expected sign and small magnitude",
            "rotor copper loss follows slip * airgap_power trend",
            "breakdown torque region is bracketed before claiming peak torque",
            "motoring and generating slips are labeled separately if negative slip is used",
            "skin-effect and bar-conductivity assumptions are recorded",
        ],
    }


def _default_dq_parameters(family: str, current_limit_a_peak: float) -> dict[str, float]:
    current = max(float(current_limit_a_peak), 1.0e-9)
    if family in {"spm", "bldc", "slotless_pm", "axial_flux_pm", "linear_pm", "stepper"}:
        return {"ld_h": 1.0e-3, "lq_h": 1.0e-3, "pm_flux_wb": 0.045, "id_min": -0.6 * current, "id_max": 0.0}
    if family in {"ipm", "line_start_pm"}:
        return {"ld_h": 0.75e-3, "lq_h": 1.45e-3, "pm_flux_wb": 0.055, "id_min": -0.9 * current, "id_max": 0.1 * current}
    if family == "pm_assisted_synrm":
        return {"ld_h": 1.8e-3, "lq_h": 0.75e-3, "pm_flux_wb": 0.020, "id_min": 0.0, "id_max": current}
    if family in {"synrm", "srm"}:
        return {"ld_h": 2.0e-3, "lq_h": 0.65e-3, "pm_flux_wb": 0.0, "id_min": 0.0, "id_max": current}
    if family in {"flux_switching_pm", "vernier_pm"}:
        return {"ld_h": 1.1e-3, "lq_h": 1.8e-3, "pm_flux_wb": 0.035, "id_min": -0.5 * current, "id_max": 0.5 * current}
    return {"ld_h": 1.0e-3, "lq_h": 1.2e-3, "pm_flux_wb": 0.02, "id_min": -0.5 * current, "id_max": 0.5 * current}


def _dq_torque_terms(
    pole_pairs: int,
    id_a: float,
    iq_a: float,
    ld_h: float,
    lq_h: float,
    pm_flux_wb: float,
) -> dict[str, float]:
    scale = 1.5 * max(int(pole_pairs), 1)
    pm_torque = scale * pm_flux_wb * iq_a
    reluctance_torque = scale * (ld_h - lq_h) * id_a * iq_a
    total = pm_torque + reluctance_torque
    return {
        "pm_torque_nm_proxy": pm_torque,
        "reluctance_torque_nm_proxy": reluctance_torque,
        "total_torque_nm_proxy": total,
    }


def build_motor_dq_axis_map_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    current_limit_a_peak: float = 40.0,
    id_min_a: float | None = None,
    id_max_a: float | None = None,
    iq_min_a: float = 0.0,
    iq_max_a: float | None = None,
    id_points: int = 5,
    iq_points: int = 5,
    ld_h: float | None = None,
    lq_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> dict[str, Any]:
    """Build an Id/Iq map plan with PM and reluctance torque decomposition."""
    family = _infer_motor_type(motor_type, "ipm")
    current_limit = max(float(current_limit_a_peak), 1.0e-9)
    defaults = _default_dq_parameters(family, current_limit)
    ld = defaults["ld_h"] if ld_h is None else float(ld_h)
    lq = defaults["lq_h"] if lq_h is None else float(lq_h)
    psi = defaults["pm_flux_wb"] if pm_flux_wb is None else float(pm_flux_wb)
    id_min = defaults["id_min"] if id_min_a is None else float(id_min_a)
    id_max = defaults["id_max"] if id_max_a is None else float(id_max_a)
    iq_max = current_limit if iq_max_a is None else float(iq_max_a)
    ids = _linspace(id_min, id_max, id_points)
    iqs = _linspace(float(iq_min_a), iq_max, iq_points)
    points = []
    for id_index, id_value in enumerate(ids):
        for iq_index, iq_value in enumerate(iqs):
            current_mag = hypot(id_value, iq_value)
            feasible = current_mag <= current_limit + 1.0e-12
            terms = _dq_torque_terms(max(int(pole_pairs), 1), id_value, iq_value, ld, lq, psi)
            current_angle = degrees(atan2(id_value, iq_value)) if current_mag > 0 else 0.0
            points.append(
                {
                    "point_id": f"id{id_index:02d}_iq{iq_index:02d}",
                    "id_a_peak": round(id_value, 8),
                    "iq_a_peak": round(iq_value, 8),
                    "current_a_peak": round(current_mag, 8),
                    "current_angle_deg_from_q_axis": round(current_angle, 8),
                    "feasible_by_current_limit": feasible,
                    **{key: round(value, 10) for key, value in terms.items()},
                    "requested_observables": ["flux_linkage", "torque", "ld_lq", "convergence_status"],
                }
            )
    return {
        "schema_version": "elf-python-motor-dq-axis-map-plan/v1",
        "motor_type": family,
        "pole_pairs": max(int(pole_pairs), 1),
        "current_limit_a_peak": current_limit,
        "dq_parameters": {
            "ld_h": ld,
            "lq_h": lq,
            "pm_flux_wb": psi,
            "torque_formula": "T = 1.5*p*(psi_pm*Iq + (Ld-Lq)*Id*Iq)",
        },
        "axes": {
            "id_a_peak": [round(value, 8) for value in ids],
            "iq_a_peak": [round(value, 8) for value in iqs],
        },
        "operating_points": points,
        "recommended_studies": ["dq_inductance", "static_torque_angle"],
        "parser_keys": [
            "flux_d_wb",
            "flux_q_wb",
            "ld_h",
            "lq_h",
            "torque_value",
            "torque_ripple_value",
            "convergence_status",
        ],
        "quality_gates": [
            "Id/Iq sign convention is written before comparing maps",
            "Ld/Lq perturbation current is small enough for local slope but large enough for parser noise",
            "PM torque and reluctance torque are reported separately",
            "points outside current limit are labeled, not silently removed",
            "MTPA candidates are recomputed after each material or geometry change",
        ],
    }


def build_motor_mtpa_search_plan(
    motor_type: str = "ipm",
    pole_pairs: int = 4,
    current_limit_a_peak: float = 40.0,
    angle_min_deg: float = -80.0,
    angle_max_deg: float = 80.0,
    angle_points: int = 17,
    ld_h: float | None = None,
    lq_h: float | None = None,
    pm_flux_wb: float | None = None,
) -> dict[str, Any]:
    """Build an MTPA current-angle scan using a dq torque proxy."""
    family = _infer_motor_type(motor_type, "ipm")
    current = max(float(current_limit_a_peak), 1.0e-9)
    defaults = _default_dq_parameters(family, current)
    ld = defaults["ld_h"] if ld_h is None else float(ld_h)
    lq = defaults["lq_h"] if lq_h is None else float(lq_h)
    psi = defaults["pm_flux_wb"] if pm_flux_wb is None else float(pm_flux_wb)
    angles = _linspace(float(angle_min_deg), float(angle_max_deg), angle_points)
    rows = []
    best: dict[str, Any] | None = None
    for index, angle in enumerate(angles):
        theta = radians(angle)
        id_value = current * sin(theta)
        iq_value = current * cos(theta)
        terms = _dq_torque_terms(max(int(pole_pairs), 1), id_value, iq_value, ld, lq, psi)
        torque = terms["total_torque_nm_proxy"]
        torque_per_amp = torque / current
        row = {
            "case": f"angle_{index:02d}",
            "current_angle_deg_from_q_axis": round(angle, 8),
            "id_a_peak": round(id_value, 8),
            "iq_a_peak": round(iq_value, 8),
            **{key: round(value, 10) for key, value in terms.items()},
            "torque_per_amp_proxy": round(torque_per_amp, 10),
        }
        rows.append(row)
        if best is None or torque_per_amp > best["torque_per_amp_proxy"]:
            best = row
    return {
        "schema_version": "elf-python-motor-mtpa-search-plan/v1",
        "motor_type": family,
        "pole_pairs": max(int(pole_pairs), 1),
        "current_limit_a_peak": current,
        "dq_parameters": {
            "ld_h": ld,
            "lq_h": lq,
            "pm_flux_wb": psi,
            "torque_formula": "T = 1.5*p*(psi_pm*Iq + (Ld-Lq)*Id*Iq)",
        },
        "angle_axis_deg_from_q_axis": [round(value, 8) for value in angles],
        "rows": rows,
        "best_proxy_point": best or {},
        "local_runner_sequence": [
            "scan current angle at fixed current magnitude",
            "run or interpolate torque and flux linkage for each angle",
            "compute torque_per_amp and voltage/current margins",
            "refine around the best proxy angle",
            "validate final candidate with dq_inductance and static_torque_angle studies",
        ],
        "quality_gates": [
            "current angle convention is explicit",
            "best proxy point is not claimed as final until product/local RunResult confirms torque",
            "voltage margin and thermal labels are attached before map publication",
        ],
    }


def build_reluctance_motor_design_plan(
    motor_type: str = "synrm",
    pole_pairs: int = 2,
    stator_slots: int = 36,
    rotor_topology: str = "flux_barrier",
    current_limit_a_peak: float = 40.0,
) -> dict[str, Any]:
    """Build a reluctance-focused motor design plan for SynRM, PMa-SynRM, or SRM."""
    family = _infer_motor_type(motor_type, "synrm")
    if family not in {"synrm", "pm_assisted_synrm", "srm"}:
        family = "synrm"
    variables = list(MOTOR_DESIGN_VARIABLES[family])
    dq_plan = build_motor_dq_axis_map_plan(
        motor_type=family,
        pole_pairs=pole_pairs,
        current_limit_a_peak=current_limit_a_peak,
        id_points=5,
        iq_points=5,
    )
    mtpa = build_motor_mtpa_search_plan(
        motor_type=family,
        pole_pairs=pole_pairs,
        current_limit_a_peak=current_limit_a_peak,
        angle_min_deg=0.0 if family in {"synrm", "pm_assisted_synrm"} else -20.0,
        angle_max_deg=90.0 if family in {"synrm", "pm_assisted_synrm"} else 60.0,
        angle_points=10,
    )
    studies = ["dq_inductance", "static_torque_angle"]
    if family == "pm_assisted_synrm":
        studies.append("back_emf_speed_sweep")
    if family == "srm":
        studies.extend(["turn_on_turn_off_angle_sweep", "aligned_unaligned_inductance"])
    return {
        "schema_version": "elf-python-reluctance-motor-design-plan/v1",
        "motor_type": family,
        "pole_pairs": max(int(pole_pairs), 1),
        "stator_slots": max(int(stator_slots), 1),
        "rotor_topology": rotor_topology,
        "design_variables": variables,
        "saliency_targets": {
            "primary": "maximize |Ld-Lq| while keeping saturation, ripple, and stress labels acceptable",
            "dq_contract": "extract flux_d/flux_q and local Ld/Lq slopes over Id/Iq perturbations",
            "torque_contract": "separate reluctance torque from PM torque; SynRM/SRM should be reluctance-dominant",
        },
        "recommended_studies": studies,
        "dq_axis_map_plan": dq_plan,
        "mtpa_search_plan": mtpa,
        "aligned_unaligned_inductance_checks": [
            "sample aligned rotor position for maximum phase inductance",
            "sample unaligned rotor position for minimum phase inductance",
            "compute saliency ratio L_aligned / L_unaligned",
            "check dL/dtheta sign over the intended positive-torque interval",
            "label negative-torque and commutation overlap regions for SRM control",
        ],
        "observable_contracts": [
            "elf_python_motor_observable_contract(motor_type=\"%s\", study=\"dq_inductance\")" % family,
            "elf_python_motor_observable_contract(motor_type=\"%s\", study=\"static_torque_angle\")" % family,
        ],
        "quality_gates": [
            "Ld/Lq sign convention is documented",
            "aligned and unaligned positions are both sampled for SRM",
            "torque ripple is reported with average torque",
            "negative torque regions are labeled before control-angle recommendations",
            "bridge, barrier, and air-gap geometry changes keep manufacturability labels attached",
        ],
    }


def build_motor_winding_layout_plan(
    stator_slots: int = 48,
    pole_pairs: int = 4,
    phases: int = 3,
    layers: int = 2,
    coil_pitch_slots: int | None = None,
) -> dict[str, Any]:
    """Build a phase-belt winding layout and winding-factor contract."""
    slots = max(int(stator_slots), 3)
    pp = max(int(pole_pairs), 1)
    nph = max(int(phases), 1)
    layer_count = max(int(layers), 1)
    pole_pitch_slots = slots / (2.0 * pp)
    pitch = int(round(pole_pitch_slots)) if coil_pitch_slots is None else max(int(coil_pitch_slots), 1)
    slot_elec_deg = 360.0 * pp / slots
    q = slots / (2.0 * pp * nph)
    beta = radians(slot_elec_deg)
    if abs(sin(beta / 2.0)) < 1.0e-12 or q <= 0:
        distribution_factor = 1.0
    else:
        distribution_factor = abs(sin(q * beta / 2.0) / (q * sin(beta / 2.0)))
    pitch_factor = abs(sin(radians(pitch * slot_elec_deg) / 2.0))
    winding_factor = distribution_factor * pitch_factor
    phase_belts = [
        ("A", "+", 0.0),
        ("C", "-", 60.0),
        ("B", "+", 120.0),
        ("A", "-", 180.0),
        ("C", "+", 240.0),
        ("B", "-", 300.0),
    ]
    slot_table = []
    for slot in range(1, slots + 1):
        angle = ((slot - 1) * slot_elec_deg) % 360.0
        phase, sign, center = min(
            phase_belts,
            key=lambda item: min(abs(angle - item[2]), 360.0 - abs(angle - item[2])),
        )
        slot_table.append(
            {
                "slot": slot,
                "electrical_angle_deg": round(angle, 8),
                "phase": phase,
                "sign": sign,
                "belt_center_deg": center,
                "layer_count": layer_count,
            }
        )
    return {
        "schema_version": "elf-python-motor-winding-layout-plan/v1",
        "stator_slots": slots,
        "pole_pairs": pp,
        "phases": nph,
        "layers": layer_count,
        "slots_per_pole_per_phase": q,
        "slot_electrical_angle_deg": slot_elec_deg,
        "coil_pitch_slots": pitch,
        "pole_pitch_slots": pole_pitch_slots,
        "winding_factors": {
            "distribution_factor_proxy": distribution_factor,
            "pitch_factor_proxy": pitch_factor,
            "fundamental_winding_factor_proxy": winding_factor,
        },
        "slot_table": slot_table,
        "quality_gates": [
            "phase-belt convention is recorded before comparing back-EMF phases",
            "coil pitch is checked against desired harmonic suppression",
            "fractional-slot windings keep q as a rational design label",
            "end-turn length and fill factor are handled by the manufacturing handoff",
        ],
    }


def build_motor_topology_parameter_plan(
    motor_type: str = "spm",
    pole_pairs: int = 4,
    stator_slots: int = 48,
    rotor_topology: str = "outer_rotor",
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
) -> dict[str, Any]:
    """Build topology-specific geometry variables and constraints."""
    family = _infer_motor_type(motor_type, "spm")
    od = max(float(outer_diameter_mm), 1.0)
    stack = max(float(stack_length_mm), 1.0)
    common = [
        {"name": "airgap_mm", "default": 0.8, "range": (0.3, 2.0), "affects": ("torque", "loss", "manufacturing")},
        {"name": "stack_length_mm", "default": stack, "range": (0.5 * stack, 1.5 * stack), "affects": ("torque", "mass", "thermal")},
        {"name": "stator_tooth_width_fraction", "default": 0.45, "range": (0.25, 0.70), "affects": ("saturation", "slot_area")},
        {"name": "slot_opening_fraction", "default": 0.20, "range": (0.05, 0.45), "affects": ("cogging", "winding_insertability")},
    ]
    family_vars: dict[str, list[dict[str, Any]]] = {
        "spm": [
            {"name": "magnet_arc_fraction", "default": 0.75, "range": (0.55, 0.95), "affects": ("back_emf", "cogging")},
            {"name": "magnet_thickness_mm", "default": 2.5, "range": (1.0, 6.0), "affects": ("flux", "demag_margin")},
            {"name": "retaining_sleeve_thickness_mm", "default": 0.3, "range": (0.0, 1.5), "affects": ("stress", "airgap")},
        ],
        "ipm": [
            {"name": "barrier_count", "default": 2, "range": (1, 4), "affects": ("Ld_Lq", "stress")},
            {"name": "bridge_thickness_mm", "default": 1.2, "range": (0.5, 3.0), "affects": ("leakage", "stress")},
            {"name": "magnet_v_angle_deg", "default": 120.0, "range": (80.0, 155.0), "affects": ("reluctance_torque", "demag")},
        ],
        "pm_assisted_synrm": [
            {"name": "barrier_count", "default": 3, "range": (1, 5), "affects": ("Ld_Lq", "ripple")},
            {"name": "assist_magnet_depth_mm", "default": 2.0, "range": (0.4, 6.0), "affects": ("back_emf", "demag")},
            {"name": "rib_thickness_mm", "default": 1.0, "range": (0.4, 3.0), "affects": ("stress", "leakage")},
        ],
        "bldc": [
            {"name": "magnet_arc_fraction", "default": 0.80, "range": (0.55, 0.95), "affects": ("trapezoidal_emf", "cogging")},
            {"name": "hall_sensor_advance_deg", "default": 0.0, "range": (-20.0, 30.0), "affects": ("six_step_commutation", "ripple")},
            {"name": "skew_fraction", "default": 0.0, "range": (0.0, 1.0), "affects": ("cogging", "average_torque")},
        ],
        "line_start_pm": [
            {"name": "cage_bar_count", "default": max(stator_slots // 2, 12), "range": (12, 96), "affects": ("starting_torque", "ripple")},
            {"name": "pm_arc_fraction", "default": 0.55, "range": (0.25, 0.85), "affects": ("synchronizing_torque", "back_emf")},
            {"name": "barrier_bridge_mm", "default": 1.2, "range": (0.5, 3.0), "affects": ("stress", "leakage")},
        ],
        "synrm": [
            {"name": "barrier_count", "default": 3, "range": (1, 5), "affects": ("Ld_Lq", "ripple")},
            {"name": "barrier_arc_fraction", "default": 0.55, "range": (0.25, 0.85), "affects": ("saliency", "stress")},
            {"name": "rib_thickness_mm", "default": 1.0, "range": (0.4, 3.0), "affects": ("stress", "leakage")},
        ],
        "srm": [
            {"name": "stator_pole_arc_fraction", "default": 0.45, "range": (0.25, 0.70), "affects": ("aligned_inductance", "ripple")},
            {"name": "rotor_pole_arc_fraction", "default": 0.42, "range": (0.20, 0.70), "affects": ("torque", "negative_torque")},
            {"name": "yoke_thickness_fraction", "default": 0.20, "range": (0.10, 0.40), "affects": ("saturation", "mass")},
        ],
        "induction": [
            {"name": "rotor_bar_count", "default": max(2 * stator_slots // 3, 12), "range": (12, 96), "affects": ("torque_ripple", "starting_torque")},
            {"name": "rotor_bar_depth_mm", "default": 8.0, "range": (3.0, 20.0), "affects": ("skin_effect", "rotor_loss")},
            {"name": "end_ring_area_scale", "default": 1.0, "range": (0.5, 2.0), "affects": ("rotor_loss", "thermal")},
        ],
        "deep_bar_induction": [
            {"name": "outer_bar_depth_mm", "default": 4.0, "range": (1.5, 10.0), "affects": ("starting_torque", "skin_effect")},
            {"name": "inner_bar_depth_mm", "default": 12.0, "range": (4.0, 30.0), "affects": ("rated_efficiency", "rotor_loss")},
            {"name": "bar_neck_width_fraction", "default": 0.35, "range": (0.15, 0.70), "affects": ("leakage", "breakdown_torque")},
        ],
        "flux_switching_pm": [
            {"name": "stator_pm_arc_fraction", "default": 0.45, "range": (0.20, 0.70), "affects": ("flux_switching", "torque")},
            {"name": "rotor_pole_arc_fraction", "default": 0.50, "range": (0.25, 0.75), "affects": ("cogging", "torque_ripple")},
            {"name": "stator_pm_bridge_mm", "default": 1.0, "range": (0.4, 3.0), "affects": ("leakage", "stress")},
        ],
        "vernier_pm": [
            {"name": "modulation_pole_count", "default": 18, "range": (6, 72), "affects": ("gear_ratio", "torque_density")},
            {"name": "modulation_tooth_width_fraction", "default": 0.45, "range": (0.20, 0.75), "affects": ("airgap_harmonics", "ripple")},
            {"name": "pm_arc_fraction", "default": 0.75, "range": (0.45, 0.95), "affects": ("back_emf", "cogging")},
        ],
        "transverse_flux_pm": [
            {"name": "module_count", "default": 3, "range": (1, 12), "affects": ("torque_density", "3d_flux")},
            {"name": "claw_overlap_fraction", "default": 0.55, "range": (0.20, 0.85), "affects": ("leakage", "torque")},
            {"name": "axial_gap_mm", "default": 1.0, "range": (0.5, 3.0), "affects": ("torque", "manufacturing")},
        ],
        "slotless_pm": [
            {"name": "coil_span_fraction", "default": 0.80, "range": (0.45, 0.98), "affects": ("winding_factor", "copper_loss")},
            {"name": "airgap_mm", "default": 2.0, "range": (0.8, 6.0), "affects": ("torque", "thermal")},
            {"name": "support_tube_thickness_mm", "default": 1.0, "range": (0.2, 3.0), "affects": ("mechanical_gap", "heat_path")},
        ],
        "claw_pole": [
            {"name": "claw_overlap_fraction", "default": 0.55, "range": (0.25, 0.85), "affects": ("leakage", "airgap_harmonics")},
            {"name": "pole_tip_taper_fraction", "default": 0.25, "range": (0.0, 0.60), "affects": ("noise", "voltage_waveform")},
            {"name": "rotor_field_window_fraction", "default": 0.35, "range": (0.15, 0.70), "affects": ("field_current", "thermal")},
        ],
        "commutator_dc": [
            {"name": "brush_advance_deg", "default": 0.0, "range": (-20.0, 30.0), "affects": ("commutation", "torque_ripple")},
            {"name": "commutator_segment_count", "default": 24, "range": (8, 96), "affects": ("torque_ripple", "manufacturing")},
            {"name": "series_field_window_fraction", "default": 0.35, "range": (0.10, 0.70), "affects": ("starting_torque", "field_loss")},
        ],
    }
    return {
        "schema_version": "elf-python-motor-topology-parameter-plan/v1",
        "motor_type": family,
        "pole_pairs": max(int(pole_pairs), 1),
        "stator_slots": max(int(stator_slots), 3),
        "rotor_topology": rotor_topology,
        "outer_diameter_mm": od,
        "stack_length_mm": stack,
        "parameters": common + family_vars.get(family, family_vars["spm"]),
        "geometry_regions": [
            "stator_yoke",
            "stator_teeth",
            "slot_copper_or_air",
            "airgap",
            "rotor_core",
            "magnet_or_barrier_or_bar",
            "shaft_or_hub",
        ],
        "quality_gates": [
            "all dimensions carry units",
            "airgap and bridge/rib dimensions are never negative after mutation",
            "region labels map to deck/material roles",
            "manufacturing tolerance labels are attached before prototype handoff",
        ],
    }


def _pm_loadline_row(
    br_t: float,
    h_knee_a_per_m: float,
    magnet_len_m: float,
    gap_m: float,
    iron_path_m: float,
    iron_mu_r: float,
    mu_rec: float,
) -> dict[str, Any]:
    mu0 = 4.0e-7 * pi
    reluctance_length = gap_m + iron_path_m / (mu_rec * iron_mu_r)
    pc = float("inf") if reluctance_length == 0.0 else magnet_len_m / reluctance_length
    b_gap = br_t if pc == float("inf") else br_t * pc / (pc + mu_rec)
    h_m = (b_gap - br_t) / (mu0 * mu_rec)
    margin = h_m - h_knee_a_per_m
    return {
        "gap_m": gap_m,
        "B_gap_T": b_gap,
        "H_m_A_per_m": h_m,
        "permeance_coefficient": pc,
        "demag_margin_A_per_m": margin,
        "safe_against_knee": margin >= 0.0,
    }


def _summarize_pm_loadline_risk(
    rows: Sequence[Mapping[str, Any]],
    axis_key: str = "gap_m",
    amber_margin_a_per_m: float = 1.0e5,
) -> dict[str, Any]:
    """Summarize load-line rows without exposing product-run provenance."""
    rows = list(rows)
    if not rows:
        return {
            "schema_version": "elf-python-pm-loadline-risk-summary/v1",
            "axis_key": axis_key,
            "row_count": 0,
            "safe_prefix_count": 0,
            "first_unsafe_index": None,
            "first_unsafe_axis_value": None,
            "minimum_demag_margin_A_per_m": None,
            "first_unsafe_gap_m": None,
            "largest_safe_gap_m": None,
            "risk_label": "unknown",
            "checks": {
                "safe_region_is_prefix": True,
                "margin_monotone_decreasing": True,
                "margin_monotone_nonincreasing": True,
            },
        }
    margins = [float(row["demag_margin_A_per_m"]) for row in rows]
    safe = [bool(row.get("safe_against_knee", margin >= 0.0)) for row, margin in zip(rows, margins)]
    first_unsafe = next((idx for idx, flag in enumerate(safe) if not flag), None)
    minimum_index = min(range(len(margins)), key=margins.__getitem__)
    safe_prefix_count = first_unsafe if first_unsafe is not None else len(rows)
    min_margin = margins[minimum_index]
    risk_label = "red" if min_margin < 0.0 else ("amber" if min_margin <= amber_margin_a_per_m else "green")
    summary = {
        "schema_version": "elf-python-pm-loadline-risk-summary/v1",
        "axis_key": axis_key,
        "row_count": len(rows),
        "safe_prefix_count": safe_prefix_count,
        "all_safe_against_knee": all(safe),
        "first_unsafe_index": first_unsafe,
        "first_unsafe_axis_value": rows[first_unsafe].get(axis_key) if first_unsafe is not None else None,
        "minimum_margin_index": minimum_index,
        "minimum_margin_axis_value": rows[minimum_index].get(axis_key),
        "minimum_demag_margin_A_per_m": min_margin,
        "risk_label": risk_label,
        "checks": {
            "safe_region_is_prefix": all(not safe[i] or safe[i - 1] for i in range(1, len(safe))),
            "margin_monotone_decreasing": all(a > b for a, b in zip(margins, margins[1:])),
            "margin_monotone_nonincreasing": all(a >= b for a, b in zip(margins, margins[1:])),
        },
    }
    if axis_key == "gap_m":
        summary["first_unsafe_gap_m"] = summary["first_unsafe_axis_value"]
        summary["largest_safe_gap_m"] = rows[safe_prefix_count - 1].get(axis_key) if safe_prefix_count > 0 else None
    return summary


def build_motor_demag_margin_plan(
    motor_type: str = "spm",
    temperature_c: float = 120.0,
    br_20c_t: float = 1.2,
    br_temp_coeff_pct_per_k: float = -0.11,
    hcj_ka_m: float = 900.0,
    hcj_temp_coeff_pct_per_k: float = -0.45,
    id_min_a_peak: float = -40.0,
    magnet_len_m: float = 0.004,
    gaps_m: Sequence[float] = (0.0005, 0.001, 0.002, 0.004, 0.008),
    iron_path_m: float = 0.08,
    iron_mu_r: float = 1000.0,
    mu_rec: float = 1.05,
) -> dict[str, Any]:
    """Build a PM demagnetization margin contract."""
    br_20c_t = positive_float(br_20c_t, name="br_20c_t")
    hcj_ka_m = positive_float(hcj_ka_m, name="hcj_ka_m")
    magnet_len_m = positive_float(magnet_len_m, name="magnet_len_m")
    gaps_m = tuple(positive_float(gap, name="gaps_m item") for gap in gaps_m)
    if not gaps_m:
        raise ValueError("gaps_m must contain at least one positive gap")
    iron_path_m = positive_float(iron_path_m, name="iron_path_m")
    iron_mu_r = positive_float(iron_mu_r, name="iron_mu_r")
    mu_rec = positive_float(mu_rec, name="mu_rec")
    family = _infer_motor_type(motor_type, "spm")
    temp = float(temperature_c)
    br_hot = float(br_20c_t) * (1.0 + float(br_temp_coeff_pct_per_k) * (temp - 20.0) / 100.0)
    hcj_hot_ka_m = float(hcj_ka_m) * (1.0 + float(hcj_temp_coeff_pct_per_k) * (temp - 20.0) / 100.0)
    h_knee_hot_a_per_m = -1000.0 * hcj_hot_ka_m
    demag_field_proxy_ka_m = abs(float(id_min_a_peak)) * 2.0
    margin = hcj_hot_ka_m / max(demag_field_proxy_ka_m, 1.0e-9)
    loadline_rows = [
        _pm_loadline_row(
            br_t=br_hot,
            h_knee_a_per_m=h_knee_hot_a_per_m,
            magnet_len_m=float(magnet_len_m),
            gap_m=float(gap),
            iron_path_m=float(iron_path_m),
            iron_mu_r=float(iron_mu_r),
            mu_rec=float(mu_rec),
        )
        for gap in gaps_m
    ]
    loadline_margins = [row["demag_margin_A_per_m"] for row in loadline_rows]
    loadline_risk = _summarize_pm_loadline_risk(loadline_rows, axis_key="gap_m")
    loadline_checks = dict(loadline_risk["checks"])
    loadline_checks["B_gap_monotone_decreasing"] = all(
        a["B_gap_T"] > b["B_gap_T"] for a, b in zip(loadline_rows, loadline_rows[1:])
    )
    fault_current_screening = {
        "schema_version": "elf-python-motor-fault-current-demag-screening/v1",
        "negative_id_a_peak": float(id_min_a_peak),
        "negative_id_is_demag_direction": float(id_min_a_peak) <= 0.0,
        "demag_field_proxy_ka_m": demag_field_proxy_ka_m,
        "screening_rule": (
            "short-circuit and field-weakening negative-Id rows use the same "
            "HBRM/HBCN recoil-step and field_probe demag-margin contract as the "
            "temperature/gap load-line sweep"
        ),
        "recommended_radia_ngsolve_gates": [
            "short_circuit_operating_point",
            "field_weakening_speed_capability",
            "pm_recoil_demag_step_summary",
            "pm_temperature_demag_sweep_summary",
        ],
        "recommended_observable_keys": [
            "id_A_peak",
            "iq_A_peak",
            "d_axis_demag_fraction",
            "current_ratio_to_characteristic",
            "field_probe",
            "demag_margin_A_per_m",
            "safe_against_knee",
            "irreversible_demag",
            "recoil_remanence_ratio_proxy",
        ],
        "elf_step_contract": "carry fault rows through HBCN steps 0/1/2 before claiming irreversible-demag safety",
    }
    if margin >= 3.0:
        label = "green"
    elif margin >= 1.5:
        label = "amber"
    else:
        label = "red"
    if loadline_risk["risk_label"] == "red":
        label = "red"
    elif label == "green" and loadline_risk["risk_label"] == "amber":
        label = "amber"
    bem_source_balance_contract = {
        "schema_version": "elf-python-pm-bem-source-balance-contract/v1",
        "metadata_gate": "pm_bem_surface_normal_metadata_gate",
        "balance_gate": "pm_bem_surface_source_balance_gate",
        "surface_source_density": "sigma_m = M dot n",
        "normal_convention": "outward_from_magnet",
        "expected_normal_convention": "outward_from_magnet",
        "source_convention": "sigma_m_equals_m_dot_n",
        "signed_charge_proxy": "sum_i area_i * dot(M_i, n_i)",
        "source_balance_unit": "area_weighted_m_dot_n",
        "signed_charge_balance_rel_tol": 1.0e-9,
        "required_row_keys": [
            "surface_name",
            "area_m2",
            "normal_unit_vector",
            "magnetization_A_per_m",
            "surface_source_artifact_id",
            "magnetization_source_id",
            "material_id",
            "material_name",
        ],
        "required_summary_keys": [
            "surface_mesh_id",
            "surface_mesh_digest",
            "surface_row_count",
            "source_balance_artifact_id",
            "source_balance_digest",
            "source_convention",
            "expected_surface_source_artifact_id",
            "expected_magnetization_source_id",
            "expected_material_id",
            "expected_material_name",
            "total_area_m2",
            "normal_convention",
            "source_balance_unit",
            "signed_charge_balance_abs",
            "signed_charge_balance_rel_tol",
        ],
        "negative_controls": [
            "inward normal",
            "normal_convention not outward_from_magnet",
            "non-unit normal",
            "missing magnetization vector",
            "duplicate surface name",
            "open surface",
            "missing surface_mesh_id",
            "stale surface_mesh_digest",
            "wrong surface_row_count",
            "missing source_balance_artifact_id",
            "stale source_balance_digest",
            "wrong source_convention",
            "stale surface_source_artifact_id",
            "missing magnetization_source_id",
            "stale material_name",
            "missing total_area_m2",
            "missing source_balance_unit",
        ],
        "public_boundary": "metadata and balance contract only; no licensed product field values",
    }
    run_result_loadline_handoff = {
        "schema_version": "elf-python-run-result-loadline-handoff/v1",
        "parser_tools": [
            "elf_python_run_result_parse",
            "elf_python_run_result_parse_path",
        ],
        "row_identity": "case_id",
        "required_normalized_columns": [
            "case_id",
            "temperature_C",
            "gap_m",
            "B_gap_T",
            "H_pm_A_per_m",
            "H_knee_A_per_m",
            "recoil_mu_r",
            "safe_against_knee",
        ],
        "metadata_gate": "pm_loadline_metadata_gate",
        "loadline_gate": "pm_temperature_demag_sweep_summary",
        "recoil_step_gate": "pm_recoil_demag_step_summary",
        "notebook_policy": (
            "A local RunResult row is not a load-line notebook row until H/B/"
            "temperature units, demag sign convention, magnetization axis, knee "
            "reference, and recoil permeability are explicit."
        ),
        "negative_controls": [
            "missing case_id",
            "missing H_pm_A_per_m",
            "wrong h_field_unit",
            "missing recoil_mu_r",
            "safe_against_knee not consistent with demag_margin_A_per_m",
        ],
        "public_boundary": "contract only; local product result values stay user-local",
    }
    demag_package_handoff = {
        "schema_version": "elf-python-demag-package-handoff/v1",
        "package_gate": "pm_demag_package_identity_gate",
        "row_identity": ["case_id", "magnet_id"],
        "required_artifacts": [
            "run_result",
            "loadline_metadata",
            "bem_surface",
            "recoil_steps",
        ],
        "required_run_result_columns": [
            "H_pm_A_per_m",
            "H_knee_A_per_m",
            "safe_against_knee",
        ],
        "source_gates": {
            "run_result": "elf_python_run_result_parse_path",
            "loadline_metadata": "pm_loadline_metadata_gate",
            "bem_surface": "pm_bem_surface_normal_metadata_gate",
            "recoil_steps": "pm_recoil_demag_three_step_gate",
        },
        "negative_controls": [
            "missing case_id",
            "stale magnet_id",
            "missing H_knee_A_per_m",
            "missing safe_against_knee",
            "recoil steps missing step 2",
        ],
        "public_boundary": "identity and gate contract only; product field values stay user-local",
    }
    demag_margin_screening_package = {
        "schema_version": "elf-python-demag-margin-screening-package/v1",
        "package_gate": "pm_demag_margin_screening_package_gate",
        "manifest_gate": "pm_demag_margin_screening_package_gate",
        "row_identity": ["case_id", "magnet_id", "temperature_C"],
        "material_state_keys": [
            "Br_T",
            "H_knee_A_per_m",
            "recoil_mu_r",
        ],
        "material_state_identity_keys": [
            "material_state_artifact_id",
            "material_state_digest",
        ],
        "material_state_contract": (
            "If any demag-margin artifact records hot magnet material state, "
            "all load-line, fault-current, BEM source-balance, and demag-package "
            "artifacts must record the same Br_T, H_knee_A_per_m, and recoil_mu_r. "
            "For ELF/MAGIC HBRM/HBCN demag workflows, also carry the material-state "
            "artifact id and digest so stale B-H/recoil step files cannot be joined "
            "to a fresh field-probe table."
        ),
        "step_identity_keys": [
            "load_step_id",
            "fault_step_id",
            "demag_step_id",
        ],
        "step_identity_contract": (
            "When the package combines load-line screening, negative-Id/fault "
            "screening, and HBRM/HBCN demag evaluation, preserve the load, fault, "
            "and demag step ids.  Matching case_id/magnet_id/temperature_C is not "
            "sufficient if a row came from a stale solver step or manifest."
        ),
        "required_artifacts": [
            "loadline_sweep",
            "fault_current_screening",
            "bem_source_balance",
            "demag_package",
        ],
        "source_gates": {
            "loadline_sweep": "pm_temperature_demag_sweep_summary",
            "fault_current_screening": "fault_current_demag_screening",
            "bem_source_balance": "pm_bem_surface_source_balance_gate",
            "demag_package": "pm_demag_package_identity_gate",
        },
        "bem_source_balance_identity_keys": [
            "source_balance_artifact_id",
            "source_balance_digest",
            "source_convention",
        ],
        "bem_source_balance_identity_contract": (
            "The BEM source-balance row is itself an artifact.  Keep the "
            "source-balance artifact id, digest, and source convention "
            "(sigma_m = M dot n for the outward normal convention) with the "
            "demag-margin package before accepting any downstream field-probe "
            "or load-line row."
        ),
        "required_fault_observables": [
            "field_probe",
            "demag_margin_A_per_m",
            "recoil_remanence_ratio_proxy",
        ],
        "field_probe_identity_keys": [
            "field_probe_id",
            "field_probe_family",
            "observation_region_id",
            "field_probe_geometry_digest",
            "field_probe_point_xyz_m",
            "observation_component",
            "field_axis_convention",
            "field_sign_convention",
            "field_probe_method",
            "averaging_rule",
        ],
        "field_probe_identity_contract": (
            "A field_probe observable is solver-ready only when tied to a stable "
            "probe id, observable family, magnet observation region, demag-axis "
            "field component, probe geometry digest, representative probe point, "
            "field-axis convention, sign convention, probe/export method, and "
            "spatial averaging rule."
        ),
        "field_probe_output_identity_keys": [
            "field_probe_output_artifact_id",
            "field_probe_output_digest",
            "field_probe_output_path",
        ],
        "field_probe_output_identity_contract": (
            "The field_probe observation identity is not enough for notebook "
            "promotion.  The exported probe table/result artifact id, digest, "
            "and path must be recorded so stale demag-margin rows cannot reuse "
            "an old output table."
        ),
        "required_bem_source_balance_summary_keys": [
            "surface_mesh_id",
            "surface_mesh_digest",
            "surface_row_count",
            "source_balance_artifact_id",
            "source_balance_digest",
            "source_convention",
            "total_area_m2",
            "normal_convention",
            "expected_bem_normal_convention",
            "source_balance_unit",
            "signed_charge_balance_abs",
            "signed_charge_balance_rel_tol",
        ],
        "negative_controls": [
            "stale temperature_C",
            "fault row with positive Id but marked as demag",
            "missing field_probe",
            "stale field_probe_id",
            "wrong field_probe_family",
            "stale field_probe_geometry_digest",
            "missing field_probe_point_xyz_m",
            "wrong observation_component",
            "wrong field_axis_convention",
            "wrong field_sign_convention",
            "wrong field_probe_method",
            "missing field_probe_method",
            "missing averaging_rule",
            "stale field_probe_output_artifact_id",
            "stale field_probe_output_digest",
            "missing field_probe_output_path",
            "stale material_state_artifact_id",
            "stale material_state_digest",
            "missing material_state_artifact_id",
            "stale fault_step_id",
            "missing demag_step_id",
            "missing BEM balance tolerance",
            "missing BEM surface mesh id",
            "stale BEM surface mesh digest",
            "wrong BEM surface row count",
            "missing BEM source-balance artifact id",
            "stale BEM source-balance digest",
            "wrong BEM source convention",
            "missing BEM surface area",
            "missing BEM normal convention",
            "wrong BEM normal convention",
            "missing BEM source unit",
            "missing BEM balance residual value",
            "demag package missing recoil_steps",
            "stale magnet_id",
            "stale Br_T/H_knee_A_per_m/recoil_mu_r material state",
            "one artifact missing material_state while others include it",
            "load-line sweep without minimum_demag_margin_A_per_m or risk label",
        ],
        "slot166_reference": {
            "case_id": "demag_case_166",
            "magnet_id": "pm_spm_A",
            "temperature_C": temp,
            "radia_ngsolve_gate": "pm_demag_margin_screening_package_gate",
            "field_probe_id": "elf_slot286_field_probe_pm_spm_A_demag_axis_v1",
            "field_probe_family": "elf_demag_margin_field_probe",
            "observation_region_id": "pm_spm_A_volume",
            "field_probe_geometry_digest": "sha256:elf_slot326_field_probe_volume_pm_spm_A",
            "field_probe_point_xyz_m": [0.028, 0.0, 0.0],
            "observation_component": "H_parallel_demag_axis",
            "field_axis_convention": "magnetization_axis_positive",
            "field_sign_convention": "negative_h_parallel_is_demag",
            "field_probe_method": "elf_volume_average_h_parallel_probe",
            "averaging_rule": "volume_average",
            "field_probe_output_artifact_id": "elf_slot294_field_probe_table_pm_spm_A_v1",
            "field_probe_output_digest": "sha256:elf_slot294_field_probe_table_pm_spm_A",
            "surface_mesh_id": "bem_surface_mesh_pm_spm_A_v1",
            "surface_mesh_digest": "sha256:bem_surface_mesh_pm_spm_A_v1",
            "surface_row_count": 6,
            "source_balance_artifact_id": "bem_source_balance_pm_spm_A_v1",
            "source_balance_digest": "sha256:bem_source_balance_pm_spm_A_v1",
            "source_convention": "sigma_m_equals_m_dot_n",
            "material_state_artifact_id": "elf_slot334_pm_spm_A_hbrm_hbcn_state_v1.json",
            "material_state_digest": "sha256:elf_slot334_pm_spm_A_hbrm_hbcn_state_v1",
            "load_step_id": "elf_slot342_loadline_hot_120c_v1",
            "fault_step_id": "elf_slot342_negative_id_fault_step_v1",
            "demag_step_id": "elf_slot342_hbcn_demag_step2_v1",
            "rejected_controls": [
                "stale temperature_C",
                "positive Id marked as demag",
                "stale field_probe_id",
                "wrong field_probe_family",
                "stale field_probe_geometry_digest",
                "missing field_probe_point_xyz_m",
                "wrong observation_component",
                "wrong field_axis_convention",
                "wrong field_sign_convention",
                "missing averaging_rule",
                "stale field_probe_output_artifact_id",
                "stale field_probe_output_digest",
                "missing field_probe_output_path",
                "stale BEM source-balance artifact id",
                "stale BEM source-balance digest",
                "wrong BEM source convention",
                "stale material_state_artifact_id",
                "stale material_state_digest",
                "stale fault_step_id",
                "missing demag_step_id",
                "missing BEM balance tolerance",
                "demag package missing recoil_steps",
            ],
        },
        "notebook_policy": (
            "Do not promote a demag-margin notebook row until load-line, "
            "fault-current, BEM source-balance, and demag-package artifacts "
            "share case_id, magnet_id, temperature_C, and any recorded hot "
            "material-state tuple, material-state artifact id/digest, BEM "
            "source-balance artifact id/digest/source convention, plus the field-probe "
            "family, field-probe observation identity, field-probe geometry identity, "
            "field-axis/sign convention, and field-probe output artifact identity when "
            "fault-current rows provide a probe.  Carry load/fault/demag step ids "
            "when rows are promoted from solver-step manifests."
        ),
        "public_boundary": "screening contract only; licensed product field values stay user-local",
    }
    return {
        "schema_version": "elf-python-motor-demag-margin-plan/v1",
        "motor_type": family,
        "temperature_c": temp,
        "br_hot_t_proxy": br_hot,
        "hcj_ka_m": float(hcj_ka_m),
        "hcj_hot_ka_m": hcj_hot_ka_m,
        "h_knee_hot_a_per_m": h_knee_hot_a_per_m,
        "id_min_a_peak": float(id_min_a_peak),
        "demag_field_proxy_ka_m": demag_field_proxy_ka_m,
        "margin_proxy": margin,
        "risk_label": label,
        "loadline_sweep": loadline_rows,
        "loadline_summary": {
            "magnet_len_m": float(magnet_len_m),
            "iron_path_m": float(iron_path_m),
            "iron_mu_r": float(iron_mu_r),
            "mu_rec": float(mu_rec),
            "safe_prefix_count": loadline_risk["safe_prefix_count"],
            "first_unsafe_index": loadline_risk["first_unsafe_index"],
            "first_unsafe_gap_m": loadline_risk["first_unsafe_gap_m"],
            "largest_safe_gap_m": loadline_risk.get("largest_safe_gap_m"),
            "minimum_demag_margin_A_per_m": min(loadline_margins) if loadline_margins else None,
            "risk_label": loadline_risk["risk_label"],
            "risk_summary": loadline_risk,
            "checks": loadline_checks,
        },
        "elf_step_contract": {
            "schema_version": "elf-python-pm-demag-hbrm-hbcn-contract/v1",
            "lint_tool": "elf_python_pm_demag_step_lint",
            "required_hbrm_role": "HBRM defines each recoil/knee curve used by a PM demag step",
            "required_hbcn_role": "HBCN maps material id and step number to the HBRM curve",
            "required_hbcn_steps": [0, 1, 2],
            "recommended_observable_keys": [
                "gap_m",
                "B_gap_T",
                "H_m_A_per_m",
                "step0_H_A_per_m",
                "step1_H_A_per_m",
                "step2_H_A_per_m",
                "H_knee_A_per_m",
                "demag_margin_A_per_m",
                "safe_against_knee",
                "irreversible_demag",
                "recoil_remanence_ratio_proxy",
            ],
            "metadata_gate": "pm_loadline_metadata_gate",
            "radia_ngsolve_gate": "pm_recoil_demag_step_summary",
            "loadline_gate": "pm_temperature_demag_sweep_summary",
            "slot46_reference": {
                "first_unsafe_gap_m": loadline_risk["first_unsafe_gap_m"],
                "safe_prefix_count": loadline_risk["safe_prefix_count"],
                "minimum_demag_margin_A_per_m": min(loadline_margins) if loadline_margins else None,
                "risk_label": loadline_risk["risk_label"],
            },
            "slot102_reference": {
                "step_fields_A_per_m": {"0": -2.0e5, "1": -6.0e5, "2": -3.0e5},
                "H_knee_A_per_m": -5.0e5,
                "irreversible_demag": True,
                "recoil_remanence_ratio_proxy": 0.8,
            },
        },
        "fault_current_screening": fault_current_screening,
        "bem_source_balance_contract": bem_source_balance_contract,
        "run_result_loadline_handoff": run_result_loadline_handoff,
        "demag_package_handoff": demag_package_handoff,
        "demag_margin_screening_package": demag_margin_screening_package,
        "required_observables": [
            "field_probe",
            "flux_linkage",
            "back_emf_constant",
            "convergence_status",
        ],
        "sweep_axes": [
            "temperature_c",
            "negative_id_a_peak",
            "magnet_thickness_mm",
            "magnet_grade_or_hcj",
        ],
        "loadline_checks": [
            "run pm_loadline_metadata_gate before parsing B_gap/H_m/H_knee rows so H units and demag sign are explicit",
            "run pm_bem_surface_normal_metadata_gate before magnetic-charge BEM assembly so outward normals and M dot n signs are explicit",
            "run pm_bem_surface_source_balance_gate so closed PM surface signed source proxy sum_i area_i*(M dot n) is near zero before BEM assembly",
            "record BEM source-balance summary keys surface_mesh_id, surface_mesh_digest, surface_row_count, source_balance_artifact_id, source_balance_digest, source_convention, total_area_m2, normal_convention, source_balance_unit, signed_charge_balance_abs, and signed_charge_balance_rel_tol before demag-margin notebook promotion",
            "record BEM source row identity keys surface_source_artifact_id, magnetization_source_id, material_id, and material_name before accepting sigma_m = M dot n rows",
            "estimate permeance coefficient Pc from magnet length, effective gap, and iron path before the run",
            "record B_gap and H_m=(B_gap-Br)/(mu0*mu_rec) and compare H_m with the irreversible-demag knee",
            "lint PM recoil/knee steps with HBRM/HBCN before running a demag sweep",
            "run pm_recoil_demag_step_summary on steps 0/1/2 before accepting step-2 recovery",
            "promote parsed RunResult rows through run_result_loadline_handoff before showing load-line notebooks",
            "bundle RunResult, load-line metadata, BEM surface metadata, and recoil steps through pm_demag_package_identity_gate before demag notebook promotion",
            "bundle load-line sweep, negative-Id fault screening, BEM source balance, and demag package through pm_demag_margin_screening_package_gate before demag-margin notebook promotion",
            "when a hot material state is recorded, keep Br_T, H_knee_A_per_m, and recoil_mu_r identical across the package",
            "map short-circuit and field-weakening negative-Id rows to the same field_probe and HBCN demag-step contract",
            "record field_probe_output_artifact_id, field_probe_output_digest, and field_probe_output_path for the exported probe table before accepting demag-margin screening rows",
            "treat load-line margin as an upper-bound precheck; product/local field results must confirm the worst magnet element",
        ],
        "quality_gates": [
            "hot Br and Hcj assumptions are recorded",
            "load-line table metadata declares columns, H/B/temperature units, magnetization axis, knee reference, and demag sign convention",
            "PM BEM surface rows declare outward_from_magnet normals and have zero closed-surface signed-charge proxy",
            "PM BEM surface source balance gate passes: sum_i area_i*(M dot n) is near zero for each closed magnet",
            "PM BEM source-balance summary records surface area, normal convention, source unit, absolute balance residual, and relative tolerance",
            "permeance-coefficient load-line precheck is recorded before claiming demag safety",
            "HBRM/HBCN step contract is complete for every PM material id used in a demag sweep",
            "step-2 recovery is checked by a recoil-remanence ratio gate after any knee crossing",
            "RunResult load-line rows have case_id, H/B/temperature units, knee reference, recoil_mu_r, and demag sign convention",
            "RunResult/load-line/BEM/recoil artifacts share case_id and magnet_id before demag notebook use",
            "load-line sweep, fault-current screening, BEM source balance, and demag package share case_id, magnet_id, and temperature_C before demag-margin notebook use",
            "load-line sweep, fault-current screening, BEM source balance, and demag package share the same Br_T/H_knee_A_per_m/recoil_mu_r material state when recorded",
            "field-probe rows record output artifact id, digest, and path before any notebook or LLM handoff reads the demag-margin value",
            "negative d-axis current cases are separated from nominal MTPA cases",
            "irreversible demag claim requires local validated field results",
            "magnet supplier grade data stays separate from public examples unless licensed for publication",
        ],
    }


def build_motor_drive_cycle_plan(
    target_market: str = "robot_drone",
    rated_torque_nm: float = 0.6,
    peak_torque_nm: float = 1.2,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
) -> dict[str, Any]:
    """Build operating points and weights for drive-cycle evaluation."""
    market = (target_market or "robot_drone").strip().lower()
    if market == "industrial_servo":
        raw_points = [
            ("idle_hold", 0.20, 0.0, 0.15),
            ("rated_move", 1.00, 0.7, 0.45),
            ("accel_peak", 0.65, 1.0, 0.20),
            ("field_weakening", 1.00, 0.35, 0.20),
        ]
    else:
        raw_points = [
            ("idle_spin", 0.20, 0.05, 0.10),
            ("hover", 0.45, 0.45, 0.50),
            ("climb", 0.70, 0.75, 0.25),
            ("burst", 1.00, 1.00, 0.15),
        ]
    points = []
    for name, speed_scale, torque_scale, weight in raw_points:
        torque_ref = peak_torque_nm if torque_scale > 0.9 else rated_torque_nm
        speed = max_speed_rpm * speed_scale if speed_scale > 0.9 else base_speed_rpm * speed_scale
        torque = torque_ref * torque_scale
        points.append(
            {
                "point_id": name,
                "speed_rpm": round(speed, 6),
                "torque_nm": round(torque, 6),
                "weight": weight,
                "mechanical_power_w": round(torque * 2.0 * pi * speed / 60.0, 6),
            }
        )
    return {
        "schema_version": "elf-python-motor-drive-cycle-plan/v1",
        "target_market": market,
        "rated_torque_nm": float(rated_torque_nm),
        "peak_torque_nm": float(peak_torque_nm),
        "base_speed_rpm": float(base_speed_rpm),
        "max_speed_rpm": float(max_speed_rpm),
        "operating_points": points,
        "weighted_outputs": [
            "cycle_efficiency",
            "weighted_total_loss_w",
            "peak_temperature_input_w",
            "worst_voltage_margin",
            "worst_current_margin",
        ],
        "quality_gates": [
            "weights sum to one or are normalized before scoring",
            "run drive_cycle_weighted_efficiency_gate on normalized result rows before ranking cycle_efficiency",
            "peak and continuous points are labeled separately",
            "efficiency map interpolation records nearest solved points",
            "thermal/NVH/stress follow-up uses weighted and worst-case points",
        ],
    }


def build_motor_optimization_study_plan(
    motor_type: str = "spm",
    objective: str = "cycle_efficiency",
    budget: int = 48,
    target_market: str = "robot_drone",
) -> dict[str, Any]:
    """Build a constrained motor optimization plan."""
    family = _infer_motor_type(motor_type, "spm")
    variables = list(MOTOR_DESIGN_VARIABLES.get(family, MOTOR_DESIGN_VARIABLES["spm"]))
    topology = build_motor_topology_parameter_plan(motor_type=family)
    selected = variables[:3] + topology["parameters"][:3]
    return {
        "schema_version": "elf-python-motor-optimization-study-plan/v1",
        "motor_type": family,
        "objective": objective,
        "target_market": target_market,
        "budget": max(int(budget), 1),
        "design_variables": selected,
        "constraints": [
            "torque target is met at required operating points",
            "current and voltage limits are not violated",
            "efficiency-map feasible labels are respected",
            "demag risk label is not red for PM machines",
            "thermal/NVH/stress validation plans are attached before prototype handoff",
            "manufacturing variables remain inside tolerance-ready ranges",
        ],
        "ranking_outputs": [
            "objective_value",
            "constraint_violation_count",
            "best_efficiency_point",
            "cycle_efficiency",
            "torque_ripple_label",
            "material_cost_proxy",
            "validation_readiness_label",
        ],
        "workflow": [
            "build topology parameter plan",
            "build winding layout plan",
            "build efficiency map plan and drive-cycle plan",
            "run DOE or optimizer over selected variables",
            "parse local RunResult into map/loss/dq contracts",
            "rank candidates with explicit constraint labels",
            "promote finalists to NGSolve thermal/NVH/stress validation",
        ],
    }


def build_motor_voltage_field_weakening_plan(
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
) -> dict[str, Any]:
    """Build a voltage-limit and field-weakening design contract."""
    family = _infer_motor_type(motor_type, "ipm")
    pp = max(int(pole_pairs), 1)
    current_limit = max(float(current_limit_a_peak), 0.0)
    vdc = max(float(dc_bus_v), 1.0)
    v_phase_peak_limit = vdc / (3.0 ** 0.5)
    dq_plan = build_motor_dq_axis_map_plan(
        motor_type=family,
        pole_pairs=pp,
        current_limit_a_peak=current_limit,
        id_points=3,
        iq_points=3,
        ld_h=ld_h,
        lq_h=lq_h,
        pm_flux_wb=pm_flux_wb,
    )
    params = dq_plan["dq_parameters"]
    ld = max(float(params["ld_h"]), 1.0e-9)
    lq = max(float(params["lq_h"]), 1.0e-9)
    psi = float(params["pm_flux_wb"])
    speeds = _linspace(max(float(speed_min_rpm), 0.0), max(float(speed_max_rpm), 0.0), speed_points)
    rows = []
    for speed in speeds:
        omega_m = 2.0 * pi * speed / 60.0
        omega_e = omega_m * pp
        emf_proxy_v = abs(omega_e * psi)
        q_axis_reactance_v = abs(omega_e * lq * current_limit)
        voltage_proxy_v = hypot(emf_proxy_v, q_axis_reactance_v)
        margin_v = v_phase_peak_limit - voltage_proxy_v
        required_negative_id = 0.0
        if margin_v < 0.0 and omega_e > 0.0 and psi > 0.0:
            required_negative_id = min(current_limit, max(0.0, (voltage_proxy_v - v_phase_peak_limit) / (omega_e * ld)))
        rows.append(
            {
                "speed_rpm": round(speed, 6),
                "electrical_frequency_hz": round(speed * pp / 60.0, 6),
                "emf_proxy_v_peak": round(emf_proxy_v, 6),
                "q_axis_reactance_proxy_v_peak": round(q_axis_reactance_v, 6),
                "voltage_proxy_v_peak": round(voltage_proxy_v, 6),
                "voltage_limit_v_peak": round(v_phase_peak_limit, 6),
                "voltage_margin_v_peak": round(margin_v, 6),
                "required_negative_id_a_peak_proxy": round(required_negative_id, 6),
                "region": "field_weakening_required" if required_negative_id > 0 else "voltage_margin_ok",
            }
        )
    return {
        "schema_version": "elf-python-motor-voltage-field-weakening-plan/v1",
        "motor_type": family,
        "pole_pairs": pp,
        "dc_bus_v": vdc,
        "current_limit_a_peak": current_limit,
        "v_phase_peak_limit": v_phase_peak_limit,
        "dq_parameters": params,
        "rows": rows,
        "required_observables": [
            "back_emf_constant",
            "flux_linkage",
            "ld_lq",
            "voltage_margin_proxy",
            "current_margin_proxy",
        ],
        "quality_gates": [
            "voltage limit convention is documented before comparing maps",
            "back-EMF constant is confirmed from local parsed flux linkage",
            "negative Id candidates also pass demag margin screening",
            "field-weakening points are linked to efficiency and thermal checks",
        ],
    }


def build_motor_cogging_ripple_plan(
    motor_type: str = "spm",
    stator_slots: int = 48,
    pole_pairs: int = 4,
    magnet_arc_fraction: float = 0.75,
    skew_fraction: float = 0.0,
) -> dict[str, Any]:
    """Build a cogging torque and torque-ripple reduction contract."""
    family = _infer_motor_type(motor_type, "spm")
    slots = max(int(stator_slots), 3)
    poles = 2 * max(int(pole_pairs), 1)
    cogging_period_slots = slots // gcd(slots, poles)
    cogging_order_mech = slots * poles // gcd(slots, poles)
    mitigation_variables = [
        {"name": "magnet_arc_fraction", "default": float(magnet_arc_fraction), "range": (0.55, 0.95), "affects": ("cogging_torque", "back_emf_constant")},
        {"name": "slot_opening_fraction", "default": 0.20, "range": (0.05, 0.45), "affects": ("cogging_torque", "winding_insertability")},
        {"name": "skew_fraction", "default": float(skew_fraction), "range": (0.0, 1.0), "affects": ("cogging_torque", "torque_ripple", "average_torque")},
        {"name": "current_angle_deg", "default": 0.0, "range": (-80.0, 80.0), "affects": ("torque_ripple", "efficiency")},
    ]
    harmonic_orders = sorted({poles, slots, abs(slots - poles), slots + poles, cogging_order_mech, 2 * cogging_order_mech})
    return {
        "schema_version": "elf-python-motor-cogging-ripple-plan/v1",
        "motor_type": family,
        "stator_slots": slots,
        "poles": poles,
        "cogging_order_mechanical": cogging_order_mech,
        "cogging_period_slots": cogging_period_slots,
        "harmonic_orders": harmonic_orders,
        "mitigation_variables": mitigation_variables,
        "recommended_studies": [
            "static_torque_angle",
            "cogging_torque",
            "back_emf_speed_sweep",
        ],
        "parser_keys": [
            "average_torque_nm",
            "torque_ripple_percent",
            "cogging_torque_peak_to_peak_nm",
            "back_emf_thd_proxy",
        ],
        "quality_gates": [
            "open-circuit cogging and loaded torque ripple are reported separately",
            "torque-angle sampling covers an integer cogging period",
            "average torque loss is reported with every ripple mitigation",
            "airgap harmonic orders are passed to NVH validation",
        ],
    }


def build_motor_airgap_harmonics_nvh_plan(
    motor_type: str = "spm",
    stator_slots: int = 48,
    pole_pairs: int = 4,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
) -> dict[str, Any]:
    """Build air-gap harmonic and NVH force-order routing."""
    family = _infer_motor_type(motor_type, "spm")
    slots = max(int(stator_slots), 3)
    pp = max(int(pole_pairs), 1)
    poles = 2 * pp
    cogging_order = slots * poles // gcd(slots, poles)
    mechanical_orders = sorted({poles, slots, abs(slots - poles), slots + poles, cogging_order})
    speed_rows = []
    for label, speed in (("base", float(base_speed_rpm)), ("max", float(max_speed_rpm))):
        mech_hz = max(speed, 0.0) / 60.0
        speed_rows.append(
            {
                "label": label,
                "speed_rpm": speed,
                "electrical_frequency_hz": round(mech_hz * pp, 6),
                "slot_pass_frequency_hz": round(mech_hz * slots, 6),
                "force_order_frequencies_hz": [
                    {"order": order, "frequency_hz": round(order * mech_hz, 6)}
                    for order in mechanical_orders
                ],
            }
        )
    return {
        "schema_version": "elf-python-motor-airgap-harmonics-nvh-plan/v1",
        "motor_type": family,
        "stator_slots": slots,
        "pole_pairs": pp,
        "mechanical_force_orders": mechanical_orders,
        "speed_rows": speed_rows,
        "required_observables": [
            "airgap_flux_density_harmonics",
            "radial_force_order_proxy",
            "torque_ripple",
            "cogging_torque",
        ],
        "ngsolve_follow_up": [
            "modal separation check at listed force-order frequencies",
            "structural-acoustic proxy when force order approaches a mode",
            "stress check for skew or sleeve changes used to reduce harmonics",
        ],
        "quality_gates": [
            "force orders are tied to speed and slot/pole combination",
            "orders near known structural modes are flagged before prototype handoff",
            "NVH claims require NGSolve modal/order validation after local electromagnetic parsing",
        ],
    }


def build_motor_thermal_network_plan(
    target_market: str = "robot_drone",
    total_loss_w: float = 25.0,
    ambient_c: float = 25.0,
    cooling_h_w_m2k: float = 35.0,
) -> dict[str, Any]:
    """Build a reduced thermal-network plan for motor design scoring."""
    market = (target_market or "robot_drone").strip().lower()
    loss = max(float(total_loss_w), 0.0)
    cooling = max(float(cooling_h_w_m2k), 1.0)
    nodes = [
        {"node": "winding", "loss_fraction": 0.45, "thermal_resistance_k_per_w": 1.2},
        {"node": "stator_core", "loss_fraction": 0.25, "thermal_resistance_k_per_w": 0.8},
        {"node": "rotor_or_magnet", "loss_fraction": 0.15, "thermal_resistance_k_per_w": 1.6},
        {"node": "case_or_air", "loss_fraction": 0.15, "thermal_resistance_k_per_w": 35.0 / cooling},
    ]
    for node in nodes:
        node_loss = loss * node["loss_fraction"]
        node["loss_w"] = round(node_loss, 6)
        node["temperature_rise_c_proxy"] = round(node_loss * node["thermal_resistance_k_per_w"], 6)
        node["temperature_c_proxy"] = round(float(ambient_c) + node["temperature_rise_c_proxy"], 6)
    return {
        "schema_version": "elf-python-motor-thermal-network-plan/v1",
        "target_market": market,
        "total_loss_w": loss,
        "ambient_c": float(ambient_c),
        "cooling_h_w_m2k": cooling,
        "nodes": nodes,
        "required_inputs": [
            "copper_loss_w",
            "iron_loss_w",
            "magnet_or_rotor_loss_w",
            "mechanical_loss_w",
            "duty_cycle_or_drive_cycle_weights",
        ],
        "ngsolve_follow_up": [
            "convert loss terms to heat-source regions",
            "solve H1 heat equation with cooling boundary",
            "compare worst node temperature against material and magnet limits",
        ],
        "quality_gates": [
            "thermal network is used as screening only",
            "loss fractions are replaced by parsed/local loss terms when available",
            "continuous and peak duty points are evaluated separately",
            "NGSolve thermal validation is required before prototype thermal claims",
        ],
    }


def build_motor_manufacturing_tolerance_plan(
    motor_type: str = "spm",
    airgap_mm: float = 0.8,
    production_intent: str = "prototype_small_lot",
) -> dict[str, Any]:
    """Build a manufacturing tolerance and robustness DOE contract."""
    family = _infer_motor_type(motor_type, "spm")
    gap = max(float(airgap_mm), 0.05)
    intent = (production_intent or "prototype_small_lot").strip().lower()
    if intent not in {"concept", "prototype_small_lot", "mass_production"}:
        intent = "prototype_small_lot"
    scale = 1.0 if intent == "prototype_small_lot" else (0.5 if intent == "concept" else 1.5)
    variables = [
        {"name": "airgap_offset_mm", "default": 0.0, "range": (-0.10 * scale, 0.10 * scale), "affects": ("cogging_torque", "torque_ripple", "radial_force")},
        {"name": "eccentricity_mm", "default": 0.0, "range": (0.0, min(0.25 * gap, 0.20 * scale)), "affects": ("unbalanced_force", "airgap_harmonics")},
        {"name": "magnet_arc_error_deg", "default": 0.0, "range": (-1.5 * scale, 1.5 * scale), "affects": ("back_emf_constant", "cogging_torque")},
        {"name": "slot_opening_error_mm", "default": 0.0, "range": (-0.05 * scale, 0.05 * scale), "affects": ("cogging_torque", "manufacturing_fit")},
        {"name": "stack_length_error_mm", "default": 0.0, "range": (-0.20 * scale, 0.20 * scale), "affects": ("torque", "thermal_mass")},
    ]
    rows = [{"case": "nominal", "changes": {var["name"]: var["default"] for var in variables}}]
    for var in variables:
        low, high = var["range"]
        rows.append({"case": f"{var['name']}_low", "changes": {var["name"]: low}})
        rows.append({"case": f"{var['name']}_high", "changes": {var["name"]: high}})
    return {
        "schema_version": "elf-python-motor-manufacturing-tolerance-plan/v1",
        "motor_type": family,
        "airgap_mm": gap,
        "production_intent": intent,
        "tolerance_variables": variables,
        "doe_rows": rows,
        "required_observables": [
            "back_emf_constant",
            "torque",
            "torque_ripple",
            "cogging_torque",
            "airgap_harmonics",
            "force_order_proxy",
        ],
        "quality_gates": [
            "nominal design is frozen before tolerance DOE",
            "worst-case and one-at-a-time tolerance effects are separated",
            "unbalanced-force/eccentricity cases route to NVH and stress validation",
            "prototype handoff includes inspection dimensions and tolerance labels",
        ],
    }


def build_motor_observable_contract(
    motor_type: str = "spm",
    study: str = "static_flux_linkage",
) -> dict[str, Any]:
    """Map a motor study to observables, ELF markers, parser keys, and validation."""
    family = _infer_motor_type(motor_type, "spm")
    study_name = study.strip().lower() or "static_flux_linkage"
    if study_name not in STUDY_TYPES:
        study_name = "static_flux_linkage"
    if study_name == "back_emf_speed_sweep":
        observables = ("flux_linkage", "back_emf_constant")
        validation = (
            "flux sign",
            "flux_linkage_back_emf_derivative_gate before Ke export",
            "phase symmetry",
        )
        age_targets = ("back_emf", "airgap_harmonics", "flux_linkage_back_emf_derivative_gate")
    elif study_name == "static_torque_angle":
        observables = ("torque", "torque_ripple", "flux_linkage")
        validation = ("torque sign", "periodicity", "co-energy trend")
        age_targets = ("torque", "airgap_harmonics")
    elif study_name == "dq_inductance":
        observables = ("ld_lq", "flux_linkage", "torque")
        validation = ("current perturbation linearity", "Ld/Lq ordering", "MTPA trend")
        age_targets = ("dq_inductance", "mtpa")
    elif study_name == "force_gap_sweep":
        observables = ("force", "field_probe", "convergence_status")
        validation = (
            "force sign",
            "axis/component mapping",
            "force quantity dimension declared before comparison",
            "gap monotonicity",
            "dipole-limit F*s^4 scaling when applicable",
        )
        age_targets = ("magnet_force", "bem_scalar_potential", "coaxial_pm_force_gap_sweep")
    elif study_name == "induction_slip_loss":
        observables = ("torque", "loss_proxy", "field_probe")
        validation = ("slip monotonicity near zero", "loss nonnegative", "frequency trend")
        age_targets = ("induction_slip", "eddy_current")
    elif study_name == "ac_loss_frequency_sweep":
        observables = ("loss_proxy", "field_probe")
        validation = ("frequency trend", "loss nonnegative", "material conductivity trend")
        age_targets = ("eddy_current", "loss")
    else:
        observables = MOTOR_DEFAULT_OBSERVABLES.get(family, MOTOR_DEFAULT_OBSERVABLES["spm"])
        validation = (
            "observable present",
            "sign/scale plausible",
            "mutual-flux sign and current-scaling gate",
            "no convergence warnings",
        )
        age_targets = ("airgap_field",)
    force_result_contract = None
    if "force" in observables:
        force_result_contract = {
            "schema_version": "elf-python-force-observable-package-contract/v1",
            "required_metadata": [
                "case_id",
                "result_set_id",
                "run_artifact_id",
                "result_revision_id",
                "observable_id",
                "operating_point_id",
                "source_function",
                "quantity_dimension",
                "force_unit",
                "component_frame",
                "sign_convention",
            ],
            "allowed_quantity_dimensions": [
                "2d_per_length",
                "3d_total",
            ],
            "allowed_force_units": [
                "N/m",
                "N",
            ],
            "per_length_parser_keys": [
                "force_x_n_per_m",
                "force_y_n_per_m",
                "force_z_n_per_m",
                "radial_force_n_per_m",
            ],
            "total_force_parser_keys": [
                "force_x_n",
                "force_y_n",
                "force_z_n",
            ],
            "component_frames": [
                "global_xyz",
                "global_xy",
                "local_normal_tangent",
                "as_exported_with_map",
            ],
            "public_gate_candidates": [
                "parallel_wire_force_result_package_gate",
                "jmag_force_table_metadata_gate",
                "maxwell_stress_surface_package_gate",
                "force_moment_resultant_summary",
            ],
            "negative_controls": [
                "2d_per_length row reported as N without explicit depth",
                "stale case_id or operating_point_id",
                "stale run_artifact_id or result_revision_id",
                "missing component_frame",
                "sign convention omitted for attractive/repulsive sweeps",
            ],
        }
    return {
        "schema_version": "elf-python-motor-observable-contract/v1",
        "motor_type": family,
        "study": study_name,
        "observables": list(observables),
        "elf_markers": {obs: list(OBSERVABLE_MARKERS.get(obs, ())) for obs in observables},
        "run_result_keys": [
            "status",
            "generated_files",
            "parsed_observables",
            "warnings",
            "validation_labels",
        ],
        "parser_observable_keys": [f"{obs}_value" for obs in observables],
        "validation_checks": list(validation),
        "age_targets": list(age_targets),
        "force_result_contract": force_result_contract,
        "public_boundary": "Contract only; no product execution or raw solver output is included.",
    }


def build_motor_market_brief(
    target_market: str = "robot_drone",
    motor_type: str = "",
    rotor_topology: str = "",
) -> dict[str, Any]:
    """Build a market/application brief for motor-design agents."""
    market_key = (target_market or "robot_drone").strip().lower()
    profile = TARGET_MARKET_PROFILES.get(market_key, TARGET_MARKET_PROFILES["robot_drone"])
    family = _infer_motor_type(motor_type or profile["default_motor_type"], profile["default_motor_type"])
    topology = (rotor_topology or profile["default_rotor_topology"]).strip().lower()
    if topology not in {"outer_rotor", "inner_rotor", "linear", "axial_flux"}:
        topology = profile["default_rotor_topology"]
    objective = "back_emf_target" if family in PM_MOTOR_TYPES else "torque_density"
    if market_key == "robot_drone":
        objective = "ripple_reduction" if "low_ripple" in profile["design_priorities"] else objective
    return {
        "schema_version": "elf-python-motor-market-brief/v1",
        "target_market": market_key,
        "display": profile["display"],
        "motor_type": family,
        "rotor_topology": topology,
        "spec_intake_fields": profile["spec_fields"],
        "design_priorities": profile["design_priorities"],
        "preferred_topologies": profile["preferred_topologies"],
        "recommended_objective": objective,
        "recommended_first_calls": [
            f'elf_python_motor_design_plan("<goal>", motor_type="{family}", objective="{objective}")',
            f'elf_python_meg_generation_plan("<geometry goal>", dimension="2d")',
            f'elf_python_2d_motor_template("{family}")',
            f'elf_python_motor_sweep_matrix(motor_type="{family}", objective="{objective}", budget=9)',
            f'elf_python_motor_observable_contract(motor_type="{family}", study="static_torque_angle")',
        ],
        "user_experience_policy": [
            "End users provide specifications and review drawings/results; they do not need to operate analysis software directly.",
            "A user-local backend may execute the licensed product through an agent-controlled contract.",
            "The public MCP layer returns schemas, deck contracts, and validation routing only.",
        ],
    }


def build_motor_design_agent_handoff(
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
) -> dict[str, Any]:
    """Build a full spec-to-design-agent handoff for motor workflows."""
    brief = build_motor_market_brief(target_market, motor_type, rotor_topology)
    family = brief["motor_type"]
    objective = brief["recommended_objective"]
    design_plan = build_motor_design_plan(goal, motor_type=family, objective=objective)
    dimension = "2d" if rotor_topology in {"outer_rotor", "inner_rotor"} else "3d"
    meg_plan = build_meg_generation_plan(goal, dimension=dimension)
    sweep = build_motor_sweep_matrix(family, objective=objective, budget=9)
    primary_study = design_plan["recommended_studies"][0]
    observable_contract = build_motor_observable_contract(family, primary_study)
    spec_values = {
        "continuous_torque_nm": continuous_torque_nm,
        "base_speed_rpm": base_speed_rpm,
        "dc_bus_v": dc_bus_v,
        "outer_diameter_mm": outer_diameter_mm,
        "stack_length_mm": stack_length_mm,
        "cooling_mode": cooling_mode,
    }
    missing = [key for key, value in spec_values.items() if value in {0, 0.0, ""}]
    ngsolve_multiphysics_route = {
        "nvh": "required NGSolve harmonic/structural-acoustic validation after torque ripple, cogging, and force-order proxies are known",
        "thermal": "required NGSolve thermal validation using loss proxies, duty-cycle data, cooling mode, and material assumptions after local RunResult parsing",
        "stress": "required NGSolve mechanical stress validation for rotor speed, bridge/sleeve margin, magnet retention, shaft, and hub risks",
        "preferred_validation": "public quick checks first, then AGE/numeric electromagnetic trend checks, then NGSolve NVH/thermal/stress validation, then local/private product run comparison",
    }
    return {
        "schema_version": "elf-python-motor-design-agent-handoff/v1",
        "goal": goal,
        "brief": brief,
        "spec_values": spec_values,
        "missing_spec_fields": missing,
        "design_plan": design_plan,
        "meg_generation_plan": meg_plan,
        "sweep_matrix": sweep,
        "observable_contract": observable_contract,
        "deliverables": DESIGN_AGENT_DELIVERABLES,
        "analysis_routing": {
            "elf_magic_local_backend": [
                "author or mutate public .mai/.meg decks",
                "run product solver only in a user-local licensed environment",
                "parse RunResult observables and warnings",
            ],
            "open_validation_backend": [
                "MMM sign/scale quick check",
                "AGE or numeric invariant route for independent trend validation",
                "required NGSolve NVH / thermal / stress validation after observables are parsed",
            ],
            "ngsolve_multiphysics": ngsolve_multiphysics_route,
        },
        "manufacturing_handoff": {
            "drawing_intent": [
                "2D cross-section with rotor/stator/slot/magnet/coil region labels",
                "critical dimensions with units and tolerances to be filled by downstream CAD",
                "magnet polarity and winding phase labels",
            ],
            "bom_intent": [
                "magnet grade placeholder",
                "laminated steel placeholder",
                "coil wire/current density placeholder",
                "shaft/hub/back-iron material placeholder",
            ],
            "prototype_gate": [
                "spec completeness",
                "deck lint PASS",
                "sweep matrix complete",
                "observable contract selected",
                "NGSolve NVH/thermal/stress validation plan selected",
                "validation labels attached",
            ],
        },
        "public_boundary": (
            "This is an agent handoff contract. It does not execute licensed "
            "software, expose product internals, or include raw solver outputs."
        ),
    }


def build_motor_feasibility_study(
    goal: str,
    target_market: str = "robot_drone",
    motor_type: str = "spm",
    production_intent: str = "prototype_small_lot",
) -> dict[str, Any]:
    """Build a feasibility/QA study plan for prototype and small-lot production."""
    brief = build_motor_market_brief(target_market, motor_type, "")
    family = brief["motor_type"]
    objective = brief["recommended_objective"]
    design_plan = build_motor_design_plan(goal, motor_type=family, objective=objective)
    selected_lanes = FEASIBILITY_LANES
    if production_intent not in {"concept", "prototype_small_lot", "mass_production"}:
        production_intent = "prototype_small_lot"
    extra_gates = []
    if production_intent == "mass_production":
        extra_gates = [
            "statistical tolerance and supplier variation plan",
            "thermal/NVH/stress sign-off by accountable downstream reviewers",
            "manufacturing inspection and traceability plan",
        ]
    elif production_intent == "prototype_small_lot":
        extra_gates = [
            "prototype drawing/BOM review",
            "local product-run smoke plus independent trend validation",
            "NGSolve thermal/NVH/stress risk register before procurement",
        ]
    else:
        extra_gates = [
            "concept sign/scale validation",
            "missing spec questions before procurement",
        ]
    return {
        "schema_version": "elf-python-motor-feasibility-study/v1",
        "goal": goal,
        "target_market": brief["target_market"],
        "motor_type": family,
        "production_intent": production_intent,
        "design_objective": objective,
        "lanes": selected_lanes,
        "design_variables": design_plan["design_variables"],
        "extra_quality_gates": extra_gates,
        "mcp_can_do": [
            "normalize specifications",
            "route to public decks and Python facade schemas",
            "prepare local backend RunRequest contracts",
            "define observable parser keys and validation gates",
            "prepare material-variation, required NGSolve NVH/thermal/stress, drawing, BOM, and prototype handoffs",
        ],
        "mcp_cannot_claim_alone": [
            "mass-production warranty",
            "final mechanical stress sign-off",
            "final thermal/NVH qualification",
            "product-license rights or customer contractual permission",
        ],
        "public_boundary": (
            "Feasibility plan only. Product execution, raw run outputs, final "
            "warranty, and contractual sign-off remain local/private or governed "
            "by the parties' agreement."
        ),
    }


def build_motor_material_variation_plan(
    motor_type: str = "spm",
    focus: str = "all",
) -> dict[str, Any]:
    """Build a public material variation plan for motor design studies."""
    family = _infer_motor_type(motor_type, "spm")
    focus_key = (focus or "all").strip().lower()
    if focus_key in {"pm", "permanent_magnet"}:
        focus_key = "magnet"
    groups = MATERIAL_VARIATION_CATALOG
    if focus_key != "all":
        groups = {focus_key: MATERIAL_VARIATION_CATALOG.get(focus_key, ())}
    rows = []
    for group, variables in groups.items():
        for variable in variables:
            rows.append({"group": group, **variable})
    observables = list(MOTOR_DEFAULT_OBSERVABLES.get(family, MOTOR_DEFAULT_OBSERVABLES["spm"]))
    if "loss_proxy" not in observables:
        observables.append("loss_proxy")
    if "field_probe" not in observables:
        observables.append("field_probe")
    return {
        "schema_version": "elf-python-motor-material-variation/v1",
        "motor_type": family,
        "focus": focus_key,
        "variables": rows,
        "recommended_observables": observables,
        "study_rules": [
            "vary one material group at a time before interaction studies",
            "keep geometry fixed for first material sensitivity sweep",
            "record hot/cold or supplier-grade assumptions explicitly",
            "do not claim material qualification from proxy checks alone",
        ],
    }


def build_license_governance_note(
    collaboration_mode: str = "joint_research",
) -> dict[str, Any]:
    """Build a public-safe license/governance note for MCP + product backends."""
    mode = (collaboration_mode or "joint_research").strip().lower()
    if mode not in {"joint_research", "customer_project", "internal_lab", "public_demo"}:
        mode = "joint_research"
    mode_rules = {
        "joint_research": [
            "write down which party may run the licensed backend",
            "write down ownership and publication rules for generated design data",
            "separate public MCP improvements from private product-run outputs",
        ],
        "customer_project": [
            "confirm product-license terms before using a backend for paid prototype work",
            "keep customer specs and run outputs out of the public repository",
            "deliver scrubbed design artifacts only after customer approval",
        ],
        "internal_lab": [
            "keep license seats and run logs inside the lab/private workspace",
            "promote only generic API/schema improvements to public MCP",
        ],
        "public_demo": [
            "use public sample decks and synthetic specs only",
            "do not imply product execution rights or performance warranty",
        ],
    }
    return {
        "schema_version": "elf-python-license-governance/v1",
        "collaboration_mode": mode,
        "topics": LICENSE_GOVERNANCE_TOPICS,
        "mode_rules": mode_rules[mode],
        "public_boundary": (
            "This is not legal advice. It is an engineering governance checklist "
            "for separating public MCP code from licensed product execution and "
            "private project data."
        ),
    }


def build_2d_motor_template(
    motor_type: str = "spm",
    pole_pairs: int = 4,
    stator_slots: int = 48,
) -> dict[str, Any]:
    """Build a constrained 2D motor geometry template for LLM-assisted drafting."""
    family = motor_type.strip().lower() or "spm"
    if family not in MOTOR_TYPES:
        family = "spm"
    pp = max(1, int(pole_pairs))
    slots = max(3, int(stator_slots))
    rotor_features: list[dict[str, Any]]
    if family in {"spm", "bldc", "slotless_pm", "axial_flux_pm", "linear_pm", "stepper"}:
        rotor_features = [
            {
                "name": "surface_pm_pole",
                "count": 2 * pp,
                "material_role": "permanent_magnet",
                "angle_span_fraction_of_pole_pitch": 0.72,
                "radial_layer": "surface_pm",
            }
        ]
    elif family in {"ipm", "pm_assisted_synrm", "line_start_pm"}:
        rotor_features = [
            {
                "name": "buried_pm_barrier",
                "count": 2 * pp,
                "material_role": "permanent_magnet",
                "angle_span_fraction_of_pole_pitch": 0.55,
                "radial_layer": "ipm_pocket",
            }
        ]
        if family == "line_start_pm":
            rotor_features.append(
                {
                    "name": "line_start_cage_bar",
                    "count": max(2 * pp * 5, slots // 2),
                    "material_role": "conducting_bar",
                    "angle_span_fraction_of_slot_pitch": 0.35,
                    "radial_layer": "rotor_cage",
                }
            )
    elif family in {"induction", "deep_bar_induction"}:
        rotor_features = [
            {
                "name": "deep_rotor_bar" if family == "deep_bar_induction" else "rotor_bar",
                "count": max(2 * pp * 5, slots // 2),
                "material_role": "conducting_bar",
                "angle_span_fraction_of_slot_pitch": 0.45,
                "radial_layer": "rotor_cage",
            }
        ]
    elif family == "flux_switching_pm":
        rotor_features = [
            {
                "name": "salient_rotor_pole",
                "count": 2 * pp,
                "material_role": "rotor_iron",
                "angle_span_fraction_of_pole_pitch": 0.55,
                "radial_layer": "rotor_saliency",
            },
            {
                "name": "stator_pm_piece",
                "count": slots,
                "material_role": "permanent_magnet",
                "angle_span_fraction_of_slot_pitch": 0.30,
                "radial_layer": "stator_tooth_slot",
            },
        ]
    elif family == "vernier_pm":
        rotor_features = [
            {
                "name": "flux_modulation_tooth",
                "count": max(slots, 2 * pp),
                "material_role": "modulation_iron",
                "angle_span_fraction_of_slot_pitch": 0.45,
                "radial_layer": "rotor_feature_layer",
            },
            {
                "name": "vernier_pm_pole",
                "count": 2 * pp,
                "material_role": "permanent_magnet",
                "angle_span_fraction_of_pole_pitch": 0.70,
                "radial_layer": "surface_pm",
            },
        ]
    elif family == "transverse_flux_pm":
        rotor_features = [
            {
                "name": "transverse_flux_module",
                "count": 2 * pp,
                "material_role": "3d_pm_flux_path",
                "angle_span_fraction_of_pole_pitch": 0.60,
                "radial_layer": "rotor_feature_layer",
            }
        ]
    elif family == "claw_pole":
        rotor_features = [
            {
                "name": "claw_pole_tooth",
                "count": 2 * pp,
                "material_role": "wound_field_rotor_iron",
                "angle_span_fraction_of_pole_pitch": 0.55,
                "radial_layer": "rotor_saliency",
            }
        ]
    elif family == "commutator_dc":
        rotor_features = [
            {
                "name": "armature_slot",
                "count": max(slots // 2, 12),
                "material_role": "armature_winding",
                "angle_span_fraction_of_slot_pitch": 0.45,
                "radial_layer": "rotor_feature_layer",
            },
            {
                "name": "field_pole",
                "count": 2 * pp,
                "material_role": "series_or_shunt_field",
                "angle_span_fraction_of_pole_pitch": 0.60,
                "radial_layer": "stator_tooth_slot",
            },
        ]
    else:
        rotor_features = [
            {
                "name": "salient_rotor_pole_or_barrier",
                "count": 2 * pp,
                "material_role": "rotor_iron",
                "angle_span_fraction_of_pole_pitch": 0.55,
                "radial_layer": "rotor_saliency",
            }
        ]

    observables = list(MOTOR_DEFAULT_OBSERVABLES.get(family, MOTOR_DEFAULT_OBSERVABLES["spm"]))
    return {
        "schema_version": "elf-python-2d-motor-template/v1",
        "motor_type": family,
        "pole_pairs": pp,
        "stator_slots": slots,
        "units": "m",
        "coordinate_system": "xy_cross_section",
        "radial_layers": [
            {"name": "shaft_or_inner_air", "r_inner": 0.0, "r_outer": 0.016, "role": "nonmagnetic"},
            {"name": "rotor_core", "r_inner": 0.016, "r_outer": 0.042, "role": "rotor_iron"},
            {"name": "rotor_feature_layer", "r_inner": 0.036, "r_outer": 0.045, "role": "family_specific"},
            {"name": "airgap", "r_inner": 0.045, "r_outer": 0.046, "role": "airgap"},
            {"name": "stator_tooth_slot", "r_inner": 0.046, "r_outer": 0.072, "role": "stator_teeth_and_slots"},
            {"name": "stator_yoke", "r_inner": 0.072, "r_outer": 0.09, "role": "stator_iron"},
            {"name": "exterior_air", "r_inner": 0.09, "r_outer": 0.12, "role": "open_boundary_air"},
        ],
        "angular_features": [
            {
                "name": "stator_slot",
                "count": slots,
                "material_role": "coil_or_air",
                "angle_span_fraction_of_slot_pitch": 0.45,
                "radial_layer": "stator_tooth_slot",
            },
            *rotor_features,
        ],
        "material_roles": [
            "air",
            "stator_iron",
            "rotor_iron",
            "coil_conductor",
            "permanent_magnet",
            "conducting_bar",
            "modulation_iron",
            "armature_winding",
            "series_or_shunt_field",
        ],
        "requested_observables": observables,
        "meg_generation_path": "llm_2d_template_then_netgen_2d_remesh",
        "hard_validation_rules": [
            "all radii must be strictly increasing per layer",
            "airgap thickness must be positive",
            "angular feature counts must be positive integers",
            "region labels must map to ELF/MAGIC element/material roles",
            "generated .mai must request outputs for requested_observables",
            "template is a draft until deck lint and physics trend checks pass",
        ],
    }


def format_python_api_schema(schema: Mapping[str, Any]) -> str:
    """Format the public schema as Markdown."""
    lines = [
        "# ELF Python Facade Schema",
        "",
        f"- schema: `{schema['schema_version']}`",
        "## Policy",
    ]
    for key, value in schema["policy"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Enums"])
    for key, values in schema["enums"].items():
        lines.append(f"- `{key}`: " + ", ".join(f"`{v}`" for v in values))
    lines.extend(["", "## Objects"])
    for key, values in schema["objects"].items():
        lines.append(f"- `{key}`: " + ", ".join(f"`{v}`" for v in values))
    return "\n".join(lines).rstrip()


def format_motor_spec_lint(report: Mapping[str, Any]) -> str:
    """Format a MotorSpec lint report."""
    lines = [
        "# ELF Python MotorSpec Lint",
        "",
        f"- schema: `{report['schema_version']}`",
        f"- status: `{report['status']}`",
        f"- motor type: `{report['motor_type']}`",
        "- recommended observables: "
        + ", ".join(f"`{item}`" for item in report["recommended_observables"]),
        "",
        "## Issues",
    ]
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['field']}`: {issue['message']}")
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip()


def format_deck_lint(report: Mapping[str, Any]) -> str:
    """Format a .mai dry-run lint report."""
    detected = report["detected"]
    sol_blocks = [item[1] if isinstance(item, tuple) else str(item) for item in detected["sol_blocks"]]
    lines = [
        "# ELF Python Deck Lint",
        "",
        f"- schema: `{report['schema_version']}`",
        f"- status: `{report['status']}`",
        "- requested observables: "
        + (", ".join(f"`{item}`" for item in report["requested_observables"]) or "none"),
        "",
        "## Detected Markers",
        "- SOL blocks: " + (", ".join(f"`{item}`" for item in sol_blocks) or "none"),
        f"- FLUM: `{detected['has_flum']}`",
        f"- field output: `{detected['has_field_output']}`",
        f"- force output: `{detected['has_force_output']}`",
        f"- AC markers: `{detected['has_ac_markers']}`",
        "",
        "## Issues",
    ]
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['field']}`: {issue['message']}")
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip()


def format_pm_demag_step_lint(report: Mapping[str, Any]) -> str:
    """Format a PM demagnetization HBRM/HBCN lint report."""

    detected = report["detected"]
    lines = [
        "# ELF Python PM Demag Step Lint",
        "",
        f"- schema: `{report['schema_version']}`",
        f"- status: `{report['status']}`",
        "- complete material ids: "
        + (", ".join(f"`{mid}`" for mid in detected["complete_three_step_mids"]) or "none"),
        "- HBRM curves: "
        + (", ".join(f"`{row['curve_id']}`" for row in detected["hbrm_rows"]) or "none"),
        "- HBCN rows: " + str(len(detected["hbcn_rows"])),
        "",
        "## Contract",
    ]
    lines.extend(f"- {item}" for item in report["contract"])
    lines.extend(["", "## Issues"])
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['field']}`: {issue['message']}")
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip()


def format_run_request_contract(contract: Mapping[str, Any]) -> str:
    """Format a local backend run-request contract."""
    request = contract["run_request"]
    lines = [
        "# ELF Python RunRequest Contract",
        "",
        f"- schema: `{contract['schema_version']}`",
        f"- goal: {contract['goal']}",
        f"- run mode: `{request['run_mode']}`",
        "- source public decks: "
        + (", ".join(f"`{item}`" for item in request["source_public_deck_paths"]) or "none"),
        "- requested observables: "
        + ", ".join(f"`{item}`" for item in request["requested_observables"]),
        f"- privacy policy: `{request['privacy_policy']}`",
        "",
        "## Backend Requirements",
    ]
    lines.extend(f"- {item}" for item in contract["backend_requirements"])
    lines.extend(["", "## MotorSpec Template"])
    template = contract["motor_spec_template"]
    lines.append(f"- motor type: `{template['motor_type']}`")
    lines.append(f"- pole pairs: `{template['pole_pairs']}`")
    lines.append(f"- stator slots: `{template['stator_slots']}`")
    lines.append(f"- air gap: `{template['airgap_m']}` m")
    lines.append(f"- stack length: `{template['stack_length_m']}` m")
    return "\n".join(lines).rstrip()


def format_run_result_parse(parsed: Mapping[str, Any]) -> str:
    """Format parsed RunResult observables."""
    lines = [
        "# ELF Python RunResult Parser",
        "",
        f"- schema: `{parsed['schema_version']}`",
        f"- case id: `{parsed['case_id']}`",
        f"- motor type: `{parsed['motor_type']}`",
        f"- status: `{parsed['status']}`",
        f"- boundary: {parsed['public_boundary']}",
        "",
        "## Parsed Observables",
    ]
    if parsed["parsed_observables"]:
        for key, value in parsed["parsed_observables"].items():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if parsed["warnings"]:
        lines.extend(f"- {item}" for item in parsed["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Validation Labels"])
    lines.extend(f"- `{item}`" for item in parsed["validation_labels"])
    return "\n".join(lines).rstrip()


def format_run_result_path_parse(parsed: Mapping[str, Any]) -> str:
    """Format a user-local run-result path parse summary."""
    lines = [
        "# ELF Python RunResult Path Parser",
        "",
        f"- schema: `{parsed['schema_version']}`",
        f"- source label: `{parsed['source_label']}`",
        f"- motor type: `{parsed['motor_type']}`",
        f"- status: `{parsed['status']}`",
        f"- parsed results: `{len(parsed['parsed_results'])}`",
        f"- boundary: {parsed['public_boundary']}",
        "",
        "## Files Scanned",
    ]
    if parsed["files_scanned"]:
        lines.extend(f"- `{item}`" for item in parsed["files_scanned"])
    else:
        lines.append("- none")
    lines.extend(["", "## Combined Observables"])
    if parsed["combined_observables"]:
        for key, value in parsed["combined_observables"].items():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Parsed Cases"])
    if parsed["parsed_results"]:
        for result in parsed["parsed_results"][:30]:
            source = result.get("source_file", "inline")
            keys = ", ".join(f"`{key}`" for key in result.get("parsed_observables", {}).keys())
            lines.append(
                f"- `{result['case_id']}` from `{source}` status `{result['status']}`: "
                + (keys or "no observables")
            )
    else:
        lines.append("- none")
    if len(parsed["parsed_results"]) > 30:
        lines.append(f"- ... {len(parsed['parsed_results']) - 30} more cases omitted")
    lines.extend(["", "## Warnings"])
    if parsed["warnings"]:
        lines.extend(f"- {item}" for item in parsed["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Validation Labels"])
    lines.extend(f"- `{item}`" for item in parsed["validation_labels"])
    return "\n".join(lines).rstrip()


def format_motor_optimization_loop(loop: Mapping[str, Any]) -> str:
    """Format an optimization loop state."""
    lines = [
        "# ELF Python Motor Optimization Loop",
        "",
        f"- schema: `{loop['schema_version']}`",
        f"- motor type: `{loop['motor_type']}`",
        f"- objective: `{loop['objective']}`",
        f"- budget: `{loop['budget']}`",
        f"- completed results: `{loop['completed_results']}`",
        f"- loop status: `{loop['loop_status']}`",
        f"- boundary: {loop['public_boundary']}",
        "",
        "## Ranked Candidates",
    ]
    if loop["ranked_candidates"]:
        for item in loop["ranked_candidates"]:
            lines.append(
                f"- `{item['case_id']}` status `{item['status']}`, score `{item['score']}`, "
                f"warnings `{item['warning_count']}`"
            )
    else:
        lines.append("- none yet")
    lines.extend(["", "## Next Run Rows"])
    if loop["next_run_rows"]:
        for row in loop["next_run_rows"]:
            lines.append(f"- `{row['case']}`: {row['purpose']}")
    else:
        lines.append("- none; promote best candidate to validation")
    lines.extend(["", "## Promotion Rules"])
    lines.extend(f"- {item}" for item in loop["promotion_rules"])
    return "\n".join(lines).rstrip()


def format_motor_ngsolve_result_crosscheck(crosscheck: Mapping[str, Any]) -> str:
    """Format an NGSolve crosscheck summary."""
    lines = [
        "# ELF Python Motor NGSolve Result Crosscheck",
        "",
        f"- schema: `{crosscheck['schema_version']}`",
        f"- overall status: `{crosscheck['overall_status']}`",
        f"- RunResult status: `{crosscheck['run_result_status']}`",
        f"- case id: `{crosscheck['case_id']}`",
        f"- boundary: {crosscheck['public_boundary']}",
        "",
        "## Lane Checks",
    ]
    if crosscheck["lane_checks"]:
        for item in crosscheck["lane_checks"]:
            lines.append(f"- `{item['lane']}`: `{item['label']}` - {item['reason']}")
    else:
        lines.append("- no NGSolve lane results parsed")
    lines.extend(["", "## Parsed Observable Keys"])
    keys = sorted(crosscheck["parsed_observables"].keys())
    if keys:
        lines.extend(f"- `{key}`" for key in keys)
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in crosscheck["next_actions"])
    return "\n".join(lines).rstrip()


def format_motor_drawing_bom_handoff(handoff: Mapping[str, Any]) -> str:
    """Format drawing and BOM handoff."""
    lines = [
        "# ELF Python Motor Drawing / BOM Handoff",
        "",
        f"- schema: `{handoff['schema_version']}`",
        f"- motor type: `{handoff['motor_type']}`",
        f"- rotor topology: `{handoff['rotor_topology']}`",
        f"- validation label: `{handoff['validation_label']}`",
        f"- boundary: {handoff['public_boundary']}",
        "",
        "## Drawing Views",
    ]
    for view in handoff["drawing_views"]:
        lines.append(f"- `{view['view']}`: " + ", ".join(f"`{item}`" for item in view["contents"]))
    lines.extend(["", "## Key Dimensions"])
    for dim in handoff["key_dimensions"]:
        lines.append(f"- `{dim['name']}`: `{dim['value']}` ({dim['tolerance']})")
    lines.extend(["", "## BOM"])
    for item in handoff["bom"]:
        lines.append(f"- `{item['item']}` x{item['quantity']}: {item['role']} - {item['spec']}")
    lines.extend(["", "## Winding Summary"])
    for key, value in handoff["winding_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Attached Result Summary"])
    for key, value in handoff["attached_result_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Export Intent"])
    lines.extend(f"- {item}" for item in handoff["export_intent"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in handoff["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_operating_point_run_queue(queue: Mapping[str, Any]) -> str:
    """Format operating-point run rows."""
    lines = [
        "# ELF Python Motor Operating-Point Run Queue",
        "",
        f"- schema: `{queue['schema_version']}`",
        f"- motor type: `{queue['motor_type']}`",
        f"- objective: `{queue['objective']}`",
        f"- run rows: `{len(queue['run_rows'])}`",
        f"- boundary: {queue['public_boundary']}",
        "",
        "## Requested Observables",
        ", ".join(f"`{item}`" for item in queue["requested_observables"]),
        "",
        "## Run Rows",
    ]
    for row in queue["run_rows"][:20]:
        lines.append(
            f"- `{row['case_id']}` speed `{row['speed_rpm']}` rpm, "
            f"torque `{row['torque_nm']}` Nm, region `{row['region']}`"
        )
    lines.extend(["", "## Parser Keys"])
    lines.extend(f"- `{item}`" for item in queue["parser_keys"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in queue["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_inverter_pwm_harmonic_plan(plan: Mapping[str, Any]) -> str:
    """Format inverter/PWM harmonic rows."""
    lines = [
        "# ELF Python Motor Inverter / PWM Harmonic Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- modulation: `{plan['modulation']}`",
        f"- switching frequency: `{plan['switching_frequency_hz']}` Hz",
        f"- fundamental frequency: `{plan['fundamental_frequency_hz']}` Hz",
        f"- phase current peak proxy: `{plan['phase_current_a_peak_proxy']}` A",
        f"- boundary: {plan['public_boundary']}",
        "",
        "## Harmonic Rows",
    ]
    for row in plan["harmonic_rows"]:
        lines.append(
            f"- `{row['kind']}` `{row['order']}`: `{row['frequency_hz']}` Hz, "
            f"Irms proxy `{row['phase_current_a_rms_proxy']}` - {row['expected_effect']}"
        )
    lines.extend(["", "## Required Observables"])
    lines.extend(f"- `{item}`" for item in plan["required_observables"])
    lines.extend(["", "## Parser Keys"])
    lines.extend(f"- `{item}`" for item in plan["parser_keys"])
    lines.extend(["", "## Validation Routes"])
    lines.extend(f"- {item}" for item in plan["validation_routes"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_saturation_inductance_map_plan(plan: Mapping[str, Any]) -> str:
    """Format saturated Ld/Lq map planning rows."""
    lines = [
        "# ELF Python Motor Saturation Inductance Map Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- pole pairs: `{plan['pole_pairs']}`",
        f"- current limit: `{plan['current_limit_a_peak']}` A peak",
        f"- rows: `{len(plan['map_rows'])}`",
        f"- boundary: {plan['public_boundary']}",
        "",
        "## Unsaturated Reference",
    ]
    for key, value in plan["unsaturated_reference"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Sample Rows"])
    for row in plan["map_rows"][:12]:
        lines.append(
            f"- `{row['case_id']}` I `{row['current_a_peak']}` A, "
            f"angle `{row['angle_deg_from_q_axis']}` deg, "
            f"Ld `{row['ld_h_proxy']}`, Lq `{row['lq_h_proxy']}`, "
            f"saliency `{row['saliency_ratio_proxy']}`, "
            f"torque proxy `{row['torque_nm_proxy']}`"
        )
    lines.extend(["", "## Parser Keys"])
    lines.extend(f"- `{item}`" for item in plan["parser_keys"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_rotor_stress_retention_plan(plan: Mapping[str, Any]) -> str:
    """Format rotor stress and retention screening plan."""
    lines = [
        "# ELF Python Motor Rotor Stress / Retention Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- rotor topology: `{plan['rotor_topology']}`",
        f"- max speed: `{plan['max_speed_rpm']}` rpm",
        f"- tip speed: `{plan['tip_speed_m_s']}` m/s",
        f"- hoop stress proxy: `{plan['hoop_stress_mpa_proxy']}` MPa",
        f"- retention margin proxy: `{plan['retention_margin_proxy']}`",
        f"- risk label: `{plan['risk_label']}`",
        f"- boundary: {plan['public_boundary']}",
        "",
        "## Required Observables",
    ]
    lines.extend(f"- `{item}`" for item in plan["required_observables"])
    lines.extend(["", "## NGSolve Follow-Up"])
    lines.extend(f"- {item}" for item in plan["ngsolve_follow_up"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_validation_scorecard(scorecard: Mapping[str, Any]) -> str:
    """Format a validation promotion scorecard."""
    lines = [
        "# ELF Python Motor Validation Scorecard",
        "",
        f"- schema: `{scorecard['schema_version']}`",
        f"- overall status: `{scorecard['overall_status']}`",
        f"- score: `{scorecard['score']}`",
        f"- promotion decision: `{scorecard['promotion_decision']}`",
        f"- case id: `{scorecard['case_id']}`",
        f"- crosscheck status: `{scorecard['crosscheck_status']}`",
        f"- boundary: {scorecard['public_boundary']}",
        "",
        "## Gate Results",
    ]
    for gate in scorecard["gate_results"]:
        lines.append(
            f"- `{gate['gate']}`: `{gate['label']}` ({gate['points']} pts) - {gate['detail']}"
        )
    lines.extend(["", "## Parsed Observable Keys"])
    if scorecard["parsed_observable_keys"]:
        lines.extend(f"- `{item}`" for item in scorecard["parsed_observable_keys"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in scorecard["next_actions"])
    return "\n".join(lines).rstrip()


def format_motor_design_plan(plan: Mapping[str, Any]) -> str:
    """Format a motor design API plan."""
    lines = [
        "# ELF Python Motor Design Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- goal: {plan['goal']}",
        f"- motor type: `{plan['motor_type']}`",
        f"- objective: `{plan['objective']}`",
        "- primary observables: " + ", ".join(f"`{item}`" for item in plan["primary_observables"]),
        "- secondary observables: " + ", ".join(f"`{item}`" for item in plan["secondary_observables"]),
        "- recommended studies: " + ", ".join(f"`{item}`" for item in plan["recommended_studies"]),
        f"- acceptance rule: {plan['acceptance_rule']}",
        "",
        "## Design Variables",
    ]
    for var in plan["design_variables"]:
        low, high = var["range"]
        lines.append(
            f"- `{var['name']}` [{var['unit']}]: default `{var['default']}`, "
            f"range `{low}` to `{high}`, affects "
            + ", ".join(f"`{item}`" for item in var["affects"])
        )
    lines.extend(["", "## Python API Sequence"])
    lines.extend(
        f"- `{call.format(goal=plan['goal'], motor_type=plan['motor_type'], objective=plan['objective'], observables=','.join(plan['primary_observables']))}`"
        for call in plan["python_api_sequence"]
    )
    lines.extend(["", "## Validation Gates"])
    lines.extend(f"- {gate}" for gate in plan["validation_gates"])
    return "\n".join(lines).rstrip()


def format_motor_sweep_matrix(matrix: Mapping[str, Any]) -> str:
    """Format a deterministic motor sweep matrix."""
    lines = [
        "# ELF Python Motor Sweep Matrix",
        "",
        f"- schema: `{matrix['schema_version']}`",
        f"- motor type: `{matrix['motor_type']}`",
        f"- objective: `{matrix['objective']}`",
        f"- budget: `{matrix['budget']}`",
        "- observables: " + ", ".join(f"`{item}`" for item in matrix["observables"]),
        "",
        "## Active Variables",
    ]
    for var in matrix["active_variables"]:
        low, high = var["range"]
        lines.append(f"- `{var['name']}` [{var['unit']}], default `{var['default']}`, range `{low}` to `{high}`")
    lines.extend(["", "## Rows"])
    for row in matrix["rows"]:
        changes = ", ".join(f"`{k}`={v}" for k, v in row["changes"].items())
        lines.append(f"- `{row['case']}`: {changes}; {row['purpose']}")
    lines.extend(["", "## Postprocess Rules"])
    lines.extend(f"- {rule}" for rule in matrix["postprocess_rules"])
    return "\n".join(lines).rstrip()


def format_motor_loss_model_contract(contract: Mapping[str, Any]) -> str:
    """Format a motor loss-model contract."""
    lines = [
        "# ELF Python Motor Loss Model Contract",
        "",
        f"- schema: `{contract['schema_version']}`",
        f"- motor type: `{contract['motor_type']}`",
        f"- map type: `{contract['map_type']}`",
        f"- total loss formula: {contract['total_loss_formula']}",
        f"- efficiency formula: {contract['efficiency_formula']}",
        f"- boundary: {contract['public_boundary']}",
        "",
        "## Loss Terms",
    ]
    for term in contract["loss_terms"]:
        lines.append(f"### {term['name']}")
        lines.append(f"- formula: `{term['formula']}`")
        lines.append("- required inputs: " + ", ".join(f"`{item}`" for item in term["required_inputs"]))
        lines.append(f"- source: {term['source']}")
    lines.extend(["", "## Required RunResult Keys"])
    lines.extend(f"- `{key}`" for key in contract["required_runresult_keys"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {gate}" for gate in contract["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_torque_speed_envelope(envelope: Mapping[str, Any]) -> str:
    """Format a motor torque-speed envelope."""
    lines = [
        "# ELF Python Motor Torque-Speed Envelope",
        "",
        f"- schema: `{envelope['schema_version']}`",
        f"- motor type: `{envelope['motor_type']}`",
        f"- peak torque: `{envelope['peak_torque_nm']}` Nm",
        f"- base speed: `{envelope['base_speed_rpm']}` rpm",
        f"- max speed: `{envelope['max_speed_rpm']}` rpm",
        f"- constant power: `{envelope['constant_power_w']}` W",
        f"- DC bus: `{envelope['dc_bus_v']}` V",
        f"- current limit: `{envelope['phase_current_limit_a_peak']}` A peak",
        "",
        "## Envelope Rows",
    ]
    for row in envelope["rows"]:
        lines.append(
            f"- `{row['speed_rpm']}` rpm -> `{row['torque_limit_nm']}` Nm, "
            f"`{row['mechanical_power_limit_w']}` W, `{row['region']}`"
        )
    lines.extend(["", "## Constraints"])
    lines.extend(f"- {item}" for item in envelope["constraints"])
    return "\n".join(lines).rstrip()


def format_motor_efficiency_map_plan(plan: Mapping[str, Any]) -> str:
    """Format an efficiency-map operating plan."""
    axes = plan["map_axes"]
    feasible = sum(1 for point in plan["operating_points"] if point["feasible_by_envelope"])
    total = len(plan["operating_points"])
    lines = [
        "# ELF Python Motor Efficiency Map Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        "- torque axis [Nm]: " + ", ".join(f"`{value}`" for value in axes["torque_nm"]),
        "- speed axis [rpm]: " + ", ".join(f"`{value}`" for value in axes["speed_rpm"]),
        f"- base speed: `{plan['base_speed_rpm']}` rpm",
        f"- DC bus: `{plan['dc_bus_v']}` V",
        f"- current limit: `{plan['phase_current_limit_a_peak']}` A peak",
        f"- feasible points by envelope: `{feasible}/{total}`",
        "- recommended studies: " + ", ".join(f"`{item}`" for item in plan["recommended_studies"]),
        "",
        "## Operating Points",
    ]
    for point in plan["operating_points"][:60]:
        label = "ok" if point["feasible_by_envelope"] else "clip"
        lines.append(
            f"- `{point['point_id']}` {point['speed_rpm']} rpm, "
            f"{point['torque_nm']} Nm, {point['mechanical_power_w']} W, "
            f"`{point['region']}`, `{label}`"
        )
    if len(plan["operating_points"]) > 60:
        lines.append(f"- ... {len(plan['operating_points']) - 60} more points omitted")
    lines.extend(["", "## Local Runner Sequence"])
    lines.extend(f"- {item}" for item in plan["local_runner_sequence"])
    lines.extend(["", "## Postprocess Outputs"])
    lines.extend(f"- `{item}`" for item in plan["postprocess_outputs"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_efficiency_map_result(result: Mapping[str, Any]) -> str:
    """Format a numeric efficiency map generated from RunResults."""
    axes = result["map_axes"]
    coverage = result["coverage"]
    best = result.get("best_efficiency_point") or {}
    lines = [
        "# ELF Python Motor Efficiency Map Result",
        "",
        f"- schema: `{result['schema_version']}`",
        f"- motor type: `{result['motor_type']}`",
        f"- status: `{result['status']}`",
        "- torque axis [Nm]: " + ", ".join(f"`{value}`" for value in axes["torque_nm"]),
        "- speed axis [rpm]: " + ", ".join(f"`{value}`" for value in axes["speed_rpm"]),
        f"- filled points: `{coverage['filled_points']}/{coverage['total_points']}`",
        f"- feasible filled points: `{coverage['feasible_filled_points']}/{coverage['feasible_total_points']}`",
        f"- boundary: {result['public_boundary']}",
        "",
        "## Best Efficiency Point",
    ]
    if best:
        lines.extend(
            [
                f"- point: `{best['point_id']}`",
                f"- case: `{best['case_id']}`",
                f"- speed: `{best['speed_rpm']}` rpm",
                f"- torque: `{best['torque_nm']}` Nm",
                f"- eta: `{best['efficiency']}`",
                f"- total loss: `{best['total_loss_w']}` W",
                f"- loss source: `{best['loss_source']}`",
                f"- voltage margin: `{best.get('voltage_margin_v')}` V",
                f"- current margin: `{best.get('current_margin_a')}` A",
            ]
        )
    else:
        lines.append("- none")
    lines.extend(["", "## Eta Grid"])
    header = "speed_rpm \\ torque_nm | " + " | ".join(str(value) for value in axes["torque_nm"])
    lines.append(header)
    lines.append(" | ".join(["---"] * (len(axes["torque_nm"]) + 1)))
    for speed, row in zip(axes["speed_rpm"], result["eta_grid"]):
        rendered = ["missing" if value is None else str(value) for value in row]
        lines.append(f"{speed} | " + " | ".join(rendered))
    lines.extend(["", "## Result Points"])
    if result["result_points"]:
        for point in result["result_points"][:60]:
            lines.append(
                f"- `{point['point_id']}` case `{point['case_id']}`: "
                f"eta `{point['efficiency']}`, loss `{point['total_loss_w']}`, "
                f"voltage margin `{point.get('voltage_margin_v')}`, "
                f"current margin `{point.get('current_margin_a')}`, "
                f"status `{point['map_status']}`"
            )
    else:
        lines.append("- none")
    if len(result["result_points"]) > 60:
        lines.append(f"- ... {len(result['result_points']) - 60} more points omitted")
    lines.extend(["", "## Quality Gate Results"])
    if result.get("quality_gate_results"):
        for gate in result["quality_gate_results"]:
            lines.append(
                f"- `{gate['gate']}`: `{gate['status']}` "
                f"(metric `{gate['metric']}`, threshold `{gate['threshold']}`) - {gate['reason']}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if result["warnings"]:
        lines.extend(f"- {item}" for item in result["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in result["quality_gates"])
    return "\n".join(lines).rstrip()


def format_induction_motor_slip_sweep_plan(plan: Mapping[str, Any]) -> str:
    """Format an induction-motor slip sweep plan."""
    lines = [
        "# ELF Python Induction Motor Slip Sweep Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- pole pairs: `{plan['pole_pairs']}`",
        f"- supply frequency: `{plan['supply_frequency_hz']}` Hz",
        f"- synchronous speed: `{plan['synchronous_speed_rpm']}` rpm",
        "- recommended studies: " + ", ".join(f"`{item}`" for item in plan["recommended_studies"]),
        "",
        "## Slip Points",
    ]
    for point in plan["operating_points"]:
        lines.append(
            f"- `{point['point_id']}` slip `{point['slip']}` -> "
            f"rotor `{point['rotor_speed_rpm']}` rpm, slip frequency "
            f"`{point['slip_frequency_hz']}` Hz"
        )
    lines.extend(["", "## Parser Keys"])
    lines.extend(f"- `{key}`" for key in plan["run_contract"]["parser_keys"])
    lines.extend(["", "## Derived Quantities"])
    for item in plan["operating_points"][0]["derived_quantities"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_dq_axis_map_plan(plan: Mapping[str, Any]) -> str:
    """Format an Id/Iq axis map plan."""
    params = plan["dq_parameters"]
    feasible = sum(1 for point in plan["operating_points"] if point["feasible_by_current_limit"])
    total = len(plan["operating_points"])
    lines = [
        "# ELF Python Motor DQ Axis Map Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- pole pairs: `{plan['pole_pairs']}`",
        f"- current limit: `{plan['current_limit_a_peak']}` A peak",
        f"- Ld: `{params['ld_h']}` H",
        f"- Lq: `{params['lq_h']}` H",
        f"- PM flux: `{params['pm_flux_wb']}` Wb",
        f"- torque formula: `{params['torque_formula']}`",
        "- decomposition: PM and reluctance torque terms are reported separately",
        f"- feasible points by current limit: `{feasible}/{total}`",
        "- recommended studies: " + ", ".join(f"`{item}`" for item in plan["recommended_studies"]),
        "",
        "## Axes",
        "- Id [A peak]: " + ", ".join(f"`{value}`" for value in plan["axes"]["id_a_peak"]),
        "- Iq [A peak]: " + ", ".join(f"`{value}`" for value in plan["axes"]["iq_a_peak"]),
        "",
        "## Points",
    ]
    for point in plan["operating_points"][:60]:
        label = "ok" if point["feasible_by_current_limit"] else "clip"
        lines.append(
            f"- `{point['point_id']}` Id `{point['id_a_peak']}`, Iq `{point['iq_a_peak']}`, "
            f"Trel `{point['reluctance_torque_nm_proxy']}`, Tpm `{point['pm_torque_nm_proxy']}`, "
            f"T `{point['total_torque_nm_proxy']}`, `{label}`"
        )
    if len(plan["operating_points"]) > 60:
        lines.append(f"- ... {len(plan['operating_points']) - 60} more points omitted")
    lines.extend(["", "## Parser Keys"])
    lines.extend(f"- `{key}`" for key in plan["parser_keys"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_mtpa_search_plan(plan: Mapping[str, Any]) -> str:
    """Format an MTPA current-angle search plan."""
    params = plan["dq_parameters"]
    best = plan["best_proxy_point"]
    lines = [
        "# ELF Python Motor MTPA Search Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- pole pairs: `{plan['pole_pairs']}`",
        f"- current limit: `{plan['current_limit_a_peak']}` A peak",
        f"- Ld/Lq/PM flux: `{params['ld_h']}` H / `{params['lq_h']}` H / `{params['pm_flux_wb']}` Wb",
        f"- torque formula: `{params['torque_formula']}`",
        f"- best proxy angle: `{best.get('current_angle_deg_from_q_axis', '')}` deg from q-axis",
        f"- best proxy torque-per-amp: `{best.get('torque_per_amp_proxy', '')}`",
        "",
        "## Angle Rows",
    ]
    for row in plan["rows"]:
        lines.append(
            f"- `{row['case']}` angle `{row['current_angle_deg_from_q_axis']}` deg, "
            f"Id `{row['id_a_peak']}`, Iq `{row['iq_a_peak']}`, "
            f"Trel `{row['reluctance_torque_nm_proxy']}`, Tpm `{row['pm_torque_nm_proxy']}`, "
            f"T/A `{row['torque_per_amp_proxy']}`"
        )
    lines.extend(["", "## Local Runner Sequence"])
    lines.extend(f"- {item}" for item in plan["local_runner_sequence"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_reluctance_motor_design_plan(plan: Mapping[str, Any]) -> str:
    """Format a SynRM/SRM reluctance-focused design plan."""
    lines = [
        "# ELF Python Reluctance Motor Design Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- pole pairs: `{plan['pole_pairs']}`",
        f"- stator slots: `{plan['stator_slots']}`",
        f"- rotor topology: `{plan['rotor_topology']}`",
        "- recommended studies: " + ", ".join(f"`{item}`" for item in plan["recommended_studies"]),
        "",
        "## Saliency Targets",
    ]
    for key, value in plan["saliency_targets"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Design Variables"])
    for var in plan["design_variables"]:
        low, high = var["range"]
        lines.append(
            f"- `{var['name']}` [{var['unit']}]: default `{var['default']}`, "
            f"range `{low}` to `{high}`, affects "
            + ", ".join(f"`{item}`" for item in var["affects"])
        )
    lines.extend(["", "## DQ / MTPA Summary"])
    lines.append(
        f"- dq points: `{len(plan['dq_axis_map_plan']['operating_points'])}`; "
        f"MTPA best angle: `{plan['mtpa_search_plan']['best_proxy_point'].get('current_angle_deg_from_q_axis', '')}` deg"
    )
    lines.extend(["", "## Observable Contracts"])
    lines.extend(f"- `{item}`" for item in plan["observable_contracts"])
    lines.extend(["", "## Aligned / Unaligned Inductance Checks"])
    lines.extend(f"- {item}" for item in plan["aligned_unaligned_inductance_checks"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_winding_layout_plan(plan: Mapping[str, Any]) -> str:
    """Format winding layout and winding factor plan."""
    wf = plan["winding_factors"]
    lines = [
        "# ELF Python Motor Winding Layout Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- slots / pole pairs / phases: `{plan['stator_slots']}` / `{plan['pole_pairs']}` / `{plan['phases']}`",
        f"- q slots/pole/phase: `{plan['slots_per_pole_per_phase']}`",
        f"- slot electrical angle: `{plan['slot_electrical_angle_deg']}` deg",
        f"- coil pitch: `{plan['coil_pitch_slots']}` slots",
        f"- winding factor proxy: `{wf['fundamental_winding_factor_proxy']}`",
        "",
        "## Slot Table",
    ]
    for row in plan["slot_table"][:72]:
        lines.append(
            f"- slot `{row['slot']}`: {row['electrical_angle_deg']} deg, "
            f"phase `{row['phase']}{row['sign']}`, layers `{row['layer_count']}`"
        )
    if len(plan["slot_table"]) > 72:
        lines.append(f"- ... {len(plan['slot_table']) - 72} more slots omitted")
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_topology_parameter_plan(plan: Mapping[str, Any]) -> str:
    """Format topology parameter plan."""
    lines = [
        "# ELF Python Motor Topology Parameter Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- pole pairs / slots: `{plan['pole_pairs']}` / `{plan['stator_slots']}`",
        f"- rotor topology: `{plan['rotor_topology']}`",
        f"- outer diameter: `{plan['outer_diameter_mm']}` mm",
        f"- stack length: `{plan['stack_length_mm']}` mm",
        "",
        "## Parameters",
    ]
    for var in plan["parameters"]:
        low, high = var["range"]
        lines.append(
            f"- `{var['name']}`: default `{var['default']}`, range `{low}` to `{high}`, affects "
            + ", ".join(f"`{item}`" for item in var["affects"])
        )
    lines.extend(["", "## Geometry Regions"])
    lines.extend(f"- `{item}`" for item in plan["geometry_regions"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_demag_margin_plan(plan: Mapping[str, Any]) -> str:
    """Format PM demagnetization margin plan."""
    lines = [
        "# ELF Python Motor Demag Margin Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- temperature: `{plan['temperature_c']}` C",
        f"- hot Br proxy: `{plan['br_hot_t_proxy']}` T",
        f"- Hcj: `{plan['hcj_ka_m']}` kA/m",
        f"- hot Hcj proxy: `{plan.get('hcj_hot_ka_m')}` kA/m",
        f"- hot Hknee proxy: `{plan.get('h_knee_hot_a_per_m')}` A/m",
        f"- negative Id: `{plan['id_min_a_peak']}` A peak",
        f"- margin proxy: `{plan['margin_proxy']}`",
        f"- risk label: `{plan['risk_label']}`",
        "",
        "## Required Observables",
    ]
    lines.extend(f"- `{item}`" for item in plan["required_observables"])
    lines.extend(["", "## Sweep Axes"])
    lines.extend(f"- `{item}`" for item in plan["sweep_axes"])
    if plan.get("loadline_sweep"):
        summary = plan["loadline_summary"]
        lines.extend(
            [
                "",
                "## Load-Line Sweep",
                f"- magnet length: `{summary['magnet_len_m']}` m",
                f"- iron path: `{summary['iron_path_m']}` m",
                f"- safe prefix count: `{summary.get('safe_prefix_count')}`",
                f"- first unsafe gap: `{summary['first_unsafe_gap_m']}` m",
                f"- largest safe gap: `{summary.get('largest_safe_gap_m')}` m",
                f"- minimum demag margin: `{summary['minimum_demag_margin_A_per_m']}` A/m",
                f"- load-line risk label: `{summary.get('risk_label')}`",
            ]
        )
        for row in plan["loadline_sweep"]:
            lines.append(
                f"- gap `{row['gap_m']}` m: Bgap `{row['B_gap_T']}` T, "
                f"Hm `{row['H_m_A_per_m']}` A/m, margin `{row['demag_margin_A_per_m']}` A/m, "
                f"safe `{row['safe_against_knee']}`"
            )
        lines.append("")
        lines.append("## Load-Line Quality Checks")
        lines.extend(f"- `{key}`: `{value}`" for key, value in summary["checks"].items())
    if plan.get("elf_step_contract"):
        contract = plan["elf_step_contract"]
        reference = contract.get("slot46_reference", {})
        recoil_reference = contract.get("slot102_reference", {})
        lines.extend(
            [
                "",
                "## ELF/MAGIC Step Contract",
                f"- lint tool: `{contract['lint_tool']}`",
                f"- HBRM role: {contract['required_hbrm_role']}",
                f"- HBCN role: {contract['required_hbcn_role']}",
                "- required HBCN steps: "
                + ", ".join(f"`{step}`" for step in contract["required_hbcn_steps"]),
                f"- metadata gate: `{contract.get('metadata_gate')}`",
                f"- radia-ngsolve gate: `{contract['radia_ngsolve_gate']}`",
                f"- load-line gate: `{contract.get('loadline_gate')}`",
                "- observable keys: "
                + ", ".join(f"`{key}`" for key in contract["recommended_observable_keys"]),
                f"- reference first unsafe gap: `{reference.get('first_unsafe_gap_m')}` m",
                f"- reference safe prefix count: `{reference.get('safe_prefix_count')}`",
                f"- reference minimum demag margin: `{reference.get('minimum_demag_margin_A_per_m')}` A/m",
                f"- recoil reference irreversible: `{recoil_reference.get('irreversible_demag')}`",
                f"- recoil reference ratio: `{recoil_reference.get('recoil_remanence_ratio_proxy')}`",
            ]
        )
    if plan.get("fault_current_screening"):
        fault = plan["fault_current_screening"]
        lines.extend(
            [
                "",
                "## Fault-Current Demag Screening",
                f"- schema: `{fault['schema_version']}`",
                f"- negative Id: `{fault['negative_id_a_peak']}` A peak",
                f"- negative Id is demag direction: `{fault['negative_id_is_demag_direction']}`",
                f"- demag field proxy: `{fault['demag_field_proxy_ka_m']}` kA/m",
                f"- screening rule: {fault['screening_rule']}",
                "- radia-ngsolve gates: "
                + ", ".join(f"`{gate}`" for gate in fault["recommended_radia_ngsolve_gates"]),
                "- observable keys: "
                + ", ".join(f"`{key}`" for key in fault["recommended_observable_keys"]),
                f"- ELF step contract: {fault['elf_step_contract']}",
            ]
        )
    if plan.get("bem_source_balance_contract"):
        balance = plan["bem_source_balance_contract"]
        lines.extend(
            [
                "",
                "## PM BEM Source Balance Contract",
                f"- schema: `{balance['schema_version']}`",
                f"- metadata gate: `{balance['metadata_gate']}`",
                f"- balance gate: `{balance['balance_gate']}`",
                f"- surface source density: `{balance['surface_source_density']}`",
                f"- normal convention: `{balance['normal_convention']}`",
                f"- signed charge proxy: `{balance['signed_charge_proxy']}`",
                f"- source balance unit: `{balance['source_balance_unit']}`",
                f"- signed charge balance relative tolerance: `{balance['signed_charge_balance_rel_tol']}`",
                "- required row keys: "
                + ", ".join(f"`{key}`" for key in balance["required_row_keys"]),
                "- required summary keys: "
                + ", ".join(f"`{key}`" for key in balance["required_summary_keys"]),
                "- negative controls: "
                + ", ".join(f"`{item}`" for item in balance["negative_controls"]),
            ]
        )
    if plan.get("run_result_loadline_handoff"):
        handoff = plan["run_result_loadline_handoff"]
        lines.extend(
            [
                "",
                "## RunResult Load-Line Handoff",
                f"- schema: `{handoff['schema_version']}`",
                "- parser tools: "
                + ", ".join(f"`{tool}`" for tool in handoff["parser_tools"]),
                f"- row identity: `{handoff['row_identity']}`",
                "- required normalized columns: "
                + ", ".join(f"`{key}`" for key in handoff["required_normalized_columns"]),
                f"- metadata gate: `{handoff['metadata_gate']}`",
                f"- load-line gate: `{handoff['loadline_gate']}`",
                f"- recoil-step gate: `{handoff['recoil_step_gate']}`",
                f"- notebook policy: {handoff['notebook_policy']}",
                "- negative controls: "
                + ", ".join(f"`{item}`" for item in handoff["negative_controls"]),
            ]
        )
    if plan.get("demag_package_handoff"):
        package = plan["demag_package_handoff"]
        lines.extend(
            [
                "",
                "## Demag Package Handoff",
                f"- schema: `{package['schema_version']}`",
                f"- package gate: `{package['package_gate']}`",
                "- row identity: "
                + ", ".join(f"`{key}`" for key in package["row_identity"]),
                "- required artifacts: "
                + ", ".join(f"`{key}`" for key in package["required_artifacts"]),
                "- required RunResult columns: "
                + ", ".join(f"`{key}`" for key in package["required_run_result_columns"]),
                "- source gates: "
                + ", ".join(
                    f"`{kind}` -> `{gate}`"
                    for kind, gate in package["source_gates"].items()
                ),
                "- negative controls: "
                + ", ".join(f"`{item}`" for item in package["negative_controls"]),
            ]
        )
    if plan.get("demag_margin_screening_package"):
        package = plan["demag_margin_screening_package"]
        lines.extend(
            [
                "",
                "## Demag Margin Screening Package",
                f"- schema: `{package['schema_version']}`",
                f"- package gate: `{package['package_gate']}`",
                "- row identity: "
                + ", ".join(f"`{key}`" for key in package["row_identity"]),
                "- step identity keys: "
                + ", ".join(f"`{key}`" for key in package["step_identity_keys"]),
                f"- step identity contract: {package['step_identity_contract']}",
                "- required artifacts: "
                + ", ".join(f"`{key}`" for key in package["required_artifacts"]),
                "- source gates: "
                + ", ".join(
                    f"`{kind}` -> `{gate}`"
                    for kind, gate in package["source_gates"].items()
                ),
                "- required fault observables: "
                + ", ".join(f"`{key}`" for key in package["required_fault_observables"]),
                "- field-probe identity keys: "
                + ", ".join(f"`{key}`" for key in package["field_probe_identity_keys"]),
                f"- field-probe identity contract: {package['field_probe_identity_contract']}",
                "- field-probe output identity keys: "
                + ", ".join(
                    f"`{key}`" for key in package["field_probe_output_identity_keys"]
                ),
                (
                    "- field-probe output identity contract: "
                    f"{package['field_probe_output_identity_contract']}"
                ),
                "- required BEM source-balance summary keys: "
                + ", ".join(
                    f"`{key}`" for key in package["required_bem_source_balance_summary_keys"]
                ),
                f"- notebook policy: {package['notebook_policy']}",
                "- negative controls: "
                + ", ".join(f"`{item}`" for item in package["negative_controls"]),
            ]
        )
    lines.extend(["", "## Load-Line Checks"])
    lines.extend(f"- {item}" for item in plan["loadline_checks"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_drive_cycle_plan(plan: Mapping[str, Any]) -> str:
    """Format drive-cycle operating point plan."""
    lines = [
        "# ELF Python Motor Drive Cycle Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- target market: `{plan['target_market']}`",
        f"- rated torque: `{plan['rated_torque_nm']}` Nm",
        f"- peak torque: `{plan['peak_torque_nm']}` Nm",
        f"- base speed: `{plan['base_speed_rpm']}` rpm",
        f"- max speed: `{plan['max_speed_rpm']}` rpm",
        "",
        "## Operating Points",
    ]
    for point in plan["operating_points"]:
        lines.append(
            f"- `{point['point_id']}`: {point['speed_rpm']} rpm, "
            f"{point['torque_nm']} Nm, weight `{point['weight']}`, "
            f"{point['mechanical_power_w']} W"
        )
    lines.extend(["", "## Weighted Outputs"])
    lines.extend(f"- `{item}`" for item in plan["weighted_outputs"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_optimization_study_plan(plan: Mapping[str, Any]) -> str:
    """Format constrained motor optimization study plan."""
    lines = [
        "# ELF Python Motor Optimization Study Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- objective: `{plan['objective']}`",
        f"- target market: `{plan['target_market']}`",
        f"- budget: `{plan['budget']}`",
        "",
        "## Design Variables",
    ]
    for var in plan["design_variables"]:
        low, high = var["range"]
        lines.append(f"- `{var['name']}`: default `{var['default']}`, range `{low}` to `{high}`")
    lines.extend(["", "## Constraints"])
    lines.extend(f"- {item}" for item in plan["constraints"])
    lines.extend(["", "## Ranking Outputs"])
    lines.extend(f"- `{item}`" for item in plan["ranking_outputs"])
    lines.extend(["", "## Workflow"])
    lines.extend(f"- {item}" for item in plan["workflow"])
    return "\n".join(lines).rstrip()


def format_motor_voltage_field_weakening_plan(plan: Mapping[str, Any]) -> str:
    """Format a voltage-limit and field-weakening plan."""
    lines = [
        "# ELF Python Motor Voltage / Field-Weakening Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- pole pairs: `{plan['pole_pairs']}`",
        f"- DC bus: `{plan['dc_bus_v']}` V",
        f"- current limit: `{plan['current_limit_a_peak']}` A peak",
        f"- phase voltage limit proxy: `{plan['v_phase_peak_limit']}` V peak",
        "",
        "## Speed Rows",
    ]
    for row in plan["rows"]:
        lines.append(
            f"- `{row['speed_rpm']}` rpm: Vproxy `{row['voltage_proxy_v_peak']}`, "
            f"margin `{row['voltage_margin_v_peak']}`, Idfw `{row['required_negative_id_a_peak_proxy']}`, "
            f"`{row['region']}`"
        )
    lines.extend(["", "## Required Observables"])
    lines.extend(f"- `{item}`" for item in plan["required_observables"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_cogging_ripple_plan(plan: Mapping[str, Any]) -> str:
    """Format a cogging/ripple reduction plan."""
    lines = [
        "# ELF Python Motor Cogging / Ripple Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- slots / poles: `{plan['stator_slots']}` / `{plan['poles']}`",
        f"- cogging order mechanical: `{plan['cogging_order_mechanical']}`",
        f"- cogging period slots: `{plan['cogging_period_slots']}`",
        "- harmonic orders: " + ", ".join(f"`{item}`" for item in plan["harmonic_orders"]),
        "",
        "## Mitigation Variables",
    ]
    for var in plan["mitigation_variables"]:
        low, high = var["range"]
        lines.append(
            f"- `{var['name']}`: default `{var['default']}`, range `{low}` to `{high}`, affects "
            + ", ".join(f"`{item}`" for item in var["affects"])
        )
    lines.extend(["", "## Parser Keys"])
    lines.extend(f"- `{item}`" for item in plan["parser_keys"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_airgap_harmonics_nvh_plan(plan: Mapping[str, Any]) -> str:
    """Format an air-gap harmonic and NVH plan."""
    lines = [
        "# ELF Python Motor Airgap Harmonics / NVH Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- slots / pole pairs: `{plan['stator_slots']}` / `{plan['pole_pairs']}`",
        "- mechanical force orders: " + ", ".join(f"`{item}`" for item in plan["mechanical_force_orders"]),
        "",
        "## Speed Rows",
    ]
    for row in plan["speed_rows"]:
        lines.append(
            f"- `{row['label']}` `{row['speed_rpm']}` rpm: electrical `{row['electrical_frequency_hz']}` Hz, "
            f"slot-pass `{row['slot_pass_frequency_hz']}` Hz"
        )
        for item in row["force_order_frequencies_hz"]:
            lines.append(f"  - order `{item['order']}` -> `{item['frequency_hz']}` Hz")
    lines.extend(["", "## Required Observables"])
    lines.extend(f"- `{item}`" for item in plan["required_observables"])
    lines.extend(["", "## NGSolve Follow-Up"])
    lines.extend(f"- {item}" for item in plan["ngsolve_follow_up"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_thermal_network_plan(plan: Mapping[str, Any]) -> str:
    """Format a reduced thermal network plan."""
    lines = [
        "# ELF Python Motor Thermal Network Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- target market: `{plan['target_market']}`",
        f"- total loss: `{plan['total_loss_w']}` W",
        f"- ambient: `{plan['ambient_c']}` C",
        f"- cooling h: `{plan['cooling_h_w_m2k']}` W/m^2/K",
        "",
        "## Nodes",
    ]
    for node in plan["nodes"]:
        lines.append(
            f"- `{node['node']}`: loss `{node['loss_w']}` W, "
            f"rise `{node['temperature_rise_c_proxy']}` C, temp `{node['temperature_c_proxy']}` C"
        )
    lines.extend(["", "## Required Inputs"])
    lines.extend(f"- `{item}`" for item in plan["required_inputs"])
    lines.extend(["", "## NGSolve Follow-Up"])
    lines.extend(f"- {item}" for item in plan["ngsolve_follow_up"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_manufacturing_tolerance_plan(plan: Mapping[str, Any]) -> str:
    """Format a manufacturing tolerance plan."""
    lines = [
        "# ELF Python Motor Manufacturing Tolerance Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- airgap: `{plan['airgap_mm']}` mm",
        f"- production intent: `{plan['production_intent']}`",
        "",
        "## Tolerance Variables",
    ]
    for var in plan["tolerance_variables"]:
        low, high = var["range"]
        lines.append(
            f"- `{var['name']}`: default `{var['default']}`, range `{low}` to `{high}`, affects "
            + ", ".join(f"`{item}`" for item in var["affects"])
        )
    lines.extend(["", "## DOE Rows"])
    for row in plan["doe_rows"][:16]:
        changes = ", ".join(f"`{key}`={value}" for key, value in row["changes"].items())
        lines.append(f"- `{row['case']}`: {changes}")
    if len(plan["doe_rows"]) > 16:
        lines.append(f"- ... {len(plan['doe_rows']) - 16} more rows omitted")
    lines.extend(["", "## Required Observables"])
    lines.extend(f"- `{item}`" for item in plan["required_observables"])
    lines.extend(["", "## Quality Gates"])
    lines.extend(f"- {item}" for item in plan["quality_gates"])
    return "\n".join(lines).rstrip()


def format_motor_material_variation_plan(plan: Mapping[str, Any]) -> str:
    """Format a material variation plan."""
    lines = [
        "# ELF Python Motor Material Variation Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- focus: `{plan['focus']}`",
        "",
        "## Variables",
    ]
    for var in plan["variables"]:
        low, high = var["range"]
        lines.append(
            f"- `{var['group']}.{var['name']}` [{var['unit']}]: default `{var['default']}`, "
            f"range `{low}` to `{high}`, affects "
            + ", ".join(f"`{item}`" for item in var["affects"])
        )
    lines.extend(["", "## Recommended Observables"])
    lines.extend(f"- `{item}`" for item in plan["recommended_observables"])
    lines.extend(["", "## Study Rules"])
    lines.extend(f"- {item}" for item in plan["study_rules"])
    return "\n".join(lines).rstrip()


def format_motor_feasibility_study(plan: Mapping[str, Any]) -> str:
    """Format a motor feasibility study plan."""
    lines = [
        "# ELF Python Motor Feasibility Study",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- goal: {plan['goal']}",
        f"- target market: `{plan['target_market']}`",
        f"- motor type: `{plan['motor_type']}`",
        f"- production intent: `{plan['production_intent']}`",
        f"- design objective: `{plan['design_objective']}`",
        "",
        "## Lanes",
    ]
    for lane in plan["lanes"]:
        lines.append(f"- `{lane['lane']}`: {lane['question']}")
        lines.append("  observables: " + ", ".join(f"`{item}`" for item in lane["observables"]))
    lines.extend(["", "## Extra Quality Gates"])
    lines.extend(f"- {item}" for item in plan["extra_quality_gates"])
    lines.extend(["", "## MCP Can Do"])
    lines.extend(f"- {item}" for item in plan["mcp_can_do"])
    lines.extend(["", "## MCP Cannot Claim Alone"])
    lines.extend(f"- {item}" for item in plan["mcp_cannot_claim_alone"])
    lines.append("")
    lines.append(f"Boundary: {plan['public_boundary']}")
    return "\n".join(lines).rstrip()


def format_motor_observable_contract(contract: Mapping[str, Any]) -> str:
    """Format a motor observable contract."""
    lines = [
        "# ELF Python Motor Observable Contract",
        "",
        f"- schema: `{contract['schema_version']}`",
        f"- motor type: `{contract['motor_type']}`",
        f"- study: `{contract['study']}`",
        "- observables: " + ", ".join(f"`{item}`" for item in contract["observables"]),
        f"- boundary: {contract['public_boundary']}",
        "",
        "## ELF Markers",
    ]
    for obs, markers in contract["elf_markers"].items():
        lines.append(f"- `{obs}`: " + (", ".join(f"`{m}`" for m in markers) or "no marker rule"))
    lines.extend(["", "## Parser Keys"])
    lines.append("- RunResult keys: " + ", ".join(f"`{item}`" for item in contract["run_result_keys"]))
    lines.append("- Observable keys: " + ", ".join(f"`{item}`" for item in contract["parser_observable_keys"]))
    lines.extend(["", "## Validation Checks"])
    lines.extend(f"- {check}" for check in contract["validation_checks"])
    force_contract = contract.get("force_result_contract")
    if force_contract:
        lines.extend(["", "## Force Result Package"])
        lines.append(
            "- allowed quantity dimensions: "
            + ", ".join(f"`{item}`" for item in force_contract["allowed_quantity_dimensions"])
        )
        lines.append(
            "- allowed force units: "
            + ", ".join(f"`{item}`" for item in force_contract["allowed_force_units"])
        )
        lines.append(
            "- required metadata: "
            + ", ".join(f"`{item}`" for item in force_contract["required_metadata"])
        )
        lines.append(
            "- public gate candidates: "
            + ", ".join(f"`{item}`" for item in force_contract["public_gate_candidates"])
        )
        lines.extend(f"- negative control: {item}" for item in force_contract["negative_controls"])
    lines.extend(["", "## AGE Targets"])
    lines.extend(f"- `{target}`" for target in contract["age_targets"])
    return "\n".join(lines).rstrip()


def format_motor_market_brief(brief: Mapping[str, Any]) -> str:
    """Format a motor market brief."""
    lines = [
        "# ELF Python Motor Market Brief",
        "",
        f"- schema: `{brief['schema_version']}`",
        f"- target market: `{brief['target_market']}` ({brief['display']})",
        f"- motor type: `{brief['motor_type']}`",
        f"- rotor topology: `{brief['rotor_topology']}`",
        f"- recommended objective: `{brief['recommended_objective']}`",
        "",
        "## Spec Intake Fields",
    ]
    lines.extend(f"- `{field}`" for field in brief["spec_intake_fields"])
    lines.extend(["", "## Design Priorities"])
    lines.extend(f"- `{item}`" for item in brief["design_priorities"])
    lines.extend(["", "## Preferred Topologies"])
    lines.extend(f"- `{item}`" for item in brief["preferred_topologies"])
    lines.extend(["", "## Recommended First Calls"])
    lines.extend(f"- `{call}`" for call in brief["recommended_first_calls"])
    lines.extend(["", "## User Experience Policy"])
    lines.extend(f"- {item}" for item in brief["user_experience_policy"])
    return "\n".join(lines).rstrip()


def format_motor_design_agent_handoff(handoff: Mapping[str, Any]) -> str:
    """Format a spec-to-design-agent handoff."""
    brief = handoff["brief"]
    lines = [
        "# ELF Python Motor Design Agent Handoff",
        "",
        f"- schema: `{handoff['schema_version']}`",
        f"- goal: {handoff['goal']}",
        f"- market: `{brief['target_market']}` ({brief['display']})",
        f"- motor type: `{brief['motor_type']}`",
        f"- rotor topology: `{brief['rotor_topology']}`",
        f"- objective: `{handoff['design_plan']['objective']}`",
        f"- boundary: {handoff['public_boundary']}",
        "",
        "## Spec Values",
    ]
    for key, value in handoff["spec_values"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Missing Spec Fields"])
    if handoff["missing_spec_fields"]:
        lines.extend(f"- `{field}`" for field in handoff["missing_spec_fields"])
    else:
        lines.append("- none")
    lines.extend(["", "## Deliverables"])
    for item in handoff["deliverables"]:
        scope = "public" if item["public"] else "local/private"
        lines.append(f"- `{item['name']}` ({scope}): {item['description']}")
    lines.extend(["", "## Analysis Routing"])
    for lane, steps in handoff["analysis_routing"].items():
        lines.append(f"### {lane}")
        if isinstance(steps, Mapping):
            for key, value in steps.items():
                lines.append(f"- `{key}`: {value}")
        else:
            lines.extend(f"- {step}" for step in steps)
    lines.extend(["", "## Manufacturing Handoff"])
    for key, items in handoff["manufacturing_handoff"].items():
        lines.append(f"### {key}")
        lines.extend(f"- {item}" for item in items)
    lines.extend(["", "## Next MCP Calls"])
    lines.append(
        f"- `elf_python_motor_design_plan(\"{handoff['goal']}\", motor_type=\"{brief['motor_type']}\", objective=\"{handoff['design_plan']['objective']}\")`"
    )
    lines.append(
        f"- `elf_python_meg_generation_plan(\"{handoff['goal']}\", dimension=\"{handoff['meg_generation_plan']['dimension']}\")`"
    )
    lines.append(
        f"- `elf_python_motor_sweep_matrix(motor_type=\"{brief['motor_type']}\", objective=\"{handoff['design_plan']['objective']}\", budget=9)`"
    )
    lines.append(
        f"- `elf_python_motor_observable_contract(motor_type=\"{brief['motor_type']}\", study=\"{handoff['observable_contract']['study']}\")`"
    )
    return "\n".join(lines).rstrip()


def format_meg_generation_plan(plan: Mapping[str, Any]) -> str:
    """Format a public .meg generation plan."""
    lines = [
        "# ELF Python MEG Generation Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- goal: {plan['goal']}",
        f"- dimension: `{plan['dimension']}`",
        f"- geometry complexity: `{plan['geometry_complexity']}`",
        f"- primary strategy: `{plan['primary_strategy']}`",
        "- alternatives: " + ", ".join(f"`{item}`" for item in plan["alternative_strategies"]),
        f"- boundary: {plan['public_boundary']}",
        "",
        "## Strategy Details",
    ]
    for name, item in plan["strategies"].items():
        lines.append(f"- `{name}`: {item['strength']}")
        lines.append("  contract: " + ", ".join(f"`{part}`" for part in item["minimum_contract"]))
    lines.extend(["", "## Validation Gates"])
    lines.extend(f"- `{gate}`" for gate in plan["validation_gates"])
    return "\n".join(lines).rstrip()


def format_2d_motor_template(template: Mapping[str, Any]) -> str:
    """Format the constrained 2D motor template."""
    lines = [
        "# ELF Python 2D Motor Template",
        "",
        f"- schema: `{template['schema_version']}`",
        f"- motor type: `{template['motor_type']}`",
        f"- pole pairs: `{template['pole_pairs']}`",
        f"- stator slots: `{template['stator_slots']}`",
        f"- generation path: `{template['meg_generation_path']}`",
        "- requested observables: "
        + ", ".join(f"`{item}`" for item in template["requested_observables"]),
        "",
        "## Radial Layers",
    ]
    for layer in template["radial_layers"]:
        lines.append(
            f"- `{layer['name']}`: `{layer['r_inner']}` to `{layer['r_outer']}` m, role `{layer['role']}`"
        )
    lines.extend(["", "## Angular Features"])
    for feature in template["angular_features"]:
        lines.append(
            f"- `{feature['name']}`: count `{feature['count']}`, role `{feature['material_role']}`, "
            f"layer `{feature['radial_layer']}`"
        )
    lines.extend(["", "## Hard Validation Rules"])
    lines.extend(f"- {rule}" for rule in template["hard_validation_rules"])
    lines.extend(["", "## JSON Template", "```json"])
    import json

    lines.append(json.dumps(template, indent=2))
    lines.append("```")
    return "\n".join(lines).rstrip()
