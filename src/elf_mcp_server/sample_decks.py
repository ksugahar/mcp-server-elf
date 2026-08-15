"""Public ELF-runnable ELF/MAGIC sample input decks.

This corpus contains lab-authored .mai/.meg decks only. It intentionally
excludes solver outputs, comparison metrics, private paths, and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
import hashlib
import json
import math
import re
from typing import Any

from .guards import bounded_int


ROOT = "public_samples"
MU0 = 4.0 * math.pi * 1e-7

VALIDATION_LEVEL_DESCRIPTIONS = {
    "static_input_contract": (
        "Public input-pair presence, syntax, and forbidden-marker checks passed."
    ),
    "ngsolve_proxy_energy": (
        "Public input-contract checks and an independent NGSolve proxy-field "
        "energy sanity check passed."
    ),
    "ngsolve_numeric_invariant": (
        "Analytic FLUM-contract invariants and independent NGSolve proxy "
        "invariants passed for numeric anchor cases."
    ),
}

VALIDATION_LEVEL_ORDER = (
    "ngsolve_numeric_invariant",
    "ngsolve_proxy_energy",
    "static_input_contract",
)

VALIDATION_LIMITATIONS = (
    "The public package bundles input decks and validation metadata only; "
    "solver outputs, regression logs, private paths, and provenance are not bundled.",
    "`ngsolve_proxy_energy` is a broad independent proxy-field gate for deck "
    "sanity, not a full absolute field/force/torque/loss agreement suite.",
    "`ngsolve_numeric_invariant` is used for numeric anchor families where "
    "analytic FLUM-contract flux, energy, force/torque-gradient, AC-loss, "
    "magnetic-circuit, and permanent-magnet invariants and NGSolve proxy "
    "invariants are both checked.",
)

QUALITY_LABELS = {
    "ngsolve_numeric_invariant": {
        "label": "gold_numeric_invariant",
        "display": "Gold numeric invariant",
        "meaning": (
            "Analytic FLUM-contract laws and independent NGSolve proxy "
            "invariants both passed for this family."
        ),
        "recommended_use": (
            "Use as the strongest public anchor when the prompt asks what "
            "physical quantity should be evaluated or how a law should scale."
        ),
    },
    "ngsolve_proxy_energy": {
        "label": "silver_proxy_energy",
        "display": "Silver proxy energy",
        "meaning": (
            "Public input-contract checks and an independent NGSolve "
            "proxy-field energy sanity gate was positive."
        ),
        "recommended_use": (
            "Use as a validated runnable authoring pattern. Do not claim "
            "absolute field, force, torque, or loss agreement from this label."
        ),
    },
    "static_input_contract": {
        "label": "bronze_input_contract",
        "display": "Bronze input contract",
        "meaning": "Input-pair presence, syntax, and forbidden-marker checks passed.",
        "recommended_use": "Use only as a syntax and workflow-contract pattern.",
    },
}

ENHANCED_OBSERVABLE_CONTRACT_LABEL = {
    "label": "silver_observable_contract",
    "display": "Silver observable contract",
    "meaning": (
        "Public input-contract and independent NGSolve proxy-energy checks "
        "passed, and the decks expose the expected FLUM/OHM2/FREQ/"
        "HBRM/HBCU observable contract for their physical quantity."
    ),
    "recommended_use": (
        "Use as a stronger public runnable pattern: the physical quantity, "
        "observable request, and representative deck are explicit, but this "
        "is still not a full absolute field/force/torque/loss agreement claim."
    ),
}

QUALITY_LABEL_DEFINITIONS = {
    "gold_numeric_invariant": QUALITY_LABELS["ngsolve_numeric_invariant"],
    ENHANCED_OBSERVABLE_CONTRACT_LABEL["label"]: ENHANCED_OBSERVABLE_CONTRACT_LABEL,
    "silver_proxy_energy": QUALITY_LABELS["ngsolve_proxy_energy"],
    "bronze_input_contract": QUALITY_LABELS["static_input_contract"],
}

QUALITY_LABEL_DISPLAY_ORDER = (
    "gold_numeric_invariant",
    "silver_observable_contract",
    "silver_proxy_energy",
    "bronze_input_contract",
)

ENHANCED_OBSERVABLE_CONTRACT_FAMILIES: dict[str, tuple[str, ...]] = {
    "application/motor/pm_square_2pole_pickup_100": ("FLUM", "HBRM", "HBCU"),
    "application/motor/pm_square_4pole_pickup_60": ("FLUM", "HBRM", "HBCU"),
    "application/motor/pm_square_6pole_pickup_72": ("FLUM", "HBRM", "HBCU"),
    "application/motor/pm_square_8pole_pickup_28": ("FLUM", "HBRM", "HBCU"),
    "application/motor/spm_surface_pm_10": ("FLUM", "HBRM", "HBCU"),
    "application/motor/spm_loop_10": ("FLUM", "HBRM", "HBCU"),
    "application/motor/srm_switched_reluctance_10": ("FLUM", "HBCU"),
    "application/motor/sr_motor_loop_10": ("FLUM", "HBCU"),
    "application/motor/induction_cage_10": ("FLUM", "OHM2", "HBCU"),
    "application/motor/emdlab_bldc_spm_10": ("FLUM", "HBRM", "HBCU"),
    "application/motor/emdlab_ipm_hairpin_10": ("FLUM", "HBRM", "HBCU"),
    "application/motor/emdlab_induction_bar_10": ("FLUM", "OHM2", "HBCU"),
    "application/motor/emdlab_synrm_flux_barrier_10": ("FLUM", "HBCU"),
    "application/motor/emdlab_srm_pole_variants_10": ("FLUM", "HBCU"),
    "application/motor/emdlab_afpm_linearized_10": ("FLUM", "HBRM", "HBCU"),
    "application/motor/emdlab_spmsm_static_torque_10": ("FLUM", "HBRM", "HBCU"),
    "application/motor/emdlab_srm1216_outer_rotor_10": ("FLUM", "HBCU"),
    "application/motor/emdlab_bldc_outer_rotor_10": ("FLUM", "HBRM", "HBCU"),
    "application/wpt_loop_10": ("FLUM", "MOMC", "FREQ"),
    "application/wpt_misalignment_10": ("FLUM", "OHM2", "MOMC", "FREQ"),
    "application/mri_loop_10": ("FLUM", "OHM2", "MOMC", "FREQ"),
    "application/ih_induction_heating_10": ("FLUM", "OHM2", "MAB8T", "MOMC", "FREQ"),
    "application/accelerator_magnet_10": ("FLUM", "HBCU"),
    "application/actuator_plunger_10": ("FLUM", "HBCU"),
    "application/electromagnetic_clutch_10": ("FLUM", "OHM2", "HBCU", "MOMC", "FREQ"),
    "application/eddy_current_brake_10": ("FLUM", "OHM2", "HBCU", "MOMC", "FREQ"),
    "application/ndt_eddy_probe_10": ("FLUM", "OHM2", "MOMC", "FREQ"),
    "application/transformer_leakage_10": ("FLUM", "HBCU"),
}

PUBLIC_OBSERVABLE_CONTRACT_CHECK = {
    "check": "public_observable_contract_passed",
    "display": "Public observable contract",
    "strength": "silver_quality_enhancement",
    "public_observable": "required FLUM/OHM2/FREQ/HBRM/HBCU/MAB8T deck markers",
    "meaning": (
        "The public `.mai` decks expose the expected observable requests and "
        "setup markers for the family-specific physical quantity."
    ),
}

PUBLIC_FORBIDDEN_TEXT_MARKERS = (
    "C:" + "\\temp",
    "C:" + "\\tmp",
    "S:" + "\\",
    "W:" + "\\",
    "_cross" + "val",
)

PUBLIC_FORBIDDEN_OUTPUT_SUFFIXES = (
    ".mao",
    ".mag",
    ".mat",
    ".mac",
)

PHYSICAL_QUANTITY_DEFINITIONS: dict[str, dict[str, str]] = {
    "flux_linkage": {
        "display": "Flux linkage / pickup flux",
        "observable": "FLUM requests in .mai decks",
        "validation_focus": "current, turns, sign, distance, symmetry, and superposition trends",
    },
    "inductance_coenergy": {
        "display": "Inductance and magnetic co-energy",
        "observable": "FLUM-derived L = Phi/I and W = 1/2 sum(I Phi)",
        "validation_focus": "current-square, turn-square, mutual, and add/cancel energy trends",
    },
    "force_torque_gradient": {
        "display": "Force / torque from co-energy gradient",
        "observable": "finite-difference dW/dx and dW/dtheta trends",
        "validation_focus": "distance force and angular torque trend checks",
    },
    "ac_loss": {
        "display": "AC eddy-current loss trend",
        "observable": "MOMC/FREQ/OHM2 conductive decks plus FLUM series",
        "validation_focus": "P proportional to I^2 f^2 / rho proxy trends",
    },
    "eddy_current_response": {
        "display": "Eddy-current / conducting-region response",
        "observable": "OHM2 and MAB8T conductive-region decks",
        "validation_focus": "conductive-region setup and positive proxy-energy gates",
    },
    "magnetic_circuit_flux": {
        "display": "Magnetic-circuit flux / reluctance trend",
        "observable": "MMB8T/HBCU iron-core and air-gap decks",
        "validation_focus": "B-H slope, air-gap, area, length, and current scaling trends",
    },
    "permanent_magnet_flux": {
        "display": "Permanent-magnet flux / magnetization polarity",
        "observable": "MWL8T/HBRM/HBCN permanent-magnet decks",
        "validation_focus": "remanence, polarity reversal, magnetization angle, and add/cancel trends",
    },
    "transformer_coupling": {
        "display": "Transformer coupling / turns ratio",
        "observable": "primary/secondary FLUM pickup in transformer decks",
        "validation_focus": "turns ratio, buck/boost, leakage, core area, and secondary-offset trends",
    },
    "motor_flux_linkage": {
        "display": "Motor phase flux-linkage pattern",
        "observable": "motor families with phase/pickup FLUM requests",
        "validation_focus": "topology-specific flux-linkage authoring and proxy-energy gates",
    },
    "wpt_mutual_coupling": {
        "display": "Wireless-power mutual coupling",
        "observable": "WPT coil decks with FLUM coupling probes",
        "validation_focus": "coil spacing, misalignment, and conductive-shield setup trends",
    },
    "mri_gradient_shielding": {
        "display": "MRI gradient and shield response",
        "observable": "MRI gradient-coil decks with FLUM/OHM2/FREQ probes",
        "validation_focus": "gradient-coil, shield, and eddy-current setup trends",
    },
    "actuator_force_proxy": {
        "display": "Actuator / solenoid force proxy",
        "observable": "plunger, relay, voice-coil, and clutch FLUM decks",
        "validation_focus": "gap, coil-current, and magnetic-circuit force-proxy trends",
    },
    "accelerator_field_quality": {
        "display": "Accelerator magnet field-quality proxy",
        "observable": "accelerator dipole/quadrupole/corrector FLUM decks",
        "validation_focus": "coil-current and pole/yoke setup trends",
    },
}

PHYSICAL_QUANTITY_ORDER = tuple(PHYSICAL_QUANTITY_DEFINITIONS)

GOLD_PHYSICS_ANCHORS = (
    "flux_linkage",
    "inductance_coenergy",
    "force_torque_gradient",
    "ac_loss",
    "magnetic_circuit_flux",
    "permanent_magnet_flux",
    "transformer_coupling",
)

CROSS_VALIDATION_METHODS: dict[str, dict[str, str]] = {
    "ngsolve_proxy_energy_positive": {
        "display": "NGSolve proxy-field energy",
        "strength": "silver_proxy_cross_check",
        "public_observable": "positive proxy magnetic energy from public deck geometry classes",
        "meaning": (
            "Independent NGSolve proxy-field energy sanity check passed for "
            "the public authoring pattern."
        ),
    },
    "ngsolve_numeric_invariants_passed": {
        "display": "NGSolve numeric invariant",
        "strength": "gold_independent_invariant",
        "public_observable": "dimensionless trend or sign invariant from an OSS reference model",
        "meaning": (
            "Independent NGSolve proxy invariants passed for the public "
            "numeric validation law."
        ),
    },
    "analytic_flux_invariants_passed": {
        "display": "Analytic FLUM-contract invariant",
        "strength": "gold_observable_invariant",
        "public_observable": "FLUM-derived flux, energy, force, loss, or coupling invariant",
        "meaning": (
            "Analytic FLUM-contract scaling, sign, energy, loss, force, or "
            "coupling invariants passed for the numeric family."
        ),
    },
}

VALIDATION_MATRIX_NOTES = (
    "The matrix connects user-visible prompt intents to public observables, "
    "quality labels, cross-validation methods, representative decks, and next "
    "MCP calls.",
    "It is public-safe by design: it exposes validation contracts and "
    "dimensionless evidence categories, not solver outputs, regression logs, "
    "private paths, or commercial benchmark numbers.",
    "Use gold rows when the prompt asks what physical quantity should be "
    "evaluated; use silver rows as runnable topology templates that still need "
    "problem-specific numeric acceptance criteria.",
)

FAMILY_META = {
    "application/mri_gradient_shield_12": {
        "title": "MRI gradient coil with eddy-current shield",
        "tags": (
            "application",
            "mri",
            "gradient-coil",
            "eddy-current",
            "shield",
            "momc",
            "mab8t",
            "ohm2",
            "fiel",
            "flum",
        ),
        "hint": "Use when a linear AC gradient-coil, conducting shield, or MOMC/FREQ pattern is needed.",
    },
    "application/mri_loop_10": {
        "title": "Loop10 MRI gradient and shield campaign",
        "tags": (
            "application",
            "mri",
            "gradient-coil",
            "eddy-current",
            "shield",
            "momc",
            "mab8t",
            "ohm2",
            "freq",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed MRI gradient-coil/shield input patterns with AC MOMC/FREQ setup and FLUM probes.",
    },
    "application/accelerator_magnet_10": {
        "title": "Loop10 accelerator electromagnet campaign",
        "tags": (
            "application",
            "accelerator",
            "electromagnet",
            "quadrupole",
            "dipole",
            "yoke",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop10",
        ),
        "hint": "Use for accelerator-style yoke electromagnets, coil polarity patterns, quadrupole/dipole variants, and FLUM pickup.",
    },
    "application/actuator_plunger_10": {
        "title": "Loop11 actuator plunger campaign",
        "tags": (
            "application",
            "actuator",
            "plunger",
            "solenoid",
            "u-yoke",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop11",
        ),
        "hint": "Use for solenoid/actuator input decks with a U-yoke, movable plunger, dual coils, air-gap pickup, and static FLUM.",
    },
    "application/eddy_current_brake_10": {
        "title": "Loop11 eddy-current brake campaign",
        "tags": (
            "application",
            "eddy-current",
            "brake",
            "conducting-plate",
            "momc",
            "freq",
            "ohm2",
            "mab8t",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop11",
        ),
        "hint": "Use for AC eddy-current brake decks with a conducting plate, steel yoke, differential coils, OHM2, FREQ, and FLUM pickup.",
    },
    "application/electromagnetic_clutch_10": {
        "title": "Loop12 electromagnetic clutch campaign",
        "tags": (
            "application",
            "electromagnetic-clutch",
            "clutch",
            "eddy-current",
            "momc",
            "freq",
            "ohm2",
            "mab8t",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop12",
        ),
        "hint": "Use for AC electromagnetic-clutch decks with steel plates, conducting armature plates, differential coils, OHM2, FREQ, and FLUM pickup.",
    },
    "application/hall_sensor_fixture_10": {
        "title": "Loop12 Hall-sensor fixture campaign",
        "tags": (
            "application",
            "hall-sensor",
            "sensor-fixture",
            "pm",
            "flux-concentrator",
            "mome",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop12",
        ),
        "hint": "Use for Hall-sensor fixture decks with opposed PM blocks, flux concentrator yokes, probe/pickup coils, and static FLUM.",
    },
    "application/ih_induction_heating_10": {
        "title": "Loop10 induction-heating coil campaign",
        "tags": (
            "application",
            "ih",
            "induction-heating",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "loop10",
        ),
        "hint": "Use for induction-heating coils, conducting workpieces, AC MOMC/FREQ setup, OHM2 conductors, and FLUM checks.",
    },
    "application/maglev_bearing_10": {
        "title": "Loop11 maglev bearing campaign",
        "tags": (
            "application",
            "maglev",
            "bearing",
            "differential-coils",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop11",
        ),
        "hint": "Use for magnetic-bearing or maglev-style pole pairs, mover-offset sweeps, differential coil signs, and static FLUM pickup.",
    },
    "application/magnetic_separator_10": {
        "title": "Loop11 magnetic separator campaign",
        "tags": (
            "application",
            "magnetic-separator",
            "separator",
            "pm",
            "belt",
            "mome",
            "mwl8t",
            "mmb8t",
            "mab8t",
            "ohm2",
            "flum",
            "loop11",
        ),
        "hint": "Use for magnetic-separator decks with PM pole pairs, steel back-yokes, conductive belt proxies, and FLUM pickup.",
    },
    "application/magnetic_gear_10": {
        "title": "Loop12 magnetic gear campaign",
        "tags": (
            "application",
            "magnetic-gear",
            "pm",
            "soft-yoke",
            "mome",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop12",
        ),
        "hint": "Use for magnetic-gear input decks with alternating PM teeth, soft yokes, relative tooth offsets, and FLUM pickup.",
    },
    "application/ndt_eddy_probe_10": {
        "title": "Loop11 NDT eddy-current probe campaign",
        "tags": (
            "application",
            "ndt",
            "eddy-current",
            "probe",
            "flaw",
            "conductivity-contrast",
            "momc",
            "freq",
            "ohm2",
            "mab8t",
            "mcl8t",
            "flum",
            "loop11",
        ),
        "hint": "Use for NDT eddy-current probe decks with conductive plates, flaw-property patches, OHM2 contrast, FREQ sweeps, and FLUM pickup.",
    },
    "application/relay_solenoid_10": {
        "title": "Loop12 relay solenoid campaign",
        "tags": (
            "application",
            "relay",
            "solenoid",
            "armature",
            "u-core",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop12",
        ),
        "hint": "Use for relay/solenoid decks with U-cores, armature air gaps, twin coil legs, and static FLUM pickup.",
    },
    "application/transformer_loop_10": {
        "title": "Loop10 transformer core and pickup campaign",
        "tags": (
            "application",
            "transformer",
            "core",
            "primary",
            "secondary",
            "pickup",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed transformer-style core/coil coupling, primary-secondary polarity, passive pickup FLUM, and B-H setup.",
    },
    "application/wpt_coupled_coils_10": {
        "title": "WPT coupled coils with AC flux pickup",
        "tags": (
            "application",
            "wpt",
            "wireless-power-transfer",
            "coupled-coils",
            "momc",
            "freq",
            "mcl8t",
            "mab8t",
            "ohm2",
            "flum",
            "shield",
        ),
        "hint": "Use for WPT primary/secondary coil pads, AC MOMC/FREQ setup, optional conducting shields, and FLUM coupling checks.",
    },
    "application/wpt_loop_10": {
        "title": "Loop10 WPT coupled-coil campaign",
        "tags": (
            "application",
            "wpt",
            "wireless-power-transfer",
            "coupled-coils",
            "momc",
            "freq",
            "mcl8t",
            "mab8t",
            "ohm2",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed WPT primary/secondary coil pads, AC MOMC/FREQ setup, conducting shields, and FLUM coupling checks.",
    },
    "application/voice_coil_10": {
        "title": "Loop12 voice-coil actuator campaign",
        "tags": (
            "application",
            "voice-coil",
            "actuator",
            "pm-bias",
            "moving-coil",
            "mome",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop12",
        ),
        "hint": "Use for voice-coil actuator decks with PM bias fields, moving differential coils, return iron, and static FLUM pickup.",
    },
    "application/transformer_core_pickup_12": {
        "title": "Transformer core and passive pickup coil",
        "tags": (
            "application",
            "transformer",
            "core",
            "primary",
            "secondary",
            "pickup",
            "mmb8t",
            "mcl8t",
            "flum",
        ),
        "hint": "Use for transformer-style core/coil coupling, passive pickup FLUM, and nonlinear B-H setup.",
    },
    "application/motor/emdlab_afpm_linearized_10": {
        "title": "EMDLAB-style AFPM linearized-airgap campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "afpm",
            "axial-flux",
            "pm",
            "linearized-airgap",
            "line-airgap",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for axial-flux PM motor authoring patterns represented as unfolded line-airgap decks with face magnets, stator coils, and FLUM pickup.",
    },
    "application/motor/emdlab_bldc_spm_10": {
        "title": "EMDLAB-style BLDC/SPM slotted-stator campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "bldc",
            "spm",
            "surface-pm",
            "pm",
            "slotted-stator",
            "three-phase",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for BLDC/SPM motor input patterns with surface PM rotor proxies, slotted stator iron, phase coils, and passive FLUM pickup.",
    },
    "application/motor/emdlab_induction_bar_10": {
        "title": "EMDLAB-style induction-machine rotor-bar campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "induction",
            "im",
            "rotor-bar",
            "squirrel-cage",
            "three-phase",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for induction-machine rotor-bar decks with stator phase coils, conductive bar proxies, OHM2 material data, and FLUM pickup.",
    },
    "application/motor/emdlab_ipm_hairpin_10": {
        "title": "EMDLAB-style IPM hairpin campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "ipm",
            "interior-pm",
            "hairpin",
            "54-slot",
            "buried-pm",
            "three-phase",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for IPM hairpin-style authoring with buried PM rotor proxies, stator phase coils, rotor-angle sweeps, and FLUM pickup.",
    },
    "application/motor/emdlab_srm_pole_variants_10": {
        "title": "EMDLAB-style SRM pole-variant campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "srm",
            "switched-reluctance",
            "reluctance",
            "pole-variant",
            "6-4",
            "8-6",
            "12-8",
            "12-16",
            "salient",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for SRM 6/4, 8/6, 12/8, and 12/16 pole-variant decks with salient iron, phase-pair excitation, and FLUM pickup.",
    },
    "application/motor/emdlab_synrm_flux_barrier_10": {
        "title": "EMDLAB-style SynRM flux-barrier campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "synrm",
            "synchronous-reluctance",
            "reluctance",
            "flux-barrier",
            "saliency",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for synchronous-reluctance flux-barrier rotor proxies, stator phase coils, rotor-angle sweeps, and FLUM pickup.",
    },
    "application/accelerator_corrector_10": {
        "title": "Loop13 accelerator corrector magnet campaign",
        "tags": (
            "application",
            "accelerator",
            "corrector",
            "electromagnet",
            "dipole",
            "trim-coil",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for accelerator corrector magnet decks with main dipole coils, trim-correction coils, aperture pickup, and static FLUM.",
    },
    "application/ih_susceptor_ring_10": {
        "title": "Loop13 IH susceptor ring campaign",
        "tags": (
            "application",
            "ih",
            "induction-heating",
            "susceptor",
            "ring",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for induction-heating susceptor decks with nested conducting workpieces, OHM2 contrast, AC coils, and FLUM pickup.",
    },
    "application/mri_gradient_sequence_10": {
        "title": "Loop13 MRI gradient sequence campaign",
        "tags": (
            "application",
            "mri",
            "gradient-sequence",
            "bipolar-gradient",
            "eddy-current",
            "shield",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for MRI gradient sequence decks with bipolar coils, split eddy-current shields, OHM2, FREQ, and FLUM pickup.",
    },
    "application/transformer_leakage_10": {
        "title": "Loop13 transformer leakage campaign",
        "tags": (
            "application",
            "transformer",
            "leakage",
            "gapped-core",
            "primary",
            "secondary",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for transformer leakage-flux decks with gapped cores, primary/secondary coils, leakage pickup coils, and FLUM.",
    },
    "application/wpt_misalignment_10": {
        "title": "Loop13 WPT misalignment campaign",
        "tags": (
            "application",
            "wpt",
            "wireless-power-transfer",
            "misalignment",
            "lateral-offset",
            "conducting-shield",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for WPT decks with primary/secondary pad offset, conducting shield plates, AC MOMC/FREQ setup, and FLUM pickup.",
    },
    "application/motor/axial_flux_pm_10": {
        "title": "Loop13 axial-flux PM motor campaign",
        "tags": (
            "motor",
            "afpm",
            "axial-flux",
            "pm",
            "face-magnet",
            "skew",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for axial-flux PM motor decks with dual axial yokes, face magnets, central stator coils, skew offsets, and FLUM.",
    },
    "application/motor/ipm_interior_pm_10": {
        "title": "Loop13 IPM interior permanent-magnet campaign",
        "tags": (
            "motor",
            "ipm",
            "interior-pm",
            "buried-pm",
            "pm",
            "rotor-angle",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for interior permanent-magnet motor decks with buried PM pairs, rotor/stator iron, phase coils, rotor-angle parameters, and FLUM.",
    },
    "application/motor/linear_pm_motor_10": {
        "title": "Loop13 linear PM motor campaign",
        "tags": (
            "motor",
            "linear-pm",
            "linear-motor",
            "pm",
            "translator",
            "forcer",
            "offset",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for linear PM motor decks with alternating PM tracks, moving three-coil forcers, translator offsets, and FLUM pickup.",
    },
    "application/motor/stepper_motor_10": {
        "title": "Loop13 stepper motor campaign",
        "tags": (
            "motor",
            "stepper",
            "stepper-motor",
            "pm",
            "four-phase",
            "detent",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for stepper motor decks with four stator phases, PM rotor proxies, detent offsets, and FLUM pickup.",
    },
    "application/motor/wound_field_sync_10": {
        "title": "Loop13 wound-field synchronous motor campaign",
        "tags": (
            "motor",
            "wound-field",
            "synchronous",
            "field-coil",
            "rotor-field",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for wound-field synchronous motor decks with DC rotor field coils, stator phase coils, soft iron, and FLUM pickup.",
    },
    "application/motor/induction_cage_10": {
        "title": "Induction motor cage and transient pickup",
        "tags": (
            "motor",
            "induction",
            "im",
            "squirrel-cage",
            "cage",
            "eddy-current",
            "three-phase",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "transient",
        ),
        "hint": "Use for induction-motor cage bars, three-phase stator COI1/AMP1 patterns, OHM2 conductors, and transient FLUM pickup.",
    },
    "application/motor/srm_switched_reluctance_10": {
        "title": "Switched-reluctance motor phase excitation",
        "tags": (
            "motor",
            "srm",
            "switched-reluctance",
            "reluctance",
            "salient",
            "stator",
            "rotor",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "pickup",
        ),
        "hint": "Use for SRM-style salient stator/rotor iron, phase-pair excitation, rotor-angle sweeps, and passive FLUM pickup.",
    },
    "application/motor/hysteresis_motor_10": {
        "title": "Loop10 hysteresis motor input-deck proxy",
        "tags": (
            "motor",
            "hysteresis",
            "hysteresis-motor",
            "high-coercivity",
            "rotor-ring",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop10",
            "proxy",
        ),
        "hint": "Use as an input-deck proxy and authoring pattern for high-coercivity rotor rings; ELF B-H curves start at the origin.",
    },
    "application/motor/pm_cosine_pickup_72": {
        "title": "2-pole cosine-amplitude PM pickup",
        "tags": ("motor", "pm", "cosine-remanence", "hbrm", "hbcn", "flum", "pickup"),
        "hint": "Use when spatially varying PM remanence or per-segment HBCN curve assignment matters.",
    },
    "application/motor/spm_surface_pm_10": {
        "title": "Surface PM motor with stator coils",
        "tags": (
            "motor",
            "spm",
            "surface-pm",
            "pm",
            "three-phase",
            "stator",
            "rotor",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "pickup",
        ),
        "hint": "Use for compact SPM motor authoring with surface MWL8T magnets, stator coils, rotor/stator iron, and passive FLUM pickup.",
    },
    "application/motor/reluctance_motor_10": {
        "title": "Loop10 synchronous reluctance motor campaign",
        "tags": (
            "motor",
            "reluctance",
            "synchronous-reluctance",
            "synrm",
            "salient",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop10",
        ),
        "hint": "Use for synchronous-reluctance saliency patterns, stator phase excitation, rotor-angle sweeps, and passive FLUM pickup.",
    },
    "application/motor/spm_loop_10": {
        "title": "Loop10 surface PM motor campaign",
        "tags": (
            "motor",
            "spm",
            "surface-pm",
            "pm",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed SPM motor decks with surface MWL8T magnets, stator coils, rotor/stator iron, and FLUM pickup.",
    },
    "application/motor/sr_motor_loop_10": {
        "title": "Loop10 SR-motor reluctance campaign",
        "tags": (
            "motor",
            "sr-motor",
            "srm",
            "switched-reluctance",
            "reluctance",
            "salient",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed SR-motor salient stator/rotor iron, phase excitation, rotor-angle sweeps, and passive FLUM pickup.",
    },
    "application/motor/pm_square_2pole_pickup_100": {
        "title": "2-pole square-wave PM pickup",
        "tags": ("motor", "pm", "2-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use as the broadest PM-only passive pickup baseline.",
    },
    "application/motor/pm_square_4pole_pickup_60": {
        "title": "4-pole square-wave PM pickup",
        "tags": ("motor", "pm", "4-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for multipole polarity, rotor-angle sign, and passive FLUM checks.",
    },
    "application/motor/pm_square_6pole_pickup_72": {
        "title": "6-pole square-wave PM pickup",
        "tags": ("motor", "pm", "6-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for shorter mechanical period PM pickup examples.",
    },
    "application/motor/pm_square_8pole_pickup_28": {
        "title": "8-pole square-wave PM pickup subset",
        "tags": ("motor", "pm", "8-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for compact high-pole-count PM pickup examples.",
    },
}

FAMILY_META.update(
    {
        "application/emdlab_1ph_transformer_static_10": {
            "title": "EMDLAB-style single-phase transformer static campaign",
            "tags": ("application", "emdlab-style", "transformer", "single-phase", "static", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for single-phase transformer static decks with core limbs, primary/secondary coils, passive pickup, and FLUM.",
        },
        "application/emdlab_benchmark_ccore_10": {
            "title": "EMDLAB-style benchmark C-core campaign",
            "tags": ("application", "emdlab-style", "benchmark", "c-core", "core", "mome", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for compact C-core benchmark-style decks with a driven coil and pickup FLUM.",
        },
        "application/emdlab_benchmark_geometry_10": {
            "title": "EMDLAB-style benchmark geometry campaign",
            "tags": ("application", "emdlab-style", "benchmark", "geometry", "mab8t", "mmb8t", "mcl8t", "ohm2", "flum", "ngsolve-crossval"),
            "hint": "Use for geometry benchmark coverage with steel, conductor, coil, and pickup entities.",
        },
        "application/emdlab_benchmark_magnet_10": {
            "title": "EMDLAB-style benchmark magnet campaign",
            "tags": ("application", "emdlab-style", "benchmark", "magnet", "pm", "mwl8t", "mmb8t", "hbrm", "hbcn", "flum", "ngsolve-crossval"),
            "hint": "Use for benchmark magnet decks with opposed PM blocks, yoke steel, and pickup FLUM.",
        },
        "application/numeric_validation_anchors_10": {
            "title": "Numeric validation anchor campaign",
            "tags": (
                "application",
                "numeric-validation",
                "anchor",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-scaling",
                "sign-reversal",
                "distance-decay",
                "symmetry",
                "cancellation",
                "mcl8t",
            ),
            "hint": "Use for compact validation anchor decks where ELF FLUM invariants and independent NGSolve proxy invariants are both expected to pass.",
        },
        "application/numeric_flum_law_64": {
            "title": "Numeric FLUM law validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "flum-law",
                "flux-linkage",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-linearity",
                "turn-linearity",
                "sign-reversal",
                "distance-decay",
                "mirror-symmetry",
                "superposition",
                "cancellation",
                "mcl8t",
            ),
            "hint": "Use for FLUM law validation decks covering current, turns, sign, distance, symmetry, superposition, and cancellation invariants.",
        },
        "application/numeric_inductance_energy_100": {
            "title": "Numeric inductance and co-energy validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "inductance",
                "co-energy",
                "energy",
                "flum-law",
                "flux-linkage",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-linearity",
                "turn-scaling",
                "mutual-inductance",
                "distance-decay",
                "mirror-symmetry",
                "superposition",
                "cancellation",
                "mcl8t",
            ),
            "hint": "Use for FLUM-derived inductance L = Phi/I and co-energy W = 1/2 sum(I Phi) validation decks covering current, turns, distance, symmetry, superposition, and add/cancel energy invariants.",
        },
        "application/numeric_ac_loss_100": {
            "title": "Numeric AC loss and eddy-current scaling validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "ac-loss",
                "eddy-current",
                "frequency",
                "freq",
                "momc",
                "ohm2",
                "mab8t",
                "resistivity",
                "conductivity",
                "loss-proxy",
                "i2f2-over-rho",
                "frequency-square",
                "current-square",
                "distance-decay",
                "mirror-symmetry",
                "lateral-symmetry",
                "add-cancel",
                "thickness-sweep",
                "width-sweep",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MOMC/FREQ/OHM2 AC-loss decks with FLUM checks and NGSolve proxy invariants covering P proportional to I^2 f^2 / rho, distance decay, symmetry, add/cancel, thickness, and width trends.",
        },
        "application/numeric_magnetic_circuit_100": {
            "title": "Numeric magnetic-circuit and B-H scaling validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "magnetic-circuit",
                "b-h",
                "bh-curve",
                "hbcu",
                "hbun",
                "mmb8t",
                "yoke",
                "air-gap",
                "reluctance",
                "core-area",
                "core-depth",
                "return-yoke",
                "pickup-coupling",
                "current-scaling",
                "turn-scaling",
                "add-cancel",
                "flum",
                "co-energy",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MMB8T/HBUN/HBCU magnetic-circuit decks with FLUM and NGSolve proxy checks covering B-H slope, air-gap reluctance, core area/depth, current/turn scaling, return-yoke continuity, and add/cancel bias behavior.",
        },
        "application/numeric_permanent_magnet_100": {
            "title": "Numeric permanent-magnet and magnetization validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "permanent-magnet",
                "pm",
                "magnetization",
                "hbrm",
                "hbcn",
                "vec3",
                "mwl8t",
                "pickup-coupling",
                "remanence",
                "distance-decay",
                "magnet-volume",
                "angle-cosine",
                "polarity-reversal",
                "lateral-symmetry",
                "add-cancel",
                "array-count",
                "pickup-turn-scaling",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MWL8T/HBRM/HBCN/VEC3 permanent-magnet decks with pickup FLUM and NGSolve proxy checks covering remanence, distance, magnet volume/depth, magnetization angle, polarity reversal, symmetry, add/cancel, array count, and pickup-turn scaling.",
        },
        "application/numeric_transformer_coupling_100": {
            "title": "Numeric transformer-coupling and turns-ratio validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "transformer",
                "transformer-coupling",
                "coupling",
                "mutual-inductance",
                "turns-ratio",
                "primary-secondary",
                "primary",
                "secondary",
                "leakage",
                "air-gap",
                "b-h",
                "hbcu",
                "hbun",
                "mmb8t",
                "core-area",
                "core-depth",
                "winding-span",
                "buck-boost",
                "flum",
                "co-energy",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MMB8T/HBUN/HBCU transformer-coupling decks with primary/secondary FLUM and NGSolve proxy checks covering current/turn scaling, turns ratio, B-H slope, air-gap leakage, span, core area/depth, secondary offset, and buck/boost superposition.",
        },
        "application/numeric_force_torque_100": {
            "title": "Numeric force and torque-gradient validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "force",
                "torque",
                "co-energy",
                "energy-gradient",
                "finite-difference",
                "dwdx",
                "dwdtheta",
                "flum-law",
                "flux-linkage",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-square-scaling",
                "distance-force",
                "mirror-symmetry",
                "lateral-symmetry",
                "angular-symmetry",
                "balanced-torque",
                "mcl8t",
            ),
            "hint": "Use for FLUM-derived co-energy force/torque-gradient checks: distance-force sign, current-square scaling, mirror/lateral symmetry, angular dW/dtheta trends, and balanced-torque invariants.",
        },
        "application/motor/emdlab_bldc_outer_rotor_10": {
            "title": "EMDLAB-style BLDC outer-rotor campaign",
            "tags": ("motor", "emdlab-style", "bldc", "outer-rotor", "spm", "surface-pm", "pm", "mwl8t", "mmb8t", "mcl8t", "hbrm", "hbcn", "flum", "ngsolve-crossval"),
            "hint": "Use for BLDC outer-rotor decks with surface PM proxies outside the stator and FLUM pickup.",
        },
        "application/motor/emdlab_induction_fraction_10": {
            "title": "EMDLAB-style induction-machine fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "induction", "im", "fractional-sector", "rotor-bar", "mab8t", "ohm2", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for induction-machine fractional-sector decks with rotor-bar conductors, OHM2, phase coils, and FLUM.",
        },
        "application/motor/emdlab_ipm_hairpin_fraction_10": {
            "title": "EMDLAB-style IPM hairpin fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "ipm", "hairpin", "fractional-sector", "interior-pm", "buried-pm", "mwl8t", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector IPM hairpin decks with buried PMs, phase coils, rotor-angle proxies, and FLUM.",
        },
        "application/motor/emdlab_spmsm_10": {
            "title": "EMDLAB-style SPMSM campaign",
            "tags": ("motor", "emdlab-style", "spmsm", "spm", "surface-pm", "pm", "mwl8t", "mmb8t", "mcl8t", "hbrm", "hbcn", "flum", "ngsolve-crossval"),
            "hint": "Use for SPMSM decks with surface PM rotor proxies, stator coils, and FLUM pickup.",
        },
        "application/motor/emdlab_spmsm_fraction_10": {
            "title": "EMDLAB-style SPMSM fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "spmsm", "spm", "fractional-sector", "surface-pm", "mwl8t", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector SPMSM decks with surface PM proxies and stator phase coils.",
        },
        "application/motor/emdlab_spmsm_static_torque_10": {
            "title": "EMDLAB-style SPMSM static-torque campaign",
            "tags": ("motor", "emdlab-style", "spmsm", "spm", "static-torque", "surface-pm", "rotor-angle", "mwl8t", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SPMSM static-torque proxy decks with rotor-angle sweeps and FLUM pickup.",
        },
        "application/motor/emdlab_srm64_10": {
            "title": "EMDLAB-style SRM 6/4 campaign",
            "tags": ("motor", "emdlab-style", "srm", "6-4", "switched-reluctance", "salient", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 6/4 pole-pattern decks with salient iron, phase-pair excitation, and FLUM.",
        },
        "application/motor/emdlab_srm86_10": {
            "title": "EMDLAB-style SRM 8/6 campaign",
            "tags": ("motor", "emdlab-style", "srm", "8-6", "switched-reluctance", "salient", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 8/6 pole-pattern decks with salient iron, phase-pair excitation, and FLUM.",
        },
        "application/motor/emdlab_srm86_fraction_10": {
            "title": "EMDLAB-style SRM 8/6 fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "srm", "8-6", "fractional-sector", "switched-reluctance", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector SRM 8/6 decks with salient iron and phase excitation.",
        },
        "application/motor/emdlab_srm86_static_torque_10": {
            "title": "EMDLAB-style SRM 8/6 static-torque campaign",
            "tags": ("motor", "emdlab-style", "srm", "8-6", "static-torque", "switched-reluctance", "rotor-angle", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 8/6 static-torque proxy decks with rotor-position sweeps and FLUM.",
        },
        "application/motor/emdlab_srm128_10": {
            "title": "EMDLAB-style SRM 12/8 campaign",
            "tags": ("motor", "emdlab-style", "srm", "12-8", "switched-reluctance", "salient", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 12/8 pole-pattern decks with salient iron and phase excitation.",
        },
        "application/motor/emdlab_srm1216_outer_rotor_10": {
            "title": "EMDLAB-style SRM 12/16 outer-rotor campaign",
            "tags": ("motor", "emdlab-style", "srm", "12-16", "outer-rotor", "switched-reluctance", "salient", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 12/16 outer-rotor pole-pattern decks with salient iron and FLUM.",
        },
        "application/motor/emdlab_synrm_static_torque_10": {
            "title": "EMDLAB-style SynRM static-torque campaign",
            "tags": ("motor", "emdlab-style", "synrm", "synchronous-reluctance", "static-torque", "flux-barrier", "saliency", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SynRM static-torque proxy decks with flux-barrier rotor proxies and FLUM.",
        },
        "application/motor/emdlab_synrm_fraction_static_torque_10": {
            "title": "EMDLAB-style SynRM fractional static-torque campaign",
            "tags": ("motor", "emdlab-style", "synrm", "synchronous-reluctance", "fractional-sector", "static-torque", "flux-barrier", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector SynRM static-torque proxy decks with saliency and FLUM.",
        },
    }
)

TEAM28_CASES: tuple[tuple[str, str], ...] = (
    ("application/motor/pm_square_2pole_pickup_100", "pm001"),
    ("application/motor/pm_square_2pole_pickup_100", "pm006"),
    ("application/motor/pm_square_2pole_pickup_100", "pm019"),
    ("application/motor/pm_square_2pole_pickup_100", "pm024"),
    ("application/motor/pm_square_2pole_pickup_100", "pm049"),
    ("application/motor/pm_square_2pole_pickup_100", "pm072"),
    ("application/motor/pm_square_2pole_pickup_100", "pm097"),
    ("application/motor/pm_square_2pole_pickup_100", "pm100"),
    ("application/motor/pm_square_4pole_pickup_60", "pm001"),
    ("application/motor/pm_square_4pole_pickup_60", "pm012"),
    ("application/motor/pm_square_4pole_pickup_60", "pm025"),
    ("application/motor/pm_square_4pole_pickup_60", "pm036"),
    ("application/motor/pm_square_4pole_pickup_60", "pm060"),
    ("application/motor/pm_square_6pole_pickup_72", "pm001"),
    ("application/motor/pm_square_6pole_pickup_72", "pm018"),
    ("application/motor/pm_square_6pole_pickup_72", "pm025"),
    ("application/motor/pm_square_6pole_pickup_72", "pm042"),
    ("application/motor/pm_square_6pole_pickup_72", "pm061"),
    ("application/motor/pm_square_6pole_pickup_72", "pm072"),
    ("application/motor/pm_square_8pole_pickup_28", "pm001"),
    ("application/motor/pm_square_8pole_pickup_28", "pm013"),
    ("application/motor/pm_square_8pole_pickup_28", "pm028"),
    ("application/motor/pm_cosine_pickup_72", "pm001"),
    ("application/motor/pm_cosine_pickup_72", "pm004"),
    ("application/motor/pm_cosine_pickup_72", "pm025"),
    ("application/motor/pm_cosine_pickup_72", "pm049"),
    ("application/motor/pm_cosine_pickup_72", "pm071"),
    ("application/motor/pm_cosine_pickup_72", "pm072"),
)

REPRESENTATIVE_CASES: tuple[dict[str, str], ...] = (
    {
        "area": "pm-foundation",
        "family": "application/motor/pm_square_2pole_pickup_100",
        "case": "pm001",
        "reason": "Small PM pickup seed for HBCN/HBRM polarity and FLUM inspection.",
    },
    {
        "area": "pm-foundation",
        "family": "application/motor/pm_cosine_pickup_72",
        "case": "pm001",
        "reason": "Cosine-remanence PM pickup pattern for smoother air-gap-field prompts.",
    },
    {
        "area": "motor",
        "family": "application/motor/emdlab_bldc_spm_10",
        "case": "ebl001",
        "reason": "First slotted-stator BLDC/SPM deck with phase coils and passive FLUM.",
    },
    {
        "area": "motor",
        "family": "application/motor/emdlab_ipm_hairpin_10",
        "case": "eip001",
        "reason": "Default IPM hairpin seed for buried PM and dq-flux authoring.",
    },
    {
        "area": "motor",
        "family": "application/motor/emdlab_induction_bar_10",
        "case": "eim001",
        "reason": "Induction-machine rotor-bar proxy with OHM2 and FLUM.",
    },
    {
        "area": "motor",
        "family": "application/motor/emdlab_synrm_flux_barrier_10",
        "case": "esr001",
        "reason": "SynRM flux-barrier seed for saliency and reluctance prompts.",
    },
    {
        "area": "motor",
        "family": "application/motor/emdlab_srm_pole_variants_10",
        "case": "esm001",
        "reason": "SRM pole-variant seed covering salient iron and phase-pair excitation.",
    },
    {
        "area": "motor",
        "family": "application/motor/axial_flux_pm_10",
        "case": "afm001",
        "reason": "Axial-flux PM authoring pattern with face magnets and axial yokes.",
    },
    {
        "area": "motor",
        "family": "application/motor/wound_field_sync_10",
        "case": "wfs001",
        "reason": "Wound-field synchronous motor seed with rotor field and stator coils.",
    },
    {
        "area": "motor",
        "family": "application/motor/stepper_motor_10",
        "case": "stm001",
        "reason": "Stepper motor seed for four-phase stator and detent-offset prompts.",
    },
    {
        "area": "motor",
        "family": "application/motor/reluctance_motor_10",
        "case": "ryl001",
        "reason": "Compact synchronous-reluctance seed with saliency and pickup coils.",
    },
    {
        "area": "motor",
        "family": "application/motor/hysteresis_motor_10",
        "case": "hyl001",
        "reason": "Hysteresis-motor proxy seed with high-coercivity material behavior.",
    },
    {
        "area": "application",
        "family": "application/transformer_core_pickup_12",
        "case": "tf001",
        "reason": "Transformer core/pickup deck for primary-secondary FLUM examples.",
    },
    {
        "area": "application",
        "family": "application/transformer_leakage_10",
        "case": "tlg001",
        "reason": "Gapped transformer leakage seed for coupling and stray-pickup prompts.",
    },
    {
        "area": "application",
        "family": "application/wpt_coupled_coils_10",
        "case": "wpt001",
        "reason": "Wireless-power coupled-coil AC seed with MOMC/FREQ and FLUM.",
    },
    {
        "area": "application",
        "family": "application/wpt_misalignment_10",
        "case": "wpm001",
        "reason": "WPT misalignment seed with conducting shield and lateral offset.",
    },
    {
        "area": "application",
        "family": "application/mri_gradient_shield_12",
        "case": "mri001",
        "reason": "MRI gradient-coil/shield seed with eddy-current AC setup.",
    },
    {
        "area": "application",
        "family": "application/ih_induction_heating_10",
        "case": "ihl001",
        "reason": "Induction-heating seed with conducting workpiece and MOMC setup.",
    },
    {
        "area": "application",
        "family": "application/accelerator_magnet_10",
        "case": "acl001",
        "reason": "Accelerator electromagnet seed with yoke, aperture pickup, and coils.",
    },
    {
        "area": "application",
        "family": "application/actuator_plunger_10",
        "case": "atl001",
        "reason": "Plunger actuator seed for solenoid/yoke force-oriented prompts.",
    },
    {
        "area": "application",
        "family": "application/eddy_current_brake_10",
        "case": "ebl001",
        "reason": "Eddy-current brake seed with conducting plate and AC excitation.",
    },
    {
        "area": "application",
        "family": "application/ndt_eddy_probe_10",
        "case": "ndl001",
        "reason": "NDT eddy-current probe seed with lift-off and conductive target patterns.",
    },
    {
        "area": "application",
        "family": "application/magnetic_gear_10",
        "case": "mgl001",
        "reason": "Magnetic gear seed with PM pole modulation and FLUM pickup.",
    },
    {
        "area": "application",
        "family": "application/voice_coil_10",
        "case": "vcl001",
        "reason": "Voice-coil actuator seed with compact moving-coil authoring pattern.",
    },
    {
        "area": "application",
        "family": "application/hall_sensor_fixture_10",
        "case": "hsl001",
        "reason": "Hall-sensor fixture seed with PMs, concentrators, and pickup coils.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_validation_anchors_10",
        "case": "nva001",
        "reason": "Small numeric invariant anchor for current scaling and sign sanity.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_flum_law_64",
        "case": "nfl001",
        "reason": "FLUM-law seed for current, turns, symmetry, and superposition checks.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_inductance_energy_100",
        "case": "nie001",
        "reason": "Inductance/co-energy seed for L = Phi/I and W = 1/2 sum(I Phi).",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_force_torque_100",
        "case": "nft001",
        "reason": "Co-energy force/torque-gradient seed for dW/dx and dW/dtheta trends.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_ac_loss_100",
        "case": "nal001",
        "reason": "AC-loss invariant seed for I^2 f^2 / rho scaling prompts.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_magnetic_circuit_100",
        "case": "nmc001",
        "reason": "Magnetic-circuit invariant seed for B-H slope and air-gap reluctance.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_permanent_magnet_100",
        "case": "npm001",
        "reason": "Permanent-magnet invariant seed for HBRM/HBCN/VEC3 polarity work.",
    },
    {
        "area": "numeric-gold",
        "family": "application/numeric_transformer_coupling_100",
        "case": "ntc001",
        "reason": "Transformer-coupling invariant seed for turns ratio and leakage trends.",
    },
)

SAMPLE_ROUTE_RULES: tuple[dict[str, Any], ...] = (
    {
        "intent": "Compact surface-PM motor",
        "family": "application/motor/spm_surface_pm_10",
        "query": "SPM surface-PM HBRM FLUM motor flux linkage",
        "recipe": "pm_airgap_field",
        "terms": (
            "spm motor",
            "spm",
            "motor flux linkage",
            "surface pm",
            "surface-pm",
            "surface permanent magnet",
            "surface-mounted",
            "surface mounted",
            "hbrm",
        ),
        "why": "Use these compact SPM decks first when the prompt asks for surface-PM motor flux linkage without requiring a BLDC slot campaign.",
    },
    {
        "intent": "Loop-reviewed SPM motor",
        "family": "application/motor/spm_loop_10",
        "query": "Loop10 SPM HBRM FLUM surface-PM motor",
        "recipe": "pm_airgap_field",
        "terms": ("loop10 spm", "loop 10 spm", "spm loop", "loop-reviewed spm"),
        "why": "Use these loop-reviewed SPM decks when the prompt explicitly asks for the Loop10 SPM family or reviewed surface-PM examples.",
    },
    {
        "intent": "BLDC or surface-PM motor",
        "family": "application/motor/emdlab_bldc_spm_10",
        "query": "EMDLAB-style BLDC SPM surface-pm FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("bldc", "brushless", "spm", "surface pm", "surface-pm", "slotted", "stator"),
        "why": "Start here for slotted-stator surface-PM machines with phase coils and passive FLUM pickup.",
    },
    {
        "intent": "IPM hairpin motor",
        "family": "application/motor/emdlab_ipm_hairpin_10",
        "query": "EMDLAB-style IPM hairpin buried-pm FLUM",
        "recipe": "ipm_ldlq_flux",
        "terms": ("ipm", "interior pm", "interior-pm", "hairpin", "buried pm", "buried-pm", "54-slot"),
        "why": "Use these decks when the prompt mentions IPM, buried magnets, hairpin conductors, or dq flux work.",
    },
    {
        "intent": "Interior-PM angle sweep",
        "family": "application/motor/ipm_interior_pm_10",
        "query": "Loop13 IPM interior permanent-magnet rotor angle FLUM",
        "recipe": "ipm_ldlq_flux",
        "terms": ("interior", "rotor angle", "angle sweep", "dq", "ld", "lq"),
        "why": "Use these simpler IPM decks when rotor-angle variation or current-on flux is the main task.",
    },
    {
        "intent": "Induction machine rotor bars",
        "family": "application/motor/emdlab_induction_bar_10",
        "query": "induction-machine bar OHM2 FLUM",
        "recipe": "eddy_current_time_domain",
        "terms": ("induction", "im", "rotor bar", "rotor-bar", "squirrel cage", "squirrel-cage", "ohm2"),
        "why": "Use these decks for induction-machine stator phase coils with conductive rotor-bar proxies.",
    },
    {
        "intent": "Synchronous reluctance or flux-barrier motor",
        "family": "application/motor/emdlab_synrm_flux_barrier_10",
        "query": "EMDLAB-style SynRM flux-barrier saliency FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("synrm", "synchronous reluctance", "flux barrier", "flux-barrier", "saliency"),
        "why": "Use these decks for SynRM-style flux-barrier rotor proxies and saliency-driven studies.",
    },
    {
        "intent": "Switched-reluctance motor pole variant",
        "family": "application/motor/emdlab_srm_pole_variants_10",
        "query": "EMDLAB-style SRM pole-variant switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm", "switched reluctance", "switched-reluctance", "pole variant", "6/4", "8/6", "12/8", "12/16"),
        "why": "Use these decks for SRM 6/4, 8/6, 12/8, or 12/16 pole proxy prompts.",
    },
    {
        "intent": "Axial-flux PM motor",
        "family": "application/motor/axial_flux_pm_10",
        "query": "Loop13 axial-flux PM face magnet FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("afpm", "axial flux", "axial-flux", "face magnet", "face-magnet", "skew"),
        "why": "Use these decks for axial-flux PM motors with face magnets, axial yokes, and skew offsets.",
    },
    {
        "intent": "Linear PM motor",
        "family": "application/motor/linear_pm_motor_10",
        "query": "Loop13 linear PM motor translator offset FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("linear pm", "linear-pm", "linear motor", "translator", "forcer"),
        "why": "Use these decks for linear PM tracks, moving forcer coils, and translator offset sweeps.",
    },
    {
        "intent": "Stepper motor",
        "family": "application/motor/stepper_motor_10",
        "query": "Loop13 stepper motor detent FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("stepper", "stepper motor", "detent", "four phase", "four-phase"),
        "why": "Use these decks for four-phase stepper motors, PM rotor proxies, and detent-offset prompts.",
    },
    {
        "intent": "Wound-field synchronous motor",
        "family": "application/motor/wound_field_sync_10",
        "query": "Loop13 wound-field synchronous rotor field FLUM",
        "recipe": "mutual_flux_current_pickup",
        "terms": ("wound field", "wound-field", "field coil", "field-coil", "synchronous motor", "rotor field"),
        "why": "Use these decks for DC rotor field coils, stator phase coils, and synchronous-machine prompts without PMs.",
    },
    {
        "intent": "PM pickup or back-EMF seed",
        "family": "application/motor/pm_cosine_pickup_72",
        "query": "HBCN FLUM cosine-remanence PM pickup",
        "recipe": "passive_flum_pickup",
        "terms": ("back emf", "back-emf", "flux linkage", "flux-linkage", "pickup", "flum", "pm pickup"),
        "why": "Use this broad PM pickup baseline before adding coils, iron, saliency, or current excitation.",
    },
    {
        "intent": "WPT misalignment",
        "family": "application/wpt_misalignment_10",
        "query": "Loop13 WPT misalignment OHM2 FLUM",
        "recipe": "sinusoidal_momc",
        "terms": ("wpt", "wireless power", "wireless-power", "misalignment", "lateral offset", "lateral-offset"),
        "why": "Use these decks for primary/secondary pad offsets, conducting shields, MOMC/FREQ, and FLUM.",
    },
    {
        "intent": "MRI gradient sequence",
        "family": "application/mri_gradient_sequence_10",
        "query": "Loop13 MRI gradient sequence OHM2 FREQ FLUM",
        "recipe": "sinusoidal_momc",
        "terms": ("mri", "gradient", "gradient sequence", "bipolar", "shield"),
        "why": "Use these decks for bipolar gradient coils, eddy-current shields, OHM2, FREQ, and FLUM.",
    },
    {
        "intent": "Transformer leakage",
        "family": "application/transformer_leakage_10",
        "query": "Loop13 transformer leakage gapped-core FLUM",
        "recipe": "mutual_flux_current_pickup",
        "terms": ("transformer", "leakage", "gapped core", "gapped-core", "primary", "secondary"),
        "why": "Use these decks for gapped transformer cores, primary/secondary coils, and leakage pickup.",
    },
    {
        "intent": "Induction-heating susceptor",
        "family": "application/ih_susceptor_ring_10",
        "query": "Loop13 IH susceptor OHM2 MOMC FLUM",
        "recipe": "sinusoidal_momc",
        "terms": ("ih", "induction heating", "induction-heating", "susceptor", "ring"),
        "why": "Use these decks for AC induction-heating coils with nested conducting workpieces and OHM2 contrast.",
    },
    {
        "intent": "Accelerator corrector magnet",
        "family": "application/accelerator_corrector_10",
        "query": "Loop13 accelerator corrector trim coil FLUM",
        "recipe": "linear_iron_boost",
        "terms": ("accelerator", "corrector", "trim coil", "trim-coil", "dipole", "aperture"),
        "why": "Use these decks for main dipole coils, trim-correction coils, aperture pickup, and yoke checks.",
    },
    {
        "intent": "General motor authoring starter",
        "family": "application/motor/emdlab_bldc_spm_10",
        "query": "EMDLAB-style motor FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("motor", "machine", "rotor", "stator"),
        "why": "Use this as the first public motor deck when the prompt is broad and does not name a machine type.",
    },
)

SAMPLE_ROUTE_RULES = (
    {
        "intent": "Numeric transformer-coupling and turns-ratio validation",
        "family": "application/numeric_transformer_coupling_100",
        "query": "numeric transformer coupling primary secondary turns ratio FLUM HBCU MMB8T",
        "recipe": "mutual_flux_current_pickup",
        "terms": (
            "transformer coupling",
            "coupling coefficient",
            "turns ratio",
            "turn ratio",
            "primary secondary",
            "primary/secondary",
            "secondary turn",
            "primary turn",
            "transformer flum law",
            "buck boost",
            "buck/boost",
            "air-gap leakage",
            "core coupling",
        ),
        "why": "Use these decks when the prompt asks how to validate transformer primary/secondary FLUM, turns ratio, leakage coupling, core B-H/area/depth effects, or buck/boost superposition before detailed transformer studies.",
    },
    {
        "intent": "Numeric permanent-magnet and magnetization validation",
        "family": "application/numeric_permanent_magnet_100",
        "query": "numeric permanent magnet HBRM HBCN VEC3 magnetization angle polarity FLUM",
        "recipe": "pm_airgap_field",
        "terms": (
            "permanent magnet",
            "permanent-magnet",
            "pm scaling",
            "hbrm",
            "hbcn",
            "vec3",
            "mwl8t",
            "magnetization angle",
            "magnet angle",
            "remanence",
            "polarity reversal",
            "magnet polarity",
            "magnet volume",
            "pickup turn",
            "magnet array",
            "add cancel",
            "add/cancel",
        ),
        "why": "Use these decks when the prompt asks how to validate MWL8T/HBRM/HBCN/VEC3 permanent-magnet behavior, magnetization direction, polarity, PM volume, array count, or pickup-turn coupling before detailed motor PM studies.",
    },
    {
        "intent": "Numeric magnetic-circuit and B-H scaling validation",
        "family": "application/numeric_magnetic_circuit_100",
        "query": "numeric magnetic circuit B-H HBCU MMB8T air gap reluctance yoke FLUM",
        "recipe": "magnetic_circuit_yoke_gap",
        "terms": (
            "magnetic circuit",
            "magnetic-circuit",
            "b-h",
            "bh curve",
            "hbcu",
            "hbun",
            "mmb8t",
            "air gap",
            "air-gap",
            "reluctance",
            "yoke",
            "return yoke",
            "return-yoke",
            "core area",
            "core depth",
            "pickup coupling",
            "magnetic path",
            "flux path",
        ),
        "why": "Use these decks when the prompt asks how to validate MMB8T/HBUN/HBCU magnetic-circuit behavior, air-gap reluctance, yoke continuity, or pickup coupling before detailed nonlinear material studies.",
    },
    {
        "intent": "Numeric AC loss and eddy-current scaling validation",
        "family": "application/numeric_ac_loss_100",
        "query": "numeric AC loss eddy current MOMC FREQ OHM2 frequency square resistivity",
        "recipe": "eddy_current_frequency_sweep",
        "terms": (
            "ac loss",
            "eddy loss",
            "eddy-current loss",
            "eddy current loss",
            "frequency square",
            "frequency-square",
            "current square",
            "current-square",
            "resistivity inverse",
            "i2f2",
            "i^2 f^2",
            "ohm2",
            "momc",
            "freq",
            "skin",
            "conducting plate",
            "loss proxy",
            "add cancel",
            "add/cancel",
        ),
        "why": "Use these decks when the prompt asks how to validate MOMC/FREQ/OHM2 AC-loss or eddy-current scaling behavior before moving to detailed loss post-processing.",
    },
    {
        "intent": "Numeric force and torque-gradient validation",
        "family": "application/numeric_force_torque_100",
        "query": "numeric force torque co-energy gradient FLUM dWdx dWdtheta",
        "recipe": "maxwell_torque_surface",
        "terms": (
            "force",
            "torque",
            "force law",
            "torque law",
            "co-energy gradient",
            "coenergy gradient",
            "energy gradient",
            "dwdx",
            "dw/dx",
            "dwdtheta",
            "dw/dtheta",
            "finite difference force",
            "finite-difference force",
            "angular torque",
            "balanced torque",
            "distance force",
        ),
        "why": "Use these decks when the prompt asks how to validate force or torque behavior from FLUM-derived co-energy gradients before moving to direct FORT/FIXB post-processing.",
    },
    {
        "intent": "Numeric inductance and co-energy validation",
        "family": "application/numeric_inductance_energy_100",
        "query": "numeric inductance co-energy FLUM current turns superposition energy",
        "recipe": "mutual_flux_current_pickup",
        "terms": (
            "inductance",
            "co-energy",
            "coenergy",
            "energy law",
            "phi over current",
            "phi/i",
            "l = phi/i",
            "w = 1/2",
            "half i phi",
            "mutual inductance",
            "self inductance",
            "turn scaling",
            "energy current square",
            "energy turns square",
            "add cancel energy",
            "what physical quantity",
            "what quantity",
        ),
        "why": "Use these decks when the prompt asks what physical quantity should be evaluated after FLUM, especially inductance L = Phi/I or co-energy W = 1/2 sum(I Phi).",
    },
    {
        "intent": "Numeric FLUM law validation",
        "family": "application/numeric_flum_law_64",
        "query": "numeric FLUM law current turns symmetry superposition cancellation",
        "recipe": "passive_flum_pickup",
        "terms": (
            "flum law",
            "flux linkage law",
            "numeric flum",
            "current linearity",
            "turn linearity",
            "superposition",
            "cancellation",
            "mirror symmetry",
            "pickup ratio",
            "distance decay",
        ),
        "why": "Use these decks when the prompt asks which physical quantity is validated or needs FLUM law checks across current, turns, distance, symmetry, and superposition.",
    },
    {
        "intent": "Numeric validation anchor",
        "family": "application/numeric_validation_anchors_10",
        "query": "numeric-validation anchor FLUM NGSolve invariant",
        "recipe": "passive_flum_pickup",
        "terms": (
            "numeric validation",
            "validation anchor",
            "ngsolve invariant",
            "flux invariant",
            "flum invariant",
            "current scaling",
            "sign reversal",
            "distance decay",
            "symmetry check",
            "cancellation check",
        ),
        "why": "Use these decks when the prompt asks whether validation is stronger than a simple run/pass or proxy-energy gate.",
    },
    {
        "intent": "BLDC outer-rotor motor",
        "family": "application/motor/emdlab_bldc_outer_rotor_10",
        "query": "EMDLAB-style BLDC outer-rotor surface-pm FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("outer rotor", "outer-rotor", "bldc outer", "outside rotor"),
        "why": "Use these decks when the prompt specifically asks for a BLDC/SPM outer-rotor topology.",
    },
    {
        "intent": "Fractional-sector induction machine",
        "family": "application/motor/emdlab_induction_fraction_10",
        "query": "EMDLAB-style induction fractional-sector OHM2 FLUM",
        "recipe": "eddy_current_time_domain",
        "terms": ("induction fraction", "fractional induction", "fractional-sector induction", "im fraction"),
        "why": "Use these decks for reduced-sector induction-machine rotor-bar prompts.",
    },
    {
        "intent": "Fractional-sector IPM hairpin motor",
        "family": "application/motor/emdlab_ipm_hairpin_fraction_10",
        "query": "EMDLAB-style IPM hairpin fractional-sector FLUM",
        "recipe": "ipm_ldlq_flux",
        "terms": ("ipm fraction", "hairpin fraction", "fractional-sector ipm", "fractional ipm"),
        "why": "Use these decks for reduced-sector IPM hairpin prompts with buried PMs and phase coils.",
    },
    {
        "intent": "SPMSM motor",
        "family": "application/motor/emdlab_spmsm_10",
        "query": "EMDLAB-style SPMSM surface-pm FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("spmsm", "surface pm synchronous", "surface-pm synchronous"),
        "why": "Use these decks for SPMSM prompts that name the synchronous-machine form explicitly.",
    },
    {
        "intent": "SPMSM static torque",
        "family": "application/motor/emdlab_spmsm_static_torque_10",
        "query": "EMDLAB-style SPMSM static-torque rotor-angle FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("spmsm torque", "spmsm static torque", "surface pm torque", "static torque spm"),
        "why": "Use these decks for SPMSM rotor-angle/static-torque proxy prompts.",
    },
    {
        "intent": "SPMSM fractional-sector",
        "family": "application/motor/emdlab_spmsm_fraction_10",
        "query": "EMDLAB-style SPMSM fractional-sector FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("spmsm fraction", "fractional spmsm", "fractional-sector spmsm"),
        "why": "Use these decks for reduced-sector SPMSM prompt variants.",
    },
    {
        "intent": "Specific SRM pole count",
        "family": "application/motor/emdlab_srm86_10",
        "query": "EMDLAB-style SRM 8-6 switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 8/6", "srm86", "8/6 srm", "8-6 srm"),
        "why": "Use these decks when the prompt names the common SRM 8/6 example.",
    },
    {
        "intent": "SRM 6/4 pole count",
        "family": "application/motor/emdlab_srm64_10",
        "query": "EMDLAB-style SRM 6-4 switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 6/4", "srm64", "6/4 srm", "6-4 srm"),
        "why": "Use these decks for SRM 6/4 pole-pattern prompts.",
    },
    {
        "intent": "SRM 12/8 pole count",
        "family": "application/motor/emdlab_srm128_10",
        "query": "EMDLAB-style SRM 12-8 switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 12/8", "srm128", "12/8 srm", "12-8 srm"),
        "why": "Use these decks for SRM 12/8 pole-pattern prompts.",
    },
    {
        "intent": "SRM 12/16 outer-rotor",
        "family": "application/motor/emdlab_srm1216_outer_rotor_10",
        "query": "EMDLAB-style SRM 12-16 outer-rotor FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 12/16", "srm1216", "12/16 srm", "12-16 srm", "srm outer rotor"),
        "why": "Use these decks for SRM 12/16 outer-rotor prompts.",
    },
    {
        "intent": "SynRM static torque",
        "family": "application/motor/emdlab_synrm_static_torque_10",
        "query": "EMDLAB-style SynRM static-torque flux-barrier FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("synrm torque", "synrm static torque", "reluctance torque"),
        "why": "Use these decks for SynRM static-torque proxy prompts.",
    },
    {
        "intent": "Single-phase transformer static example",
        "family": "application/emdlab_1ph_transformer_static_10",
        "query": "EMDLAB-style single-phase transformer static FLUM",
        "recipe": "mutual_flux_current_pickup",
        "terms": ("1ph transformer", "single phase transformer", "single-phase transformer", "transformer static"),
        "why": "Use these decks for single-phase transformer static core/coil prompts.",
    },
    {
        "intent": "EMDLAB benchmark C-core",
        "family": "application/emdlab_benchmark_ccore_10",
        "query": "EMDLAB-style benchmark C-core FLUM",
        "recipe": "linear_iron_boost",
        "terms": ("benchmark ccore", "benchmark c-core", "c-core", "ccore"),
        "why": "Use these decks for compact C-core benchmark-style prompts.",
    },
    {
        "intent": "EMDLAB benchmark magnet",
        "family": "application/emdlab_benchmark_magnet_10",
        "query": "EMDLAB-style benchmark magnet HBCN FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("benchmark magnet", "magnet benchmark"),
        "why": "Use these decks for benchmark-style PM/yoke prompts.",
    },
    {
        "intent": "EMDLAB benchmark geometry",
        "family": "application/emdlab_benchmark_geometry_10",
        "query": "EMDLAB-style benchmark geometry OHM2 FLUM",
        "recipe": "linear_iron_boost",
        "terms": ("benchmark geometry", "geometry benchmark"),
        "why": "Use these decks for geometry benchmark prompts with mixed steel, conductor, and coil primitives.",
    },
    *SAMPLE_ROUTE_RULES,
)

SOL_RE = re.compile(r"^\s*SOL\s+([A-Z0-9_]+)", re.MULTILINE)
ELEMENT_RE = re.compile(
    r"\b(MWL8T|MWV8T|MCL8T|MMB8T|MAB8T|MAT[0-9A-Z]*|MBB[0-9A-Z]*|"
    r"MCO[0-9A-Z]*|MCM[0-9A-Z]*|MJH[0-9A-Z]*)\b"
)
KEYWORDS = (
    "HBUN",
    "HBSC",
    "HBCU",
    "HBRM",
    "HBCN",
    "VEC3",
    "COI1",
    "AMP1",
    "AMP1I",
    "OHM2",
    "CMU1",
    "CMU1I",
    "TIME",
    "FREQ",
    "NONL",
    "DMEG",
    "FLUM",
)


@dataclass(frozen=True)
class SampleDeck:
    path: str
    family: str
    case: str
    ext: str
    char_count: int
    text: str


def _sample_root():
    return resources.files("elf_mcp_server").joinpath(ROOT)


@lru_cache(maxsize=1)
def load_validated_manifest() -> dict[str, Any]:
    """Load the public validation manifest for sample deck families."""
    path = _sample_root().joinpath("VALIDATED_MANIFEST.json")
    return json.loads(path.read_text(encoding="ascii"))


@lru_cache(maxsize=1)
def load_publication_batches() -> dict[str, Any]:
    """Load the public 100-case publication checkpoint manifest."""
    path = _sample_root().joinpath("PUBLICATION_BATCHES.json")
    return json.loads(path.read_text(encoding="ascii"))


def _validation_counts(families: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for entry in families.values():
        level = entry.get("validation_level") or "unknown"
        bucket = counts.setdefault(
            level,
            {
                "families": 0,
                "cases": 0,
                "input_files": 0,
                "description": VALIDATION_LEVEL_DESCRIPTIONS.get(level, ""),
            },
        )
        bucket["families"] += 1
        bucket["cases"] += int(entry.get("cases", 0))
        bucket["input_files"] += int(entry.get("input_files", 0))
    return counts


def validation_level_counts() -> dict[str, dict[str, Any]]:
    """Return validation-level counts for all public sample families."""
    families = load_validated_manifest().get("families", {})
    return _validation_counts(families)


def build_publication_batch_summary() -> dict[str, Any]:
    """Return public-safe 100-case checkpoint metadata."""
    batches = load_publication_batches()
    return {
        "checkpoint_size": int(batches.get("checkpoint_size", 0)),
        "total_cases": int(batches.get("total_cases", 0)),
        "total_batches": int(batches.get("total_batches", 0)),
        "full_100_case_batches": int(batches.get("full_100_case_batches", 0)),
        "remainder_cases": int(batches.get("remainder_cases", 0)),
        "next_checkpoint_cases": int(batches.get("next_checkpoint_cases", 0)),
        "additional_cases_needed_for_next_100_case_checkpoint": int(
            batches.get("additional_cases_needed_for_next_100_case_checkpoint", 0)
        ),
        "batches": [
            {
                "batch_id": batch.get("batch_id", ""),
                "batch_kind": batch.get("batch_kind", ""),
                "status": batch.get("status", ""),
                "case_count": int(batch.get("case_count", 0)),
                "case_start": int(batch.get("case_start", 0)),
                "case_end": int(batch.get("case_end", 0)),
                "validation_level_counts": dict(batch.get("validation_level_counts", {})),
            }
            for batch in batches.get("batches", [])
        ],
    }


def _public_gate(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "gate": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
    }


def _normalise_duplicate_text(text: str) -> str:
    """Normalize deck text for stable duplicate checks without changing semantics."""
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalised.split("\n")).strip()


def _duplicate_hash(text: str) -> str:
    return hashlib.sha256(_normalise_duplicate_text(text).encode("utf-8")).hexdigest()


def _sample_duplicate_facts(decks: dict[str, SampleDeck]) -> dict[str, Any]:
    """Classify exact case duplicates and single-file reuse in public decks."""
    pair_hashes: dict[str, list[dict[str, str]]] = {}
    mai_hashes: dict[str, list[dict[str, str]]] = {}
    meg_hashes: dict[str, list[dict[str, str]]] = {}
    missing_meg: list[str] = []
    missing_mai: list[str] = []

    for deck in decks.values():
        entry = {
            "path": deck.path,
            "family": deck.family,
            "case": deck.case,
            "ext": deck.ext,
        }
        if deck.ext == "mai":
            mai_hashes.setdefault(_duplicate_hash(deck.text), []).append(entry)
            meg_path = deck.path.rsplit(".", 1)[0] + ".meg"
            meg = decks.get(meg_path)
            if meg is None:
                missing_meg.append(deck.path)
                continue
            pair_key = hashlib.sha256(
                (
                    _normalise_duplicate_text(deck.text)
                    + "\n---MEG---\n"
                    + _normalise_duplicate_text(meg.text)
                ).encode("utf-8")
            ).hexdigest()
            pair_hashes.setdefault(pair_key, []).append(
                {
                    "family": deck.family,
                    "case": deck.case,
                    "mai_path": deck.path,
                    "meg_path": meg_path,
                }
            )
        elif deck.ext == "meg":
            meg_hashes.setdefault(_duplicate_hash(deck.text), []).append(entry)
            mai_path = deck.path.rsplit(".", 1)[0] + ".mai"
            if mai_path not in decks:
                missing_mai.append(deck.path)

    pair_duplicate_groups = {
        key: rows for key, rows in pair_hashes.items() if len(rows) > 1
    }
    mai_reuse_groups = {
        key: rows for key, rows in mai_hashes.items() if len(rows) > 1
    }
    meg_reuse_groups = {
        key: rows for key, rows in meg_hashes.items() if len(rows) > 1
    }
    cross_family_meg_reuse_groups = {
        key: rows
        for key, rows in meg_reuse_groups.items()
        if len({row["family"] for row in rows}) > 1
    }

    return {
        "case_pairs": len(pair_hashes),
        "missing_meg": sorted(missing_meg),
        "missing_mai": sorted(missing_mai),
        "pair_duplicate_groups": pair_duplicate_groups,
        "mai_reuse_groups": mai_reuse_groups,
        "meg_reuse_groups": meg_reuse_groups,
        "cross_family_meg_reuse_groups": cross_family_meg_reuse_groups,
        "pair_duplicate_cases": sum(len(rows) for rows in pair_duplicate_groups.values()),
        "pair_delete_candidates": sum(len(rows) - 1 for rows in pair_duplicate_groups.values()),
        "mai_reuse_files": sum(len(rows) for rows in mai_reuse_groups.values()),
        "meg_reuse_files": sum(len(rows) for rows in meg_reuse_groups.values()),
        "cross_family_meg_reuse_files": sum(
            len(rows) for rows in cross_family_meg_reuse_groups.values()
        ),
    }


def _duplicate_group_rows(
    groups: dict[str, list[dict[str, str]]],
    max_groups: int,
    *,
    pair: bool = False,
) -> list[dict[str, Any]]:
    rows = []
    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    for key, entries in ordered[:max(0, max_groups)]:
        families = sorted({entry["family"] for entry in entries})
        row: dict[str, Any] = {
            "hash": key[:12],
            "count": len(entries),
            "family_count": len(families),
            "families": families[:10],
        }
        if pair:
            row["cases"] = [
                {
                    "family": entry["family"],
                    "case": entry["case"],
                    "mai_path": entry["mai_path"],
                    "meg_path": entry["meg_path"],
                }
                for entry in entries[:10]
            ]
        else:
            row["paths"] = [entry["path"] for entry in entries[:10]]
        rows.append(row)
    return rows


def build_duplicate_audit(family: str | None = None, max_groups: int = 12) -> dict[str, Any]:
    """Build an MCP-oriented duplicate audit for public sample decks."""
    all_decks = load_sample_decks()
    family_filter = family.lower() if family else ""
    decks = {
        path: deck
        for path, deck in all_decks.items()
        if not family_filter or family_filter in deck.family.lower()
    }
    facts = _sample_duplicate_facts(decks)
    total_cases = sum(1 for deck in decks.values() if deck.ext == "mai")
    total_meg = sum(1 for deck in decks.values() if deck.ext == "meg")
    group_limit = max(0, min(max_groups, 50))
    pair_duplicate_groups = facts["pair_duplicate_groups"]
    mai_reuse_groups = facts["mai_reuse_groups"]
    meg_reuse_groups = facts["meg_reuse_groups"]
    cross_family_meg_reuse_groups = facts["cross_family_meg_reuse_groups"]
    gates = [
        _public_gate(
            "paired_mai_meg_for_duplicate_audit",
            not facts["missing_meg"] and not facts["missing_mai"] and total_cases == total_meg,
            (
                f"{total_cases} .mai files, {total_meg} .meg files, "
                f"{len(facts['missing_meg'])} missing .meg, "
                f"{len(facts['missing_mai'])} missing .mai"
            ),
        ),
        _public_gate(
            "exact_sample_pairs_unique",
            not pair_duplicate_groups,
            (
                f"{len(pair_duplicate_groups)} duplicate .mai+.meg groups, "
                f"{facts['pair_delete_candidates']} safe-delete candidates"
            ),
        ),
        _public_gate(
            "single_file_reuse_classified",
            True,
            (
                f"{len(mai_reuse_groups)} .mai reuse groups and "
                f"{len(meg_reuse_groups)} .meg reuse groups are reported as "
                "MCP collapse/display candidates, not automatic deletion candidates"
            ),
        ),
    ]
    return {
        "total_cases": total_cases,
        "total_input_files": len(decks),
        "family_filter": family or "",
        "delete_recommendation": (
            "delete_exact_pair_duplicates"
            if pair_duplicate_groups
            else "no_public_deck_deletion_recommended"
        ),
        "mcp_display_recommendation": (
            "Keep single-file reuse as design-space coverage, but collapse or "
            "summarize those groups in MCP views when the user wants a concise tour."
        ),
        "audit_gate_status": (
            "PASS" if all(gate["status"] == "PASS" for gate in gates) else "FAIL"
        ),
        "gates": gates,
        "exact_pair_duplicate_groups": len(pair_duplicate_groups),
        "exact_pair_duplicate_cases": facts["pair_duplicate_cases"],
        "exact_pair_delete_candidates": facts["pair_delete_candidates"],
        "mai_reuse_groups": len(mai_reuse_groups),
        "mai_reuse_files": facts["mai_reuse_files"],
        "meg_reuse_groups": len(meg_reuse_groups),
        "meg_reuse_files": facts["meg_reuse_files"],
        "cross_family_meg_reuse_groups": len(cross_family_meg_reuse_groups),
        "cross_family_meg_reuse_files": facts["cross_family_meg_reuse_files"],
        "exact_pair_duplicates": _duplicate_group_rows(
            pair_duplicate_groups, group_limit, pair=True
        ),
        "mai_reuse_examples": _duplicate_group_rows(mai_reuse_groups, group_limit),
        "meg_reuse_examples": _duplicate_group_rows(meg_reuse_groups, group_limit),
        "cross_family_meg_reuse_examples": _duplicate_group_rows(
            cross_family_meg_reuse_groups, group_limit
        ),
        "public_use_notes": [
            "Exact `.mai` + `.meg` pair duplicates are the only automatic deletion candidates.",
            "Identical `.mai` with different `.meg` means the same analysis-control pattern is reused over different geometry.",
            "Identical `.meg` with different `.mai` means the same geometry is reused for different currents, frequency, material, output, or validation intent.",
            "For MCP clients, representative routing and playbooks should prefer one representative from each reuse group before showing the whole sweep.",
        ],
    }


def build_public_quality_gates() -> list[dict[str, str]]:
    """Return publication-readiness gates for the bundled public sample corpus."""
    manifest = load_validated_manifest()
    batches = load_publication_batches()
    decks = load_sample_decks()
    all_public_files = _walk_public_files(_sample_root())
    mai_paths = {path for path, deck in decks.items() if deck.ext == "mai"}
    meg_paths = {path for path, deck in decks.items() if deck.ext == "meg"}
    mai_stems = {path.rsplit(".", 1)[0] for path in mai_paths}
    meg_stems = {path.rsplit(".", 1)[0] for path in meg_paths}
    paired_stems = mai_stems & meg_stems
    missing_meg = sorted(mai_stems - meg_stems)
    missing_mai = sorted(meg_stems - mai_stems)

    gates = [
        _public_gate(
            "paired_mai_meg",
            not missing_meg and not missing_mai and len(mai_paths) == len(meg_paths),
            (
                f"{len(paired_stems)} paired cases, {len(mai_paths)} .mai files, "
                f"{len(meg_paths)} .meg files"
            ),
        )
    ]
    duplicate_facts = _sample_duplicate_facts(decks)
    gates.append(
        _public_gate(
            "exact_sample_pairs_unique",
            not duplicate_facts["pair_duplicate_groups"],
            (
                f"{len(duplicate_facts['pair_duplicate_groups'])} duplicate .mai+.meg groups, "
                f"{duplicate_facts['pair_delete_candidates']} safe-delete candidates"
            ),
        )
    )

    manifest_families = manifest.get("families", {})
    deck_case_counts: dict[str, int] = {}
    deck_input_counts: dict[str, int] = {}
    for deck in decks.values():
        deck_input_counts[deck.family] = deck_input_counts.get(deck.family, 0) + 1
        if deck.ext == "mai":
            deck_case_counts[deck.family] = deck_case_counts.get(deck.family, 0) + 1

    manifest_family_names = set(manifest_families)
    deck_family_names = set(deck_case_counts)
    family_count_mismatches = []
    for family, entry in manifest_families.items():
        if deck_case_counts.get(family, 0) != int(entry.get("cases", 0)):
            family_count_mismatches.append(family)
        if deck_input_counts.get(family, 0) != int(entry.get("input_files", 0)):
            family_count_mismatches.append(family)
    family_ok = (
        manifest_family_names == deck_family_names
        and not family_count_mismatches
        and int(manifest.get("total_cases", 0)) == len(mai_paths)
        and int(manifest.get("total_input_files", 0)) == len(decks)
    )
    gates.append(
        _public_gate(
            "manifest_matches_files",
            family_ok,
            (
                f"{len(manifest_family_names)} manifest families, "
                f"{len(deck_family_names)} deck families, {len(decks)} input files"
            ),
        )
    )
    digest = hashlib.sha256()
    input_nodes = [
        (path, node)
        for path, node in all_public_files
        if path.lower().endswith((".mai", ".meg"))
    ]
    for path, node in sorted(input_nodes, key=lambda item: item[0]):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(node.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        digest.update(b"\0")
    current_digest = "sha256:" + digest.hexdigest()
    gates.append(
        _public_gate(
            "manifest_content_digest_matches",
            manifest.get("content_digest_algorithm")
            == "sha256-path-and-lf-normalized-bytes-v1"
            and manifest.get("content_sha256") == current_digest,
            f"{len(input_nodes)} input files bound by {current_digest}",
        )
    )

    batched_case_paths: list[str] = []
    for batch in batches.get("batches", []):
        batched_case_paths.extend(str(path) for path in batch.get("case_paths", []))
    batched_case_set = set(batched_case_paths)
    publication_ok = (
        int(batches.get("total_cases", 0)) == len(mai_paths)
        and int(batches.get("full_100_case_batches", 0)) * int(batches.get("checkpoint_size", 0))
        == len(mai_paths)
        and int(batches.get("remainder_cases", 0)) == 0
        and len(batched_case_paths) == len(mai_paths)
        and batched_case_set == mai_paths
    )
    gates.append(
        _public_gate(
            "publication_batches_cover_cases",
            publication_ok,
            (
                f"{int(batches.get('total_batches', 0))} batches, "
                f"{len(batched_case_set)} unique case paths"
            ),
        )
    )

    forbidden_text_hits = []
    for deck in decks.values():
        haystack = f"{deck.path}\n{deck.text}"
        if any(marker in haystack for marker in PUBLIC_FORBIDDEN_TEXT_MARKERS):
            forbidden_text_hits.append(deck.path)
    gates.append(
        _public_gate(
            "public_boundary_text",
            not forbidden_text_hits,
            f"{len(forbidden_text_hits)} decks contain private-path or private-log markers",
        )
    )

    solver_output_files = []
    for path, node in all_public_files:
        lower_path = path.lower()
        if lower_path.endswith(PUBLIC_FORBIDDEN_OUTPUT_SUFFIXES):
            solver_output_files.append(path)
    gates.append(
        _public_gate(
            "no_solver_output_files",
            not solver_output_files,
            (
                f"{len(solver_output_files)} solver-output files"
            ),
        )
    )

    old_motor_files = [path for path, _node in all_public_files if path.startswith("motor/")]
    application_hierarchy_ok = all(deck.path.startswith("application/") for deck in decks.values())
    gates.append(
        _public_gate(
            "application_hierarchy",
            application_hierarchy_ok and not old_motor_files,
            (
                f"{len(old_motor_files)} top-level motor files, "
                f"{sum(1 for deck in decks.values() if deck.path.startswith('application/motor/'))} "
                "motor input files under application/motor"
            ),
        )
    )

    known_levels = set(QUALITY_LABELS)
    unknown_level_families = [
        family
        for family, entry in manifest_families.items()
        if entry.get("validation_level") not in known_levels
    ]
    gates.append(
        _public_gate(
            "quality_labels_cover_manifest",
            not unknown_level_families,
            (
                f"{len(manifest_family_names) - len(unknown_level_families)} "
                f"of {len(manifest_family_names)} families have public quality labels"
            ),
        )
    )

    flum_case_count = sum(
        1
        for deck in decks.values()
        if deck.ext == "mai" and "FLUM" in deck.text.upper()
    )
    gates.append(
        _public_gate(
            "observable_flum_coverage",
            flum_case_count > 0,
            f"{flum_case_count} .mai decks include FLUM-observable requests",
        )
    )

    representative_missing = [
        f"{entry['family']}/{entry['case']}/{entry['case']}.mai"
        for entry in REPRESENTATIVE_CASES
        if f"{entry['family']}/{entry['case']}/{entry['case']}.mai" not in decks
    ]
    gates.append(
        _public_gate(
            "representatives_resolve",
            not representative_missing,
            (
                f"{len(REPRESENTATIVE_CASES) - len(representative_missing)} "
                f"of {len(REPRESENTATIVE_CASES)} representative paths resolve"
            ),
        )
    )
    gates.extend(
        _build_physical_quantity_gates(
            build_physical_quantity_summary(include_gates=False)
        )
    )
    gates.extend(
        _build_cross_validation_gates(
            build_cross_validation_summary(include_gates=False)
        )
    )
    gates.extend(
        _build_validation_matrix_gates(
            build_validation_matrix(include_gates=False)
        )
    )
    gates.extend(
        _build_observable_contract_gates(
            build_observable_contract_summary(include_gates=False)
        )
    )

    return gates


def get_family_validation(family: str) -> dict[str, Any]:
    """Return public validation metadata for one sample family."""
    entry = load_validated_manifest().get("families", {}).get(family)
    if entry is None:
        return {
            "family": family,
            "validation": "unknown",
            "validation_level": "unknown",
            "validation_scope": "No public validation manifest entry found.",
            "checks": [],
            "cases": 0,
            "input_files": 0,
        }
    return {
        "family": family,
        "validation": entry.get("validation", ""),
        "validation_level": entry.get("validation_level", ""),
        "validation_scope": entry.get("validation_scope", ""),
        "checks": list(entry.get("checks", [])),
        "cases": int(entry.get("cases", 0)),
        "input_files": int(entry.get("input_files", 0)),
        "validated_on": entry.get("validated_on", ""),
    }


def quality_label_for_level(level: str) -> dict[str, str]:
    """Return public quality label metadata for a validation level."""
    return QUALITY_LABELS.get(
        level,
        {
            "label": "unlabeled",
            "display": "Unlabeled",
            "meaning": "No public quality label is defined for this validation level.",
            "recommended_use": "Inspect validation metadata before reuse.",
        },
    )


def family_has_observable_contract(family: str) -> bool:
    """Return whether a family belongs to the 500-case observable-contract set."""
    return family in ENHANCED_OBSERVABLE_CONTRACT_FAMILIES


def quality_label_for_family(family: str) -> dict[str, str]:
    """Return public quality label metadata for one sample family."""
    validation = get_family_validation(family)
    if (
        validation.get("validation_level") == "ngsolve_proxy_energy"
        and family_has_observable_contract(family)
    ):
        return dict(ENHANCED_OBSERVABLE_CONTRACT_LABEL)
    return quality_label_for_level(validation["validation_level"])


def _sample_cases() -> list[dict[str, Any]]:
    decks = load_sample_decks()
    cases = []
    for mai in sorted((deck for deck in decks.values() if deck.ext == "mai"), key=lambda d: d.path):
        meg_path = f"{mai.path.rsplit('.', 1)[0]}.meg"
        meg = decks.get(meg_path)
        cases.append(
            {
                "family": mai.family,
                "case": mai.case,
                "mai_path": mai.path,
                "meg_path": meg_path,
                "mai_text": mai.text,
                "meg_text": meg.text if meg else "",
            }
        )
    return cases


def _physical_quantity_keys_for_case(case: dict[str, Any]) -> tuple[str, ...]:
    family = str(case["family"])
    meta = _family_meta(family)
    context = " ".join(
        [
            family,
            meta["title"],
            " ".join(meta["tags"]),
            meta["hint"],
            str(case["mai_text"]),
            str(case["meg_text"]),
        ]
    )
    lower = context.lower()
    upper = context.upper()
    keys: set[str] = set()

    if "FLUM" in upper:
        keys.add("flux_linkage")
    if family.startswith("application/motor/"):
        keys.add("motor_flux_linkage")
    if "OHM2" in upper or "MAB8T" in upper:
        keys.add("eddy_current_response")
    if (
        "numeric_ac_loss" in family
        or "ac-loss" in lower
        or "eddy-current" in lower
        or ("OHM2" in upper and ("FREQ" in upper or "MOMC" in upper))
    ):
        keys.add("ac_loss")
    if (
        "numeric_inductance_energy" in family
        or "inductance" in lower
        or "co-energy" in lower
        or "coenergy" in lower
    ):
        keys.add("inductance_coenergy")
    if (
        "numeric_force_torque" in family
        or "force" in lower
        or "torque" in lower
        or "static_torque" in family
    ):
        keys.add("force_torque_gradient")
    if (
        "numeric_magnetic_circuit" in family
        or "magnetic-circuit" in lower
        or "reluctance" in lower
        or ("MMB8T" in upper and "HBCU" in upper)
    ):
        keys.add("magnetic_circuit_flux")
    if (
        "numeric_permanent_magnet" in family
        or "permanent-magnet" in lower
        or "surface-pm" in lower
        or "HBRM" in upper
        or "MWL8T" in upper
    ):
        keys.add("permanent_magnet_flux")
    if "transformer" in lower:
        keys.add("transformer_coupling")
    if "wpt" in lower or "wireless-power" in lower:
        keys.add("wpt_mutual_coupling")
    if "mri" in lower or "gradient-coil" in lower:
        keys.add("mri_gradient_shielding")
    if any(
        term in lower
        for term in (
            "actuator",
            "plunger",
            "solenoid",
            "relay",
            "voice-coil",
            "clutch",
        )
    ):
        keys.add("actuator_force_proxy")
    if "accelerator" in lower or "corrector" in lower or "quadrupole" in lower:
        keys.add("accelerator_field_quality")

    return tuple(key for key in PHYSICAL_QUANTITY_ORDER if key in keys)


def _matches_physical_quantity_filter(key: str, query: str) -> bool:
    if not query:
        return True
    definition = PHYSICAL_QUANTITY_DEFINITIONS[key]
    haystack = " ".join(
        [
            key,
            definition["display"],
            definition["observable"],
            definition["validation_focus"],
        ]
    ).lower()
    return query.lower() in haystack


def _build_physical_quantity_gates(summary: dict[str, Any]) -> list[dict[str, str]]:
    counts = summary["quantity_counts"]
    no_quantity_families = [
        row["family"] for row in summary["families"] if not row["quantity_keys"]
    ]
    missing_gold = [
        key
        for key in GOLD_PHYSICS_ANCHORS
        if counts.get(key, {}).get("gold_cases", 0) <= 0
    ]
    gates = [
        _public_gate(
            "physical_quantity_case_coverage",
            summary["cases_with_quantities"] == summary["total_cases"],
            (
                f"{summary['cases_with_quantities']} of {summary['total_cases']} "
                "cases map to at least one physical quantity"
            ),
        ),
        _public_gate(
            "physical_quantity_family_coverage",
            not no_quantity_families,
            (
                f"{summary['total_families'] - len(no_quantity_families)} "
                f"of {summary['total_families']} families map to physical quantities"
            ),
        ),
        _public_gate(
            "gold_physics_anchor_coverage",
            not missing_gold,
            (
                "gold invariant anchors cover "
                + ", ".join(GOLD_PHYSICS_ANCHORS)
                if not missing_gold
                else "missing gold anchors for " + ", ".join(missing_gold)
            ),
        ),
        _public_gate(
            "flux_linkage_observable_all_cases",
            counts.get("flux_linkage", {}).get("cases", 0) == summary["total_cases"],
            (
                f"{counts.get('flux_linkage', {}).get('cases', 0)} "
                f"of {summary['total_cases']} cases include FLUM observables"
            ),
        ),
        _public_gate(
            "motor_physical_quantity_coverage",
            counts.get("motor_flux_linkage", {}).get("cases", 0)
            == summary["motor_case_count"],
            (
                f"{counts.get('motor_flux_linkage', {}).get('cases', 0)} "
                f"of {summary['motor_case_count']} motor cases map to motor flux linkage"
            ),
        ),
        _public_gate(
            "conductive_physics_coverage",
            counts.get("eddy_current_response", {}).get("cases", 0)
            >= summary["ohm2_case_count"],
            (
                f"{counts.get('eddy_current_response', {}).get('cases', 0)} "
                f"conductive-response cases for {summary['ohm2_case_count']} OHM2 cases"
            ),
        ),
    ]
    return gates


def build_physical_quantity_summary(
    quantity: str | None = None,
    family: str | None = None,
    include_gates: bool = True,
) -> dict[str, Any]:
    """Build public physical-quantity coverage for the sample deck corpus."""
    quantity_filter = (quantity or "").strip().lower()
    family_filter = (family or "").strip().lower()
    manifest = load_validated_manifest()
    active_quantity_keys = [
        key
        for key in PHYSICAL_QUANTITY_ORDER
        if _matches_physical_quantity_filter(key, quantity_filter)
    ]
    quantity_counts = {
        key: {
            "display": PHYSICAL_QUANTITY_DEFINITIONS[key]["display"],
            "observable": PHYSICAL_QUANTITY_DEFINITIONS[key]["observable"],
            "validation_focus": PHYSICAL_QUANTITY_DEFINITIONS[key]["validation_focus"],
            "families": set(),
            "cases": 0,
            "gold_cases": 0,
            "silver_cases": 0,
            "representative_paths": [],
        }
        for key in active_quantity_keys
    }
    family_rows: dict[str, dict[str, Any]] = {}
    cases_with_quantities = 0
    selected_case_count = 0
    total_case_count = 0
    motor_case_count = 0
    ohm2_case_count = 0

    for case in _sample_cases():
        total_case_count += 1
        if case["family"].startswith("application/motor/"):
            motor_case_count += 1
        combined_upper = f"{case['mai_text']}\n{case['meg_text']}".upper()
        if "OHM2" in combined_upper:
            ohm2_case_count += 1

        all_keys = _physical_quantity_keys_for_case(case)
        if all_keys:
            cases_with_quantities += 1
        if family_filter and family_filter not in str(case["family"]).lower():
            continue
        keys = [key for key in all_keys if key in active_quantity_keys]
        if quantity_filter and not keys:
            continue
        if not quantity_filter:
            keys = list(all_keys)
        if not keys:
            continue
        selected_case_count += 1

        validation = manifest.get("families", {}).get(case["family"], {})
        quality = quality_label_for_family(case["family"])
        row = family_rows.setdefault(
            case["family"],
            {
                "family": case["family"],
                "title": _family_meta(case["family"])["title"],
                "cases": 0,
                "quantity_cases": {},
                "quantity_keys": set(),
                "validation_level": validation.get("validation_level", ""),
                "quality_label": quality["label"],
                "quality_display": quality["display"],
                "representative_paths": representative_paths_for_family(case["family"], limit=2),
            },
        )
        row["cases"] += 1
        for key in keys:
            row["quantity_keys"].add(key)
            row["quantity_cases"][key] = row["quantity_cases"].get(key, 0) + 1
            qrow = quantity_counts[key]
            qrow["families"].add(case["family"])
            qrow["cases"] += 1
            if quality["label"] == "gold_numeric_invariant":
                qrow["gold_cases"] += 1
            elif quality["label"] == "silver_proxy_energy":
                qrow["silver_cases"] += 1
            if len(qrow["representative_paths"]) < 3:
                reps = representative_paths_for_family(case["family"], limit=1)
                for path in reps:
                    if path not in qrow["representative_paths"]:
                        qrow["representative_paths"].append(path)

    serial_quantity_counts = {}
    for key, row in quantity_counts.items():
        serial_quantity_counts[key] = {
            "display": row["display"],
            "observable": row["observable"],
            "validation_focus": row["validation_focus"],
            "families": len(row["families"]),
            "cases": row["cases"],
            "gold_cases": row["gold_cases"],
            "silver_cases": row["silver_cases"],
            "representative_paths": list(row["representative_paths"]),
        }
    serial_family_rows = []
    for row in sorted(family_rows.values(), key=lambda item: item["family"]):
        quantity_keys = [key for key in PHYSICAL_QUANTITY_ORDER if key in row["quantity_keys"]]
        serial_family_rows.append(
            {
                "family": row["family"],
                "title": row["title"],
                "cases": row["cases"],
                "quantity_keys": quantity_keys,
                "quantity_cases": {
                    key: row["quantity_cases"].get(key, 0)
                    for key in quantity_keys
                },
                "validation_level": row["validation_level"],
                "quality_label": row["quality_label"],
                "quality_display": row["quality_display"],
                "representative_paths": row["representative_paths"],
            }
        )

    summary = {
        "schema_version": manifest.get("schema_version"),
        "total_cases": total_case_count,
        "total_families": len(manifest.get("families", {})),
        "selected_cases": selected_case_count,
        "selected_family_count": len(serial_family_rows),
        "cases_with_quantities": cases_with_quantities,
        "motor_case_count": motor_case_count,
        "ohm2_case_count": ohm2_case_count,
        "quantity_filter": quantity or "",
        "family_filter": family or "",
        "quantity_counts": serial_quantity_counts,
        "families": serial_family_rows,
        "limitations": [
            "Physical quantity coverage is inferred from public input decks and validation metadata.",
            "It does not expose private solver outputs or absolute commercial benchmark numbers.",
            "Gold labels indicate public numeric-invariant checks; silver labels indicate runnable proxy-energy gates.",
        ],
    }
    if include_gates and not quantity_filter and not family_filter:
        physical_gates = _build_physical_quantity_gates(summary)
        summary["physical_gate_status"] = (
            "PASS" if all(gate["status"] == "PASS" for gate in physical_gates) else "FAIL"
        )
        summary["physical_gates"] = physical_gates
    else:
        summary["physical_gate_status"] = ""
        summary["physical_gates"] = []
    return summary


def _cross_validation_methods_for_checks(checks: list[str]) -> list[dict[str, str]]:
    methods = []
    for check in checks:
        method = CROSS_VALIDATION_METHODS.get(check)
        if method:
            methods.append({"check": check, **method})
    return methods


def _has_independent_cross_validation(checks: list[str]) -> bool:
    return any(check.startswith("ngsolve_") for check in checks)


def _build_cross_validation_gates(summary: dict[str, Any]) -> list[dict[str, str]]:
    method_counts = summary["method_counts"]
    gaps = summary["gaps"]
    return [
        _public_gate(
            "all_families_have_independent_cross_validation",
            gaps["families_without_independent_cross_validation"] == 0,
            (
                f"{summary['families_with_independent_cross_validation']} "
                f"of {summary['total_families']} families include an independent NGSolve check"
            ),
        ),
        _public_gate(
            "all_cases_have_independent_cross_validation",
            gaps["cases_without_independent_cross_validation"] == 0,
            (
                f"{summary['cases_with_independent_cross_validation']} "
                f"of {summary['total_cases']} cases include an independent NGSolve check"
            ),
        ),
        _public_gate(
            "gold_families_have_dual_invariant_validation",
            gaps["gold_families_without_dual_invariants"] == 0,
            (
                f"{method_counts.get('ngsolve_numeric_invariants_passed', {}).get('cases', 0)} "
                "gold cases have NGSolve numeric invariants"
            ),
        ),
        _public_gate(
            "silver_families_have_proxy_energy_cross_validation",
            gaps["silver_families_without_proxy_energy"] == 0,
            (
                f"{method_counts.get('ngsolve_proxy_energy_positive', {}).get('cases', 0)} "
                "silver cases have NGSolve proxy-energy checks"
            ),
        ),
        _public_gate(
            "cross_validation_tied_to_physical_quantities",
            gaps["families_without_physical_quantity"] == 0,
            (
                f"{summary['total_families'] - gaps['families_without_physical_quantity']} "
                f"of {summary['total_families']} cross-validated families map to physical quantities"
            ),
        ),
    ]


def build_cross_validation_summary(
    family: str | None = None,
    level: str | None = None,
    include_gates: bool = True,
) -> dict[str, Any]:
    """Build public cross-validation coverage and gap metadata."""
    manifest = load_validated_manifest()
    family_filter = (family or "").strip().lower()
    level_filter = (level or "").strip()
    physical = build_physical_quantity_summary(include_gates=False)
    family_to_quantities = {
        row["family"]: row["quantity_keys"]
        for row in physical["families"]
    }

    method_counts: dict[str, dict[str, int]] = {
        check: {"families": 0, "cases": 0}
        for check in CROSS_VALIDATION_METHODS
    }
    rows = []
    gap_rows = []
    upgrade_candidates = []
    cases_with_independent = 0
    families_with_independent = 0
    total_cases = int(manifest.get("total_cases", 0))

    for fam, entry in sorted(manifest.get("families", {}).items()):
        if family_filter and family_filter not in fam.lower():
            continue
        if level_filter and entry.get("validation_level") != level_filter:
            continue
        checks = list(entry.get("checks", []))
        methods = _cross_validation_methods_for_checks(checks)
        independent = _has_independent_cross_validation(checks)
        cases = int(entry.get("cases", 0))
        quality = quality_label_for_family(fam)
        quantity_keys = list(family_to_quantities.get(fam, []))

        if independent:
            families_with_independent += 1
            cases_with_independent += cases
        for method in methods:
            bucket = method_counts[method["check"]]
            bucket["families"] += 1
            bucket["cases"] += cases

        has_dual_gold = (
            entry.get("validation_level") == "ngsolve_numeric_invariant"
            and "analytic_flux_invariants_passed" in checks
            and "ngsolve_numeric_invariants_passed" in checks
        )
        has_silver_proxy = (
            entry.get("validation_level") == "ngsolve_proxy_energy"
            and "ngsolve_proxy_energy_positive" in checks
        )
        if not independent or not quantity_keys:
            gap_rows.append(
                {
                    "family": fam,
                    "cases": cases,
                    "validation_level": entry.get("validation_level", ""),
                    "missing": [
                        name
                        for name, condition in (
                            ("independent_ngsolve_cross_validation", independent),
                            ("physical_quantity_mapping", bool(quantity_keys)),
                        )
                        if not condition
                    ],
                }
            )
        if quality["label"] in {"silver_proxy_energy", "silver_observable_contract"}:
            upgrade_candidates.append(
                {
                    "family": fam,
                    "cases": cases,
                    "quantity_keys": quantity_keys,
                    "current_cross_validation": "ngsolve_proxy_energy_positive",
                    "quality_label": quality["label"],
                    "possible_upgrade": (
                        "Add a family-specific public numeric invariant only when "
                        "the physical law is simple enough to verify without "
                        "publishing solver outputs."
                    ),
                }
            )

        rows.append(
            {
                "family": fam,
                "title": _family_meta(fam)["title"],
                "cases": cases,
                "validation_level": entry.get("validation_level", ""),
                "quality_label": quality["label"],
                "checks": checks,
                "cross_validation_methods": methods,
                "has_independent_cross_validation": independent,
                "has_gold_dual_invariants": has_dual_gold,
                "has_silver_proxy_energy": has_silver_proxy,
                "quantity_keys": quantity_keys,
                "validation_scope": entry.get("validation_scope", ""),
                "representative_paths": representative_paths_for_family(fam, limit=2),
            }
        )

    all_manifest_families = manifest.get("families", {})
    global_missing_independent = [
        fam
        for fam, entry in all_manifest_families.items()
        if not _has_independent_cross_validation(list(entry.get("checks", [])))
    ]
    global_missing_physics = [
        fam
        for fam in all_manifest_families
        if not family_to_quantities.get(fam)
    ]
    global_gold_without_dual = [
        fam
        for fam, entry in all_manifest_families.items()
        if entry.get("validation_level") == "ngsolve_numeric_invariant"
        and not (
            "analytic_flux_invariants_passed" in entry.get("checks", [])
            and "ngsolve_numeric_invariants_passed" in entry.get("checks", [])
        )
    ]
    global_silver_without_proxy = [
        fam
        for fam, entry in all_manifest_families.items()
        if entry.get("validation_level") == "ngsolve_proxy_energy"
        and "ngsolve_proxy_energy_positive" not in entry.get("checks", [])
    ]
    gaps = {
        "families_without_independent_cross_validation": len(global_missing_independent),
        "cases_without_independent_cross_validation": sum(
            int(all_manifest_families[fam].get("cases", 0))
            for fam in global_missing_independent
        ),
        "families_without_physical_quantity": len(global_missing_physics),
        "gold_families_without_dual_invariants": len(global_gold_without_dual),
        "silver_families_without_proxy_energy": len(global_silver_without_proxy),
        "gap_families": sorted(set(global_missing_independent + global_missing_physics)),
    }
    summary = {
        "schema_version": manifest.get("schema_version"),
        "total_cases": total_cases,
        "total_families": len(all_manifest_families),
        "selected_cases": sum(row["cases"] for row in rows),
        "selected_family_count": len(rows),
        "cases_with_independent_cross_validation": cases_with_independent,
        "families_with_independent_cross_validation": families_with_independent,
        "method_counts": method_counts,
        "families": rows,
        "gaps": gaps,
        "upgrade_candidates": upgrade_candidates,
        "family_filter": family or "",
        "level_filter": level or "",
        "limitations": [
            "This public audit records validation contracts and categories, not solver outputs.",
            "No family is treated as publication-ready unless it has an independent NGSolve cross-check.",
            "Silver proxy-energy families are cross-validated but are not full absolute field, force, torque, or loss agreement claims.",
            "Gold numeric-invariant families add public FLUM-derived invariants and independent NGSolve proxy invariants.",
        ],
    }
    if include_gates and not family_filter and not level_filter:
        gates = _build_cross_validation_gates(summary)
        summary["cross_validation_gate_status"] = (
            "PASS" if all(gate["status"] == "PASS" for gate in gates) else "FAIL"
        )
        summary["cross_validation_gates"] = gates
    else:
        summary["cross_validation_gate_status"] = ""
        summary["cross_validation_gates"] = []
    return summary


def _quantity_matches_filter(key: str, needle: str) -> bool:
    if not needle:
        return True
    definition = PHYSICAL_QUANTITY_DEFINITIONS[key]
    haystack = " ".join(
        [
            key,
            definition["display"],
            definition["observable"],
            definition["validation_focus"],
        ]
    ).lower()
    return needle in haystack


def _append_unique_paths(target: list[str], paths: list[str], limit: int = 3) -> None:
    for path in paths:
        if path not in target:
            target.append(path)
        if len(target) >= limit:
            break


def _build_validation_matrix_gates(summary: dict[str, Any]) -> list[dict[str, str]]:
    family_rows = summary["families"]
    quantity_rows = summary["quantities"]
    gold_anchor_gaps = [
        key
        for key in GOLD_PHYSICS_ANCHORS
        if quantity_rows.get(key, {}).get("gold_cases", 0) <= 0
    ]
    missing_methods = [
        row["family"] for row in family_rows if not row["validation_methods"]
    ]
    missing_representatives = [
        row["family"] for row in family_rows if not row["representative_paths"]
    ]
    missing_next_calls = [
        row["family"] for row in family_rows if not row["recommended_calls"]
    ]
    return [
        _public_gate(
            "validation_matrix_covers_all_families",
            summary["selected_family_count"] == summary["total_families"],
            (
                f"{summary['selected_family_count']} of {summary['total_families']} "
                "families appear in the unfiltered validation matrix"
            ),
        ),
        _public_gate(
            "validation_matrix_covers_gold_physics_anchors",
            not gold_anchor_gaps,
            (
                f"{len(GOLD_PHYSICS_ANCHORS) - len(gold_anchor_gaps)} "
                f"of {len(GOLD_PHYSICS_ANCHORS)} gold physics anchors have gold cases"
            ),
        ),
        _public_gate(
            "validation_matrix_has_cross_validation_methods",
            not missing_methods,
            f"{len(missing_methods)} families lack matrix cross-validation methods",
        ),
        _public_gate(
            "validation_matrix_has_representatives",
            not missing_representatives,
            f"{len(missing_representatives)} families lack representative .mai paths",
        ),
        _public_gate(
            "validation_matrix_has_next_calls",
            not missing_next_calls,
            f"{len(missing_next_calls)} families lack next MCP calls",
        ),
    ]


def build_validation_matrix(
    quantity: str | None = None,
    family: str | None = None,
    label: str | None = None,
    include_gates: bool = True,
) -> dict[str, Any]:
    """Build a prompt-routing matrix across quantities, quality, and validation."""
    manifest = load_validated_manifest()
    quantity_filter = (quantity or "").strip().lower()
    family_filter = (family or "").strip().lower()
    label_filter = (label or "").strip().lower()
    physical = build_physical_quantity_summary(include_gates=False)
    cross_validation = build_cross_validation_summary(include_gates=False)
    cross_by_family = {
        row["family"]: row
        for row in cross_validation["families"]
    }

    quantity_accumulator: dict[str, dict[str, Any]] = {
        key: {
            "display": definition["display"],
            "observable": definition["observable"],
            "validation_focus": definition["validation_focus"],
            "families": set(),
            "cases": 0,
            "gold_cases": 0,
            "silver_cases": 0,
            "validation_methods": set(),
            "quality_enhancements": set(),
            "representative_paths": [],
        }
        for key, definition in PHYSICAL_QUANTITY_DEFINITIONS.items()
    }
    family_rows = []

    for prow in physical["families"]:
        fam = prow["family"]
        if family_filter and family_filter not in fam.lower():
            continue
        validation = get_family_validation(fam)
        quality = quality_label_for_family(fam)
        if (
            label_filter
            and label_filter not in quality["label"].lower()
            and label_filter not in quality["display"].lower()
            and label_filter not in validation.get("validation_level", "").lower()
        ):
            continue
        quantity_keys = [
            key
            for key in prow["quantity_keys"]
            if _quantity_matches_filter(key, quantity_filter)
        ]
        if not quantity_keys:
            continue

        cross_row = cross_by_family.get(fam, {})
        methods = [
            {
                "check": method["check"],
                "display": method["display"],
                "strength": method["strength"],
                "public_observable": method.get("public_observable", ""),
            }
            for method in cross_row.get("cross_validation_methods", [])
        ]
        method_checks = [method["check"] for method in methods]
        quality_enhancements = []
        if family_has_observable_contract(fam):
            quality_enhancements.append(PUBLIC_OBSERVABLE_CONTRACT_CHECK)
        representatives = representative_paths_for_family(fam, limit=3)
        short_family = fam.rsplit("/", 1)[-1]
        recommended_calls = [
            f'elf_sample_decks_route("{prow["title"]}")',
            f'elf_sample_decks_playbook(limit=10, family="{short_family}")',
            f'elf_sample_decks_validation(family="{short_family}")',
            f'elf_sample_decks_cross_validation(family="{short_family}")',
        ]

        for key in quantity_keys:
            qrow = quantity_accumulator[key]
            qcases = int(prow["quantity_cases"].get(key, prow["cases"]))
            qrow["families"].add(fam)
            qrow["cases"] += qcases
            if quality["label"] == "gold_numeric_invariant":
                qrow["gold_cases"] += qcases
            elif quality["label"] == "silver_proxy_energy":
                qrow["silver_cases"] += qcases
            qrow["validation_methods"].update(method_checks)
            qrow["quality_enhancements"].update(
                enhancement["check"] for enhancement in quality_enhancements
            )
            _append_unique_paths(qrow["representative_paths"], representatives, limit=3)

        family_rows.append(
            {
                "family": fam,
                "title": prow["title"],
                "cases": int(prow["cases"]),
                "validation_level": validation.get("validation_level", ""),
                "quality_label": quality["label"],
                "quality_display": quality["display"],
                "recommended_use": quality["recommended_use"],
                "quantity_keys": quantity_keys,
                "evidence_contract": [
                    {
                        "quantity": key,
                        "observable": PHYSICAL_QUANTITY_DEFINITIONS[key]["observable"],
                        "validation_focus": PHYSICAL_QUANTITY_DEFINITIONS[key]["validation_focus"],
                    }
                    for key in quantity_keys
                ],
                "validation_methods": methods,
                "quality_enhancements": quality_enhancements,
                "has_independent_cross_validation": bool(
                    cross_row.get("has_independent_cross_validation", False)
                ),
                "representative_paths": representatives,
                "recommended_calls": recommended_calls,
            }
        )

    serial_quantities = {}
    for key in PHYSICAL_QUANTITY_ORDER:
        row = quantity_accumulator[key]
        if not row["families"]:
            continue
        serial_quantities[key] = {
            "display": row["display"],
            "observable": row["observable"],
            "validation_focus": row["validation_focus"],
            "families": len(row["families"]),
            "cases": row["cases"],
            "gold_cases": row["gold_cases"],
            "silver_cases": row["silver_cases"],
            "validation_methods": sorted(row["validation_methods"]),
            "quality_enhancements": sorted(row["quality_enhancements"]),
            "representative_paths": list(row["representative_paths"]),
        }

    summary = {
        "schema_version": manifest.get("schema_version"),
        "total_cases": int(manifest.get("total_cases", 0)),
        "total_families": len(manifest.get("families", {})),
        "selected_cases": sum(row["cases"] for row in family_rows),
        "selected_family_count": len(family_rows),
        "quantity_filter": quantity or "",
        "family_filter": family or "",
        "label_filter": label or "",
        "quantities": serial_quantities,
        "families": family_rows,
        "notes": list(VALIDATION_MATRIX_NOTES),
    }
    if include_gates and not quantity_filter and not family_filter and not label_filter:
        gates = _build_validation_matrix_gates(summary)
        summary["validation_matrix_gate_status"] = (
            "PASS" if all(gate["status"] == "PASS" for gate in gates) else "FAIL"
        )
        summary["validation_matrix_gates"] = gates
    else:
        summary["validation_matrix_gate_status"] = ""
        summary["validation_matrix_gates"] = []
    return summary


def _build_observable_contract_gates(summary: dict[str, Any]) -> list[dict[str, str]]:
    return [
        _public_gate(
            "observable_contract_target_is_500_cases",
            summary["enhanced_cases"] == 500,
            f"{summary['enhanced_cases']} cases are covered by observable contracts",
        ),
        _public_gate(
            "observable_contract_families_resolve",
            summary["missing_family_count"] == 0,
            f"{summary['missing_family_count']} configured families are absent from the deck corpus",
        ),
        _public_gate(
            "observable_contract_markers_pass",
            summary["failed_case_count"] == 0,
            f"{summary['failed_case_count']} enhanced cases are missing required public markers",
        ),
        _public_gate(
            "observable_contract_independent_cross_validation",
            summary["families_without_independent_cross_validation"] == 0,
            (
                f"{summary['enhanced_family_count'] - summary['families_without_independent_cross_validation']} "
                f"of {summary['enhanced_family_count']} enhanced families retain independent NGSolve checks"
            ),
        ),
    ]


def build_observable_contract_summary(
    family: str | None = None,
    label: str | None = None,
    include_gates: bool = True,
) -> dict[str, Any]:
    """Build the 500-case public observable-contract quality audit."""
    family_filter = (family or "").strip().lower()
    label_filter = (label or "").strip().lower()
    decks = load_sample_decks()
    manifest = load_validated_manifest()
    physical = build_physical_quantity_summary(include_gates=False)
    quantities_by_family = {
        row["family"]: row["quantity_keys"]
        for row in physical["families"]
    }
    rows = []
    missing_families = []
    failed_cases = []
    missing_independent = []
    enhanced_cases = 0

    for fam, required_markers in sorted(ENHANCED_OBSERVABLE_CONTRACT_FAMILIES.items()):
        if family_filter and family_filter not in fam.lower():
            continue
        validation = get_family_validation(fam)
        quality = quality_label_for_family(fam)
        if (
            label_filter
            and label_filter not in quality["label"].lower()
            and label_filter not in quality["display"].lower()
        ):
            continue
        fam_decks = sorted(
            (
                deck
                for deck in decks.values()
                if deck.family == fam and deck.ext == "mai"
            ),
            key=lambda deck: deck.path,
        )
        if not fam_decks:
            missing_families.append(fam)
            continue
        checks = list(validation.get("checks", []))
        has_independent = _has_independent_cross_validation(checks)
        if not has_independent:
            missing_independent.append(fam)

        case_failures = []
        for deck in fam_decks:
            upper = deck.text.upper()
            missing = [marker for marker in required_markers if marker not in upper]
            if missing:
                case_failures.append(
                    {
                        "path": deck.path,
                        "missing_markers": missing,
                    }
                )
        if case_failures:
            failed_cases.extend(case_failures)

        cases = len(fam_decks)
        enhanced_cases += cases
        rows.append(
            {
                "family": fam,
                "title": _family_meta(fam)["title"],
                "cases": cases,
                "quality_label": quality["label"],
                "quality_display": quality["display"],
                "validation_level": validation.get("validation_level", ""),
                "checks": checks,
                "required_markers": list(required_markers),
                "passed_cases": cases - len(case_failures),
                "failed_cases": len(case_failures),
                "has_independent_cross_validation": has_independent,
                "quantity_keys": quantities_by_family.get(fam, []),
                "representative_paths": representative_paths_for_family(fam, limit=2),
                "enhancement_check": PUBLIC_OBSERVABLE_CONTRACT_CHECK,
            }
        )

    summary = {
        "schema_version": manifest.get("schema_version"),
        "configured_family_count": len(ENHANCED_OBSERVABLE_CONTRACT_FAMILIES),
        "enhanced_family_count": len(rows),
        "enhanced_cases": enhanced_cases,
        "missing_family_count": len(missing_families),
        "missing_families": missing_families,
        "failed_case_count": len(failed_cases),
        "failed_cases": failed_cases[:20],
        "families_without_independent_cross_validation": len(missing_independent),
        "families_missing_independent_cross_validation": missing_independent,
        "family_filter": family or "",
        "label_filter": label or "",
        "families": rows,
        "notes": [
            "This 500-case upgrade is a public observable-contract gate, not a hidden solver-output disclosure.",
            "The gate checks that each selected public `.mai` deck exposes the markers needed to evaluate its mapped physical quantity.",
            "The enhanced label remains below gold numeric-invariant status unless public numeric scaling/sign/law invariants are added.",
        ],
    }
    if include_gates and not family_filter and not label_filter:
        gates = _build_observable_contract_gates(summary)
        summary["observable_contract_gate_status"] = (
            "PASS" if all(gate["status"] == "PASS" for gate in gates) else "FAIL"
        )
        summary["observable_contract_gates"] = gates
    else:
        summary["observable_contract_gate_status"] = ""
        summary["observable_contract_gates"] = []
    return summary


def build_quality_summary(family: str | None = None, label: str | None = None) -> dict[str, Any]:
    """Build quality-label counts and selected family rows for MCP clients."""
    manifest = load_validated_manifest()
    quality_gates = build_public_quality_gates()
    family_filter = family.lower() if family else ""
    label_filter = label.lower() if label else ""
    rows = []
    label_counts: dict[str, dict[str, int]] = {}
    for fam, entry in sorted(manifest.get("families", {}).items()):
        q = quality_label_for_family(fam)
        if family_filter and family_filter not in fam.lower():
            continue
        if (
            label_filter
            and label_filter not in q["label"].lower()
            and label_filter not in q["display"].lower()
        ):
            continue
        label_counts.setdefault(q["label"], {"families": 0, "cases": 0, "input_files": 0})
        label_counts[q["label"]]["families"] += 1
        label_counts[q["label"]]["cases"] += int(entry.get("cases", 0))
        label_counts[q["label"]]["input_files"] += int(entry.get("input_files", 0))
        meta = _family_meta(fam)
        rows.append(
            {
                "family": fam,
                "title": meta["title"],
                "cases": int(entry.get("cases", 0)),
                "input_files": int(entry.get("input_files", 0)),
                "validation_level": entry.get("validation_level", ""),
                "quality_label": q["label"],
                "quality_display": q["display"],
                "quality_meaning": q["meaning"],
                "recommended_use": q["recommended_use"],
                "checks": list(entry.get("checks", [])),
                "validation_scope": entry.get("validation_scope", ""),
            }
        )
    return {
        "schema_version": manifest.get("schema_version"),
        "total_cases": int(manifest.get("total_cases", 0)),
        "total_input_files": int(manifest.get("total_input_files", 0)),
        "selected_family_count": len(rows),
        "selected_cases": sum(row["cases"] for row in rows),
        "selected_input_files": sum(row["input_files"] for row in rows),
        "label_counts": label_counts,
        "families": rows,
        "family_filter": family or "",
        "label_filter": label or "",
        "label_definitions": QUALITY_LABEL_DEFINITIONS,
        "quality_gate_status": (
            "PASS" if all(gate["status"] == "PASS" for gate in quality_gates) else "FAIL"
        ),
        "quality_gates": quality_gates,
    }


def build_validation_summary(
    family: str | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Build a public validation summary for MCP clients."""
    manifest = load_validated_manifest()
    all_families = manifest.get("families", {})
    family_filter = family.lower() if family else None
    level_filter = level.strip() if level else None

    selected: dict[str, dict[str, Any]] = {}
    for name, entry in sorted(all_families.items()):
        if family_filter and family_filter not in name.lower():
            continue
        if level_filter and entry.get("validation_level") != level_filter:
            continue
        selected[name] = entry

    family_rows = []
    for name, entry in selected.items():
        family_rows.append(
            {
                "family": name,
                "cases": int(entry.get("cases", 0)),
                "input_files": int(entry.get("input_files", 0)),
                "validation": entry.get("validation", ""),
                "validation_level": entry.get("validation_level", ""),
                "validation_scope": entry.get("validation_scope", ""),
                "checks": list(entry.get("checks", [])),
                "validated_on": entry.get("validated_on", ""),
            }
        )

    return {
        "schema_version": manifest.get("schema_version"),
        "total_cases": int(manifest.get("total_cases", 0)),
        "total_input_files": int(manifest.get("total_input_files", 0)),
        "total_families": len(all_families),
        "level_counts": _validation_counts(all_families),
        "selected_cases": sum(row["cases"] for row in family_rows),
        "selected_input_files": sum(row["input_files"] for row in family_rows),
        "selected_family_count": len(family_rows),
        "selected_level_counts": _validation_counts(selected),
        "families": family_rows,
        "publication_batches": build_publication_batch_summary(),
        "family_filter": family or "",
        "level_filter": level or "",
        "limitations": list(VALIDATION_LIMITATIONS),
        "recommended_calls": [
            'elf_sample_decks_validation(level="ngsolve_numeric_invariant")',
            'elf_sample_decks_validation(family="numeric_transformer_coupling")',
            'elf_sample_decks_validation(family="numeric_permanent_magnet")',
            'elf_sample_decks_validation(family="numeric_magnetic_circuit")',
            'elf_sample_decks_validation(family="numeric_ac_loss")',
            'elf_sample_decks_validation(family="numeric_force_torque")',
            'elf_sample_decks_validation(family="numeric_inductance_energy")',
            'elf_sample_decks_validation(family="numeric_flum_law")',
            'elf_sample_decks_validation(family="numeric_validation")',
            'elf_sample_decks_route("transformer coupling turns ratio HBCU FLUM")',
            'elf_sample_decks_route("permanent magnet HBRM polarity FLUM")',
            'elf_sample_decks_route("magnetic circuit air gap HBCU")',
            'elf_sample_decks_route("AC loss frequency square OHM2")',
            'elf_sample_decks_route("force torque co-energy gradient")',
            'elf_sample_decks_route("inductance co-energy FLUM turn scaling")',
            'elf_sample_decks_route("FLUM law current linearity superposition")',
            'elf_sample_decks_route("numeric validation anchor FLUM invariant")',
        ],
    }


def _ordered_levels(counts: dict[str, dict[str, Any]]) -> list[str]:
    ordered = [level for level in VALIDATION_LEVEL_ORDER if level in counts]
    ordered.extend(sorted(level for level in counts if level not in ordered))
    return ordered


def format_validation_summary(summary: dict[str, Any], max_families: int = 20) -> str:
    """Format public validation metadata as Markdown."""
    lines = [
        "# Public sample-deck validation",
        "",
        f"- manifest schema: {summary['schema_version']}",
        (
            f"- public corpus: {summary['total_cases']} cases, "
            f"{summary['total_input_files']} input files, "
            f"{summary['total_families']} families"
        ),
        "- publication rule: only manifest-listed `validation: passed` families are bundled",
        "",
        "## Validation levels",
    ]
    for level in _ordered_levels(summary["level_counts"]):
        count = summary["level_counts"][level]
        description = count.get("description") or VALIDATION_LEVEL_DESCRIPTIONS.get(level, "")
        lines.append(
            f"- `{level}`: {count['families']} families, "
            f"{count['cases']} cases, {count['input_files']} input files"
        )
        if description:
            lines.append(f"  scope: {description}")

    lines.extend(["", "## Selected families"])
    filter_bits = []
    if summary["family_filter"]:
        filter_bits.append(f"family contains `{summary['family_filter']}`")
    if summary["level_filter"]:
        filter_bits.append(f"level is `{summary['level_filter']}`")
    if filter_bits:
        lines.append(f"- filter: {', '.join(filter_bits)}")
    else:
        lines.append("- filter: none")
    lines.append(
        f"- selected: {summary['selected_family_count']} families, "
        f"{summary['selected_cases']} cases, "
        f"{summary['selected_input_files']} input files"
    )

    shown = summary["families"][: max(0, max_families)]
    for row in shown:
        lines.append(
            f"- `{row['family']}`: {row['cases']} cases, "
            f"level `{row['validation_level']}`, checks: {', '.join(row['checks'])}"
        )
        if row.get("validation_scope"):
            lines.append(f"  scope: {row['validation_scope']}")
    hidden = summary["selected_family_count"] - len(shown)
    if hidden > 0:
        lines.append(f"- ... {hidden} more families. Narrow with `family=` or `level=`.")

    lines.extend(["", "## Limits"])
    lines.extend(f"- {item}" for item in summary["limitations"])
    batches = summary.get("publication_batches", {})
    if batches:
        lines.extend(["", "## 100-case publication checkpoints"])
        lines.append(f"- checkpoint size: {batches['checkpoint_size']} cases")
        lines.append(
            f"- baseline: {batches['full_100_case_batches']} full checkpoints "
            f"+ {batches['remainder_cases']} release-remainder cases "
            f"({batches['total_cases']} cases total)"
        )
        lines.append(
            f"- next checkpoint: {batches['next_checkpoint_cases']} cases; "
            f"{batches['additional_cases_needed_for_next_100_case_checkpoint']} "
            "additional validated cases would make the next optional increment"
        )
        for batch in batches["batches"][:5]:
            level_bits = ", ".join(
                f"{name}:{count}"
                for name, count in sorted(batch["validation_level_counts"].items())
            )
            lines.append(
                f"- `{batch['batch_id']}`: {batch['case_start']}-{batch['case_end']} "
                f"({batch['case_count']} cases, {batch['batch_kind']}, {level_bits})"
            )
        hidden_batches = batches["total_batches"] - min(5, len(batches["batches"]))
        if hidden_batches > 0:
            lines.append(f"- ... {hidden_batches} more checkpoint batches.")
    lines.extend(["", "## Recommended MCP calls"])
    lines.extend(f"- `{call}`" for call in summary["recommended_calls"])
    return "\n".join(lines).rstrip()


def format_validation_matrix(summary: dict[str, Any], max_families: int = 24) -> str:
    """Format the prompt-to-validation matrix as Markdown."""
    lines = [
        "# Public sample-deck validation matrix",
        "",
        (
            f"- corpus: {summary['total_cases']} cases, "
            f"{summary['total_families']} families"
        ),
        (
            f"- selected: {summary['selected_cases']} cases, "
            f"{summary['selected_family_count']} families"
        ),
    ]
    filters = []
    if summary["quantity_filter"]:
        filters.append(f"quantity contains `{summary['quantity_filter']}`")
    if summary["family_filter"]:
        filters.append(f"family contains `{summary['family_filter']}`")
    if summary["label_filter"]:
        filters.append(f"label contains `{summary['label_filter']}`")
    lines.append(f"- filter: {', '.join(filters) if filters else 'none'}")

    if summary.get("validation_matrix_gates"):
        lines.extend(["", f"## Validation Matrix Gates ({summary['validation_matrix_gate_status']})"])
        for gate in summary["validation_matrix_gates"]:
            lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(["", "## Quantity Matrix"])
    for key, row in summary["quantities"].items():
        methods = ", ".join(f"`{method}`" for method in row["validation_methods"])
        if not methods:
            methods = "none"
        enhancements = ", ".join(
            f"`{enhancement}`" for enhancement in row["quality_enhancements"]
        )
        reps = ", ".join(f"`{path}`" for path in row["representative_paths"])
        lines.append(
            f"- `{key}` ({row['display']}): {row['families']} families, "
            f"{row['cases']} quantity-case hits, "
            f"{row['gold_cases']} gold, {row['silver_cases']} silver"
        )
        lines.append(f"  observable: {row['observable']}")
        lines.append(f"  validation focus: {row['validation_focus']}")
        lines.append(f"  methods: {methods}")
        if enhancements:
            lines.append(f"  quality enhancements: {enhancements}")
        if reps:
            lines.append(f"  representatives: {reps}")

    lines.extend(["", "## Family Routes"])
    shown = summary["families"][: max(0, max_families)]
    for row in shown:
        quantities = ", ".join(f"`{key}`" for key in row["quantity_keys"])
        methods = ", ".join(
            f"`{method['check']}`" for method in row["validation_methods"]
        )
        if not methods:
            methods = "none"
        enhancements = ", ".join(
            f"`{method['check']}`" for method in row.get("quality_enhancements", [])
        )
        lines.append(
            f"- `{row['family']}`: {row['cases']} cases, "
            f"`{row['quality_label']}`, quantities: {quantities}"
        )
        lines.append(f"  validation: `{row['validation_level']}`, methods: {methods}")
        if enhancements:
            lines.append(f"  quality enhancement: {enhancements}")
        if row["representative_paths"]:
            lines.append(
                "  representative: "
                + ", ".join(f"`{path}`" for path in row["representative_paths"][:2])
            )
        if row["recommended_calls"]:
            lines.append(f"  next call: `{row['recommended_calls'][0]}`")
    hidden = summary["selected_family_count"] - len(shown)
    if hidden > 0:
        lines.append(f"- ... {hidden} more families. Narrow with `quantity=`, `family=`, or `label=`.")

    lines.extend(["", "## Public-Safe Notes"])
    lines.extend(f"- {note}" for note in summary["notes"])
    return "\n".join(lines).rstrip()


def format_observable_contract_summary(
    summary: dict[str, Any],
    max_families: int = 32,
) -> str:
    """Format the 500-case observable-contract audit as Markdown."""
    lines = [
        "# Public observable-contract quality audit",
        "",
        (
            f"- enhanced corpus: {summary['enhanced_cases']} cases, "
            f"{summary['enhanced_family_count']} families"
        ),
        (
            f"- configured families: {summary['configured_family_count']}; "
            f"missing families: {summary['missing_family_count']}; "
            f"failed cases: {summary['failed_case_count']}"
        ),
    ]
    filters = []
    if summary["family_filter"]:
        filters.append(f"family contains `{summary['family_filter']}`")
    if summary["label_filter"]:
        filters.append(f"label contains `{summary['label_filter']}`")
    lines.append(f"- filter: {', '.join(filters) if filters else 'none'}")

    if summary.get("observable_contract_gates"):
        lines.extend(["", f"## Observable Contract Gates ({summary['observable_contract_gate_status']})"])
        for gate in summary["observable_contract_gates"]:
            lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(["", "## Families"])
    shown = summary["families"][: max(0, max_families)]
    for row in shown:
        quantities = ", ".join(f"`{key}`" for key in row["quantity_keys"])
        markers = ", ".join(f"`{marker}`" for marker in row["required_markers"])
        reps = ", ".join(f"`{path}`" for path in row["representative_paths"])
        lines.append(
            f"- `{row['family']}`: {row['cases']} cases, "
            f"{row['passed_cases']} passed, `{row['quality_label']}`"
        )
        lines.append(f"  quantities: {quantities}")
        lines.append(f"  required markers: {markers}")
        lines.append(f"  enhancement: `{row['enhancement_check']['check']}`")
        if reps:
            lines.append(f"  representatives: {reps}")
    hidden = summary["enhanced_family_count"] - len(shown)
    if hidden > 0:
        lines.append(f"- ... {hidden} more families. Narrow with `family=`.")

    if summary["failed_cases"]:
        lines.extend(["", "## Failed Cases"])
        for failed in summary["failed_cases"]:
            missing = ", ".join(f"`{marker}`" for marker in failed["missing_markers"])
            lines.append(f"- `{failed['path']}` missing {missing}")

    lines.extend(["", "## Public-Safe Notes"])
    lines.extend(f"- {note}" for note in summary["notes"])
    return "\n".join(lines).rstrip()


def format_quality_summary(summary: dict[str, Any], max_families: int = 30) -> str:
    """Format public quality-label metadata as Markdown."""
    lines = [
        "# Public sample-deck quality labels",
        "",
        (
            f"- corpus: {summary['total_cases']} cases, "
            f"{summary['total_input_files']} input files"
        ),
        (
            f"- selected: {summary['selected_family_count']} families, "
            f"{summary['selected_cases']} cases, "
            f"{summary['selected_input_files']} input files"
        ),
        "",
        f"## Publication Quality Gates ({summary['quality_gate_status']})",
    ]
    for gate in summary["quality_gates"]:
        lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(
        [
            "",
            "## Label Definitions",
        ]
    )
    for label_key in QUALITY_LABEL_DISPLAY_ORDER:
        label = QUALITY_LABEL_DEFINITIONS.get(label_key)
        if not label:
            continue
        counts = summary["label_counts"].get(
            label["label"], {"families": 0, "cases": 0, "input_files": 0}
        )
        lines.append(
            f"- `{label['label']}` ({label['display']}): "
            f"{counts['families']} families, {counts['cases']} cases"
        )
        lines.append(f"  meaning: {label['meaning']}")
        lines.append(f"  recommended use: {label['recommended_use']}")

    lines.extend(["", "## Families"])
    shown = summary["families"][: max(0, max_families)]
    for row in shown:
        lines.append(
            f"- `{row['family']}`: {row['cases']} cases, "
            f"`{row['quality_label']}`, level `{row['validation_level']}`"
        )
        lines.append(f"  title: {row['title']}")
        lines.append(f"  use: {row['recommended_use']}")
    hidden = summary["selected_family_count"] - len(shown)
    if hidden > 0:
        lines.append(f"- ... {hidden} more families. Narrow with `family=` or `label=`.")
    return "\n".join(lines).rstrip()


def format_physical_quantity_summary(
    summary: dict[str, Any],
    max_quantities: int = 16,
    max_families: int = 30,
) -> str:
    """Format public physical-quantity coverage as Markdown."""
    lines = [
        "# Public sample-deck physical quantity coverage",
        "",
        f"- corpus: {summary['total_cases']} cases, {summary['total_families']} families",
        (
            f"- selected: {summary['selected_cases']} cases, "
            f"{summary['selected_family_count']} families"
        ),
    ]
    if summary.get("quantity_filter"):
        lines.append(f"- quantity filter: `{summary['quantity_filter']}`")
    if summary.get("family_filter"):
        lines.append(f"- family filter: `{summary['family_filter']}`")

    if summary.get("physical_gates"):
        lines.extend(["", f"## Physical Quantity Gates ({summary['physical_gate_status']})"])
        for gate in summary["physical_gates"]:
            lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(["", "## Quantity Coverage"])
    shown_quantity_keys = [
        key
        for key in PHYSICAL_QUANTITY_ORDER
        if key in summary["quantity_counts"]
    ][: max(0, max_quantities)]
    for key in shown_quantity_keys:
        row = summary["quantity_counts"][key]
        lines.append(
            f"- `{key}` ({row['display']}): {row['cases']} cases, "
            f"{row['families']} families, {row['gold_cases']} gold, "
            f"{row['silver_cases']} silver"
        )
        lines.append(f"  observable: {row['observable']}")
        lines.append(f"  validation focus: {row['validation_focus']}")
        if row["representative_paths"]:
            lines.append("  representatives: " + ", ".join(f"`{p}`" for p in row["representative_paths"]))
    hidden_quantities = len(summary["quantity_counts"]) - len(shown_quantity_keys)
    if hidden_quantities > 0:
        lines.append(f"- ... {hidden_quantities} more quantities.")

    lines.extend(["", "## Families"])
    shown_families = summary["families"][: max(0, max_families)]
    for row in shown_families:
        quantity_list = ", ".join(f"`{key}`" for key in row["quantity_keys"])
        lines.append(
            f"- `{row['family']}`: {row['cases']} selected cases, "
            f"`{row['quality_label']}`, quantities: {quantity_list}"
        )
        lines.append(f"  title: {row['title']}")
        if row["representative_paths"]:
            lines.append(
                "  representative: "
                + ", ".join(f"`{path}`" for path in row["representative_paths"])
            )
    hidden_families = summary["selected_family_count"] - len(shown_families)
    if hidden_families > 0:
        lines.append(f"- ... {hidden_families} more families. Narrow with `quantity=` or `family=`.")

    lines.extend(["", "## Use Notes"])
    lines.extend(f"- {note}" for note in summary["limitations"])
    return "\n".join(lines).rstrip()


def format_cross_validation_summary(
    summary: dict[str, Any],
    max_families: int = 30,
    max_upgrade_candidates: int = 12,
) -> str:
    """Format public cross-validation coverage as Markdown."""
    lines = [
        "# Public sample-deck cross-validation audit",
        "",
        f"- corpus: {summary['total_cases']} cases, {summary['total_families']} families",
        (
            f"- selected: {summary['selected_cases']} cases, "
            f"{summary['selected_family_count']} families"
        ),
    ]
    if summary.get("family_filter"):
        lines.append(f"- family filter: `{summary['family_filter']}`")
    if summary.get("level_filter"):
        lines.append(f"- level filter: `{summary['level_filter']}`")

    if summary.get("cross_validation_gates"):
        lines.extend(["", f"## Cross-Validation Gates ({summary['cross_validation_gate_status']})"])
        for gate in summary["cross_validation_gates"]:
            lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(["", "## Methods"])
    for check, method in CROSS_VALIDATION_METHODS.items():
        counts = summary["method_counts"].get(check, {"families": 0, "cases": 0})
        lines.append(
            f"- `{check}` ({method['display']}): "
            f"{counts['cases']} cases, {counts['families']} families, "
            f"strength `{method['strength']}`"
        )
        lines.append(f"  meaning: {method['meaning']}")

    gaps = summary["gaps"]
    lines.extend(["", "## Gaps"])
    if gaps["families_without_independent_cross_validation"] == 0:
        lines.append("- No family is missing independent NGSolve cross-validation.")
    else:
        lines.append(
            "- Families missing independent NGSolve cross-validation: "
            + ", ".join(f"`{fam}`" for fam in gaps["gap_families"])
        )
    if gaps["families_without_physical_quantity"] == 0:
        lines.append("- No cross-validated family is missing physical-quantity mapping.")
    else:
        lines.append(
            "- Families missing physical-quantity mapping: "
            + ", ".join(f"`{fam}`" for fam in gaps["gap_families"])
        )

    lines.extend(["", "## Families"])
    shown = summary["families"][: max(0, max_families)]
    for row in shown:
        methods = ", ".join(f"`{m['check']}`" for m in row["cross_validation_methods"])
        quantities = ", ".join(f"`{q}`" for q in row["quantity_keys"])
        lines.append(
            f"- `{row['family']}`: {row['cases']} cases, "
            f"`{row['quality_label']}`, methods: {methods}"
        )
        lines.append(f"  quantities: {quantities}")
        lines.append(f"  scope: {row['validation_scope']}")
    hidden = summary["selected_family_count"] - len(shown)
    if hidden > 0:
        lines.append(f"- ... {hidden} more families. Narrow with `family=` or `level=`.")

    if summary["upgrade_candidates"]:
        lines.extend(["", "## Silver-To-Gold Upgrade Candidates"])
        shown_upgrades = summary["upgrade_candidates"][: max(0, max_upgrade_candidates)]
        for row in shown_upgrades:
            quantities = ", ".join(f"`{q}`" for q in row["quantity_keys"])
            lines.append(
                f"- `{row['family']}`: {row['cases']} cases, "
                f"`{row.get('quality_label', 'silver_proxy_energy')}`, "
                f"current `{row['current_cross_validation']}`, quantities: {quantities}"
            )
            lines.append(f"  possible upgrade: {row['possible_upgrade']}")
        hidden_upgrades = len(summary["upgrade_candidates"]) - len(shown_upgrades)
        if hidden_upgrades > 0:
            lines.append(f"- ... {hidden_upgrades} more silver families.")

    lines.extend(["", "## Use Notes"])
    lines.extend(f"- {note}" for note in summary["limitations"])
    return "\n".join(lines).rstrip()


def format_duplicate_audit(summary: dict[str, Any], max_groups: int = 8) -> str:
    """Format the MCP-oriented duplicate audit as Markdown."""
    lines = [
        "# Public sample-deck duplicate audit",
        "",
        (
            f"- corpus: {summary['total_cases']} cases, "
            f"{summary['total_input_files']} input files"
        ),
        f"- filter: {summary['family_filter'] or 'none'}",
        f"- deletion recommendation: `{summary['delete_recommendation']}`",
        f"- MCP display recommendation: {summary['mcp_display_recommendation']}",
        "",
        f"## Duplicate Gates ({summary['audit_gate_status']})",
    ]
    for gate in summary["gates"]:
        lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(
        [
            "",
            "## Exact Pair Duplicates",
            (
                f"- exact `.mai` + `.meg` duplicate groups: "
                f"{summary['exact_pair_duplicate_groups']}"
            ),
            (
                f"- duplicate cases: {summary['exact_pair_duplicate_cases']}; "
                f"safe-delete candidates: {summary['exact_pair_delete_candidates']}"
            ),
        ]
    )
    if summary["exact_pair_duplicates"]:
        for row in summary["exact_pair_duplicates"][: max(0, max_groups)]:
            lines.append(
                f"- hash `{row['hash']}`: {row['count']} cases, "
                f"{row['family_count']} families"
            )
            for case in row["cases"][:4]:
                lines.append(f"  - `{case['mai_path']}` + `{case['meg_path']}`")
    else:
        lines.append("- No exact pair duplicates were found; no deck deletion is recommended.")

    lines.extend(
        [
            "",
            "## MCP Collapse Candidates",
            (
                f"- `.mai` reuse groups: {summary['mai_reuse_groups']} groups, "
                f"{summary['mai_reuse_files']} files"
            ),
            (
                f"- `.meg` reuse groups: {summary['meg_reuse_groups']} groups, "
                f"{summary['meg_reuse_files']} files"
            ),
            (
                f"- cross-family `.meg` reuse: "
                f"{summary['cross_family_meg_reuse_groups']} groups, "
                f"{summary['cross_family_meg_reuse_files']} files"
            ),
        ]
    )

    def add_reuse_section(title: str, rows: list[dict[str, Any]]) -> None:
        lines.extend(["", f"### {title}"])
        if not rows:
            lines.append("- none")
            return
        for row in rows[: max(0, max_groups)]:
            families = ", ".join(f"`{family}`" for family in row["families"][:4])
            if row["family_count"] > 4:
                families += f", ... {row['family_count'] - 4} more"
            lines.append(
                f"- hash `{row['hash']}`: {row['count']} files, "
                f"{row['family_count']} families ({families})"
            )
            for path in row.get("paths", [])[:4]:
                lines.append(f"  - `{path}`")

    add_reuse_section(".mai control reuse", summary["mai_reuse_examples"])
    add_reuse_section(".meg geometry reuse", summary["meg_reuse_examples"])
    add_reuse_section(
        "cross-family .meg geometry reuse",
        summary["cross_family_meg_reuse_examples"],
    )

    lines.extend(["", "## Public-Safe Notes"])
    lines.extend(f"- {note}" for note in summary["public_use_notes"])
    return "\n".join(lines).rstrip()


def _walk_files(node, prefix: str = "") -> list[tuple[str, Any]]:
    files: list[tuple[str, Any]] = []
    for child in sorted(node.iterdir(), key=lambda p: p.name):
        rel = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            files.extend(_walk_files(child, rel))
        elif child.is_file() and child.name.lower().endswith((".mai", ".meg")):
            files.append((rel.replace("\\", "/"), child))
    return files


def _walk_public_files(node, prefix: str = "") -> list[tuple[str, Any]]:
    files: list[tuple[str, Any]] = []
    for child in sorted(node.iterdir(), key=lambda p: p.name):
        rel = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            files.extend(_walk_public_files(child, rel))
        elif child.is_file():
            files.append((rel.replace("\\", "/"), child))
    return files


@lru_cache(maxsize=1)
def load_sample_decks() -> dict[str, SampleDeck]:
    """Load bundled public sample decks once and cache them."""
    decks: dict[str, SampleDeck] = {}
    root = _sample_root()
    for rel_path, file_ref in _walk_files(root):
        text = file_ref.read_text(encoding="ascii")
        parts = rel_path.split("/")
        family = "/".join(parts[:-2]) if len(parts) >= 3 else ""
        case = parts[-2] if len(parts) >= 2 else ""
        ext = parts[-1].rsplit(".", 1)[-1].lower()
        decks[rel_path] = SampleDeck(
            path=rel_path,
            family=family,
            case=case,
            ext=ext,
            char_count=len(text),
            text=text,
        )
    return decks


def list_sample_decks(family: str | None = None, case: str | None = None, ext: str | None = None) -> list[dict[str, Any]]:
    """List public sample input decks, optionally filtered."""
    decks = load_sample_decks()
    e = ext.lower().lstrip(".") if ext else None
    out = []
    for deck in decks.values():
        if family and family not in deck.family:
            continue
        if case and case != deck.case:
            continue
        if e and e != deck.ext:
            continue
        out.append(
            {
                "path": deck.path,
                "family": deck.family,
                "case": deck.case,
                "ext": deck.ext,
                "char_count": deck.char_count,
            }
        )
    return sorted(out, key=lambda d: d["path"])


def search_sample_decks(query: str, top_k: int = 10, ext: str | None = None) -> list[dict[str, Any]]:
    """Substring-search public sample deck text and paths."""
    top_k = bounded_int(top_k, name="top_k", minimum=1, maximum=100)
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    e = ext.lower().lstrip(".") if ext else None
    hits = []
    for deck in load_sample_decks().values():
        if e and deck.ext != e:
            continue
        meta = _family_meta(deck.family)
        haystack = "\n".join(
            [
                deck.path,
                deck.family,
                meta["title"],
                " ".join(meta["tags"]),
                meta["hint"],
                deck.text,
            ]
        )
        lower = haystack.lower()
        scores = [lower.count(kw.lower()) for kw in keywords]
        if not all(score > 0 for score in scores):
            continue
        first = lower.find(keywords[0].lower())
        start = max(0, first - 80)
        end = min(len(haystack), first + 220)
        snippet = haystack[start:end].replace("\n", " | ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(haystack):
            snippet += "..."
        hits.append(
            {
                "path": deck.path,
                "family": deck.family,
                "case": deck.case,
                "ext": deck.ext,
                "score": sum(scores),
                "snippet": snippet,
            }
        )
    hits.sort(key=lambda h: (-h["score"], h["path"]))
    return hits[:top_k]


def _route_score(goal_l: str, words: set[str], rule: dict[str, Any]) -> int:
    score = 0
    for term in rule["terms"]:
        term_l = term.lower()
        if " " in term_l or "-" in term_l or "/" in term_l:
            if term_l in goal_l:
                score += 4
        elif term_l in words:
            score += 3
        elif len(term_l) > 3 and term_l in goal_l:
            score += 1
    return score


def route_sample_decks(goal: str, limit: int = 5) -> list[dict[str, Any]]:
    """Route a natural-language goal to sample families and follow-up calls."""
    limit = bounded_int(limit, name="limit", minimum=1, maximum=12)
    goal_l = goal.lower()
    words = set(re.findall(r"[a-z0-9]+", goal_l))
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, rule in enumerate(SAMPLE_ROUTE_RULES):
        score = _route_score(goal_l, words, rule)
        if score > 0:
            scored.append((score, index, rule))
    if not scored:
        scored = [(1, index, rule) for index, rule in enumerate(SAMPLE_ROUTE_RULES[-1:])]
    scored.sort(key=lambda item: (-item[0], item[1]))

    routes: list[dict[str, Any]] = []
    max_routes = max(1, min(limit, 12))
    for score, _index, rule in scored[:max_routes]:
        family = rule["family"]
        meta = _family_meta(family)
        validation = get_family_validation(family)
        quality = quality_label_for_family(family)
        examples = representative_paths_for_family(family, limit=3)
        routes.append(
            {
                "score": score,
                "intent": rule["intent"],
                "family": family,
                "title": meta["title"],
                "tags": list(meta["tags"]),
                "validation_level": validation["validation_level"],
                "validation_scope": validation["validation_scope"],
                "quality_label": quality["label"],
                "quality_display": quality["display"],
                "why": rule["why"],
                "query": rule["query"],
                "recipe": rule["recipe"],
                "representative_decks": examples,
                "next_calls": [
                    f'elf_sample_decks_validation(family="{family.rsplit("/", 1)[-1]}")',
                    f'elf_sample_decks_playbook(limit=10, family="{family.rsplit("/", 1)[-1]}")',
                    f'elf_sample_decks_search("{rule["query"]}", ext="mai")',
                    f'elf_recipe_get("{rule["recipe"]}")',
                ],
            }
        )
    return routes


def format_sample_deck_routes(routes: list[dict[str, Any]], goal: str) -> str:
    """Format goal-to-sample routes for MCP clients."""
    if not routes:
        return f"No sample-deck route found for '{goal}'. Try elf_sample_decks_search(goal, ext='mai')."
    lines = [
        f"# Sample-deck route for: {goal}",
        "",
        "Use the first route as the default seed, then inspect the playbook card and open one representative `.mai` deck.",
        "",
    ]
    for i, route in enumerate(routes, 1):
        lines.append(f"## {i}. {route['intent']}  (score={route['score']})")
        lines.append(f"- family: `{route['family']}`")
        lines.append(f"- title: {route['title']}")
        if route.get("validation_level"):
            lines.append(
                f"- validation: `{route['validation_level']}` - "
                f"{route.get('validation_scope', '')}"
            )
        if route.get("quality_label"):
            lines.append(
                f"- quality: `{route['quality_label']}` ({route.get('quality_display', '')})"
            )
        lines.append(f"- why: {route['why']}")
        lines.append(f"- tags: {', '.join(route['tags'][:10])}")
        lines.append("- next calls:")
        lines.extend(f"  - `{call}`" for call in route["next_calls"])
        if route["representative_decks"]:
            lines.append("- representative decks:")
            lines.extend(f"  - `{path}`" for path in route["representative_decks"])
        lines.append("")
    return "\n".join(lines).rstrip()


def build_local_simulation_handoff(
    goal: str,
    family: str | None = None,
    quantity: str | None = None,
    limit: int = 3,
) -> dict[str, Any]:
    """Build a public-safe handoff contract for a user-local ELF runner."""
    max_routes = max(1, min(limit, 8))
    route_goal = " ".join(part for part in (goal, family or "", quantity or "") if part).strip()
    routes = route_sample_decks(route_goal or goal, limit=max_routes * 2)
    family_filter = family.lower() if family else ""
    if family_filter:
        matching = [route for route in routes if family_filter in route["family"].lower()]
        other = [route for route in routes if route not in matching]
        routes = (matching + other)[:max_routes]
    unique_routes = []
    seen_families: set[str] = set()
    for route in routes:
        if route["family"] in seen_families:
            continue
        seen_families.add(route["family"])
        unique_routes.append(route)
    routes = unique_routes[:max_routes]

    selected_routes = []
    for route in routes:
        matrix = build_validation_matrix(family=route["family"], quantity=quantity)
        families = matrix.get("families", [])
        quantity_keys = families[0]["quantity_keys"] if families else []
        representative_decks = route["representative_decks"][:3]
        selected_routes.append(
            {
                "intent": route["intent"],
                "family": route["family"],
                "title": route["title"],
                "quality_label": route["quality_label"],
                "validation_level": route["validation_level"],
                "representative_decks": representative_decks,
                "physical_quantities": quantity_keys,
                "why": route["why"],
                "next_public_calls": route["next_calls"],
            }
        )

    return {
        "schema_version": "elf-local-simulation-handoff/v1",
        "goal": goal,
        "family_filter": family or "",
        "quantity_filter": quantity or "",
        "public_boundary": (
            "This public MCP server selects decks, quantities, validation labels, "
            "and runner/parser contracts. It does not execute ELF/MAGIC, launch "
            "GUI/CLI solvers, or bundle solver outputs."
        ),
        "selected_routes": selected_routes,
        "runner_input_contract": {
            "required": [
                "goal",
                "working_directory",
                "mai_text or mai_path",
                "meg_text or meg_path",
                "run_mode",
                "requested_observables",
            ],
            "recommended": [
                "case_id",
                "source_public_deck_paths",
                "mei_path when mesh regeneration is required",
                "parameter_overrides",
                "timeout_seconds",
                "keep_outputs",
                "field_export_modes such as M3GB or M3SJ when CSV extraction is needed",
            ],
            "run_modes": [
                "copy_public_deck_and_run",
                "mutate_public_deck_then_run",
                "generate_new_deck_from_recipe_then_run",
                "dry_run_validate_inputs_only",
            ],
            "execution_policy": {
                "preferred": "direct_solver_exe_no_gui",
                "avoid": "Launcher.exe GUI route",
                "reason": (
                    "The shell association route can leave a completion dialog. "
                    "Automation should call the solver executable directly and "
                    "wait for process exit."
                ),
                "current_elf600_executables": {
                    "mesh_script": "mesh750.exe (.mei -> .meg, optional)",
                    "magic": "magh1600.exe (.mai -> .mao/.mag/.mat/.mac)",
                    "elfin": "elfh1300.exe (.mai -> .mao and electrostatic outputs)",
                    "beam": "beamh1000.exe (.mai -> beam outputs)",
                    "field_export": "MagFilter2.exe (.mag -> requested CSV extracts)",
                },
                "artifact_roles": {
                    ".mai": "analysis/control input deck",
                    ".meg": "compiled geometry/mesh input",
                    ".mei": "mesh-script input, not a run result",
                    ".mao": "primary execution log",
                    ".mag": "field/result file for post-processing",
                },
            },
        },
        "parser_output_contract": {
            "required": [
                "case_id",
                "status",
                "exit_code",
                "stdout_summary",
                "stderr_summary",
                "generated_files",
                "parsed_observables",
            ],
            "primary_files": {
                "run_log": ".mao",
                "field_result": ".mag",
                "mesh_script_input": ".mei",
            },
            "parsed_observables": [
                "flux_linkage_FLUM",
                "field_probe",
                "force_or_torque",
                "loss_or_eddy_current_proxy",
                "convergence_or_error_messages",
            ],
            "public_rule": (
                "Keep raw solver outputs and numeric product-run references in "
                "the user's local/private workspace unless they are explicitly "
                "scrubbed into public-safe general documentation."
            ),
        },
        "motor_design_loop": [
            "Route the prompt with this handoff tool and choose the strongest matching public deck family.",
            "Open representative `.mai` and `.meg` decks with `elf_sample_decks_get(...)`.",
            "Choose the physical observable before editing parameters: FLUM for flux linkage, co-energy gradients for force/torque, MOMC/FREQ/OHM2 for AC or eddy-current behavior.",
            "Send the runner input contract to a user-local/private runner that has access to the installed ELF/MAGIC product.",
            "Parse the runner output into the parser output contract.",
            "Compare trends against the public validation label and quantity focus; only then propose the next geometry/current/frequency/material mutation.",
        ],
        "recommended_public_calls": [
            f'elf_sample_decks_route("{goal}")',
            'elf_sample_decks_validation_matrix(quantity="motor")',
            'elf_sample_decks_cross_validation(family="motor")',
            'elf_sample_decks_duplicates(family="motor")',
            'elf_plan_workflow("motor flux linkage or torque sweep")',
        ],
    }


def format_local_simulation_handoff(handoff: dict[str, Any]) -> str:
    """Format the public-safe local runner handoff contract as Markdown."""
    lines = [
        "# ELF/MAGIC local simulation handoff",
        "",
        f"- schema: `{handoff['schema_version']}`",
        f"- goal: {handoff['goal']}",
        f"- family filter: {handoff['family_filter'] or 'none'}",
        f"- quantity filter: {handoff['quantity_filter'] or 'none'}",
        f"- boundary: {handoff['public_boundary']}",
        "",
        "## Recommended Deck Routes",
    ]
    if not handoff["selected_routes"]:
        lines.append("- No route was selected. Try `elf_sample_decks_search(goal, ext=\"mai\")`.")
    for index, route in enumerate(handoff["selected_routes"], 1):
        quantities = ", ".join(f"`{item}`" for item in route["physical_quantities"]) or "not mapped"
        reps = ", ".join(f"`{path}`" for path in route["representative_decks"]) or "none"
        lines.append(f"{index}. `{route['family']}` -- {route['title']}")
        lines.append(f"   intent: {route['intent']}")
        lines.append(f"   quality: `{route['quality_label']}`, validation: `{route['validation_level']}`")
        lines.append(f"   quantities: {quantities}")
        lines.append(f"   why: {route['why']}")
        lines.append(f"   representative decks: {reps}")

    runner = handoff["runner_input_contract"]
    lines.extend(["", "## Runner Input Contract"])
    lines.append("- required fields: " + ", ".join(f"`{item}`" for item in runner["required"]))
    lines.append("- recommended fields: " + ", ".join(f"`{item}`" for item in runner["recommended"]))
    lines.append("- run modes: " + ", ".join(f"`{item}`" for item in runner["run_modes"]))
    policy = runner.get("execution_policy", {})
    if policy:
        lines.append(f"- execution policy: `{policy['preferred']}`")
        lines.append(f"- avoid: `{policy['avoid']}` -- {policy['reason']}")
        executables = policy.get("current_elf600_executables", {})
        if executables:
            lines.append("- current ELF600 executables:")
            lines.extend(f"  - `{key}`: {value}" for key, value in executables.items())
        roles = policy.get("artifact_roles", {})
        if roles:
            lines.append("- artifact roles:")
            lines.extend(f"  - `{key}`: {value}" for key, value in roles.items())

    parser = handoff["parser_output_contract"]
    lines.extend(["", "## Parser Output Contract"])
    lines.append("- required fields: " + ", ".join(f"`{item}`" for item in parser["required"]))
    primary_files = parser.get("primary_files", {})
    if primary_files:
        lines.append(
            "- primary files: "
            + ", ".join(f"`{key}` = `{value}`" for key, value in primary_files.items())
        )
    lines.append("- observables: " + ", ".join(f"`{item}`" for item in parser["parsed_observables"]))
    lines.append(f"- public rule: {parser['public_rule']}")

    lines.extend(["", "## Motor Design Loop"])
    for index, step in enumerate(handoff["motor_design_loop"], 1):
        lines.append(f"{index}. {step}")

    lines.extend(["", "## Recommended Public MCP Calls"])
    lines.extend(f"- `{call}`" for call in handoff["recommended_public_calls"])
    return "\n".join(lines).rstrip()


MCP_READINESS_ROUTE_CHECKS: tuple[dict[str, str], ...] = (
    {
        "name": "spm_handoff_routes_to_compact_spm",
        "goal": "SPM motor flux linkage sweep",
        "family": "spm",
        "quantity": "motor",
        "expected_family": "application/motor/spm_surface_pm_10",
    },
    {
        "name": "ipm_route_targets_hairpin_family",
        "goal": "IPM hairpin motor flux linkage",
        "family": "ipm",
        "quantity": "motor",
        "expected_family": "application/motor/emdlab_ipm_hairpin_10",
    },
    {
        "name": "wpt_route_targets_misalignment_family",
        "goal": "WPT misalignment with conducting shield",
        "family": "wpt",
        "quantity": "wpt",
        "expected_family": "application/wpt_misalignment_10",
    },
    {
        "name": "transformer_coupling_route_targets_gold_numeric_family",
        "goal": "transformer coupling turns ratio HBCU FLUM",
        "family": "numeric_transformer_coupling",
        "quantity": "transformer",
        "expected_family": "application/numeric_transformer_coupling_100",
    },
)


@lru_cache(maxsize=1)
def build_mcp_readiness() -> dict[str, Any]:
    """Aggregate MCP-quality gates before public release/tag push."""
    quality = build_quality_summary()
    cross_validation = build_cross_validation_summary()
    duplicate = build_duplicate_audit(max_groups=3)

    route_rows = []
    route_gates = []
    for check in MCP_READINESS_ROUTE_CHECKS:
        handoff = build_local_simulation_handoff(
            check["goal"],
            family=check["family"],
            quantity=check["quantity"],
            limit=3,
        )
        first_family = (
            handoff["selected_routes"][0]["family"]
            if handoff.get("selected_routes")
            else ""
        )
        passed = first_family == check["expected_family"]
        route_rows.append(
            {
                "name": check["name"],
                "goal": check["goal"],
                "expected_family": check["expected_family"],
                "first_family": first_family,
                "status": "PASS" if passed else "FAIL",
                "handoff_schema": handoff["schema_version"],
                "selected_families": [
                    route["family"] for route in handoff.get("selected_routes", [])
                ],
            }
        )
        route_gates.append(
            _public_gate(
                check["name"],
                passed,
                f"first route `{first_family}` expected `{check['expected_family']}`",
            )
        )

    gates = [
        _public_gate(
            "public_quality_gates_pass",
            quality["quality_gate_status"] == "PASS",
            f"quality gate status {quality['quality_gate_status']}",
        ),
        _public_gate(
            "cross_validation_gates_pass",
            cross_validation["cross_validation_gate_status"] == "PASS",
            f"cross-validation gate status {cross_validation['cross_validation_gate_status']}",
        ),
        _public_gate(
            "exact_pair_duplicates_absent",
            duplicate["exact_pair_delete_candidates"] == 0,
            (
                f"{duplicate['exact_pair_duplicate_groups']} duplicate pair groups, "
                f"{duplicate['exact_pair_delete_candidates']} delete candidates"
            ),
        ),
        _public_gate(
            "local_handoff_boundary_declared",
            "does not execute ELF/MAGIC" in build_local_simulation_handoff(
                "SPM motor flux linkage sweep",
                family="spm",
                quantity="motor",
            )["public_boundary"],
            "handoff contract states that public MCP does not execute ELF/MAGIC",
        ),
        *route_gates,
    ]
    readiness = "ready_for_tag_push" if all(gate["status"] == "PASS" for gate in gates) else "blocked"
    return {
        "readiness": readiness,
        "schema_version": "elf-mcp-readiness/v1",
        "total_cases": quality["total_cases"],
        "total_input_files": quality["total_input_files"],
        "quality_gate_status": quality["quality_gate_status"],
        "cross_validation_gate_status": cross_validation["cross_validation_gate_status"],
        "duplicate_delete_candidates": duplicate["exact_pair_delete_candidates"],
        "route_checks": route_rows,
        "gates": gates,
        "recommended_release_steps": [
            "python -m pytest",
            "python -m elf_mcp_server.policy_lint <repo>",
            "python -m elf_mcp_server.server --selftest",
            "python -m build --outdir <temp-dist-dir>",
            "git commit, git tag v1.62.1, git push origin main, git push origin v1.62.1",
        ],
        "public_boundary": (
            "Readiness uses public input decks and metadata only. It does not "
            "execute ELF/MAGIC or expose private validation provenance."
        ),
    }


def format_mcp_readiness(summary: dict[str, Any]) -> str:
    """Format MCP publication readiness as Markdown."""
    lines = [
        "# ELF MCP readiness",
        "",
        f"- schema: `{summary['schema_version']}`",
        f"- readiness: `{summary['readiness']}`",
        (
            f"- corpus: {summary['total_cases']} cases, "
            f"{summary['total_input_files']} input files"
        ),
        f"- public boundary: {summary['public_boundary']}",
        "",
        "## Gates",
    ]
    for gate in summary["gates"]:
        lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(["", "## Route Checks"])
    for row in summary["route_checks"]:
        selected = ", ".join(f"`{family}`" for family in row["selected_families"])
        lines.append(
            f"- {row['status']} `{row['name']}`: `{row['goal']}` -> "
            f"`{row['first_family']}`"
        )
        lines.append(f"  expected: `{row['expected_family']}`")
        lines.append(f"  selected: {selected}")

    lines.extend(["", "## Release Steps"])
    lines.extend(f"- `{step}`" for step in summary["recommended_release_steps"])
    return "\n".join(lines).rstrip()


MOTOR_ARCHETYPE_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "name": "SPM / BLDC / PM pickup",
        "terms": ("spm", "bldc", "pm_square", "pm_cosine", "spmsm"),
        "radia_targets": ("back_emf", "cogging_torque", "ld_lq", "mtpa"),
        "upgrade_focus": "Add stronger flux-linkage, back-EMF, cogging, and Ld/Lq invariants.",
    },
    {
        "name": "IPM",
        "terms": ("ipm", "hairpin"),
        "radia_targets": ("ld_lq", "mtpa", "field_weakening", "demag_margin"),
        "upgrade_focus": "Prioritize saliency, frozen-permeability dq, MTPA, and demag-margin checks.",
    },
    {
        "name": "Induction machine",
        "terms": ("induction", "cage"),
        "radia_targets": ("induction_machine", "deep_bar", "airgap_eddy_machine"),
        "upgrade_focus": "Promote slip-frequency rotor-loss and torque-slip trends to numeric anchors.",
    },
    {
        "name": "SRM / SR motor",
        "terms": ("srm", "sr_motor", "switched_reluctance"),
        "radia_targets": ("reluctance_torque", "power_angle", "saturating_inductance"),
        "upgrade_focus": "Add angle-current torque maps and nonlinear inductance trend anchors.",
    },
    {
        "name": "SynRM / reluctance motor",
        "terms": ("synrm", "reluctance_motor"),
        "radia_targets": ("synchronous_power_angle", "mtpa", "cross_saturation"),
        "upgrade_focus": "Anchor Ld/Lq saliency, reluctance torque, and saturation/cross-saturation trends.",
    },
    {
        "name": "AFPM / axial flux",
        "terms": ("afpm", "axial_flux"),
        "radia_targets": ("build123d_pmsm_field", "airgap_machine_rotation"),
        "upgrade_focus": "Add axial-flux geometry and air-gap field trend checks.",
    },
    {
        "name": "Wound-field / stepper / linear / hysteresis",
        "terms": ("wound_field", "stepper", "linear_pm", "hysteresis"),
        "radia_targets": ("power_angle", "skew_factor", "hysteresis_motor_loss"),
        "upgrade_focus": "Keep as specialist families; add one strong numeric anchor per subtype.",
    },
)


def build_motor_readiness(family: str | None = None) -> dict[str, Any]:
    """Summarize motor-specific corpus coverage and validation gaps."""
    family_filter = (family or "").lower()
    physics = build_physical_quantity_summary(quantity="motor_flux_linkage")
    motor_families = [
        row for row in physics["families"]
        if row["family"].startswith("application/motor/")
        and (not family_filter or family_filter in row["family"].lower())
    ]
    quality_counts: dict[str, int] = {}
    validation_counts: dict[str, int] = {}
    for row in motor_families:
        quality_counts[row["quality_label"]] = quality_counts.get(row["quality_label"], 0) + 1
        validation_counts[row["validation_level"]] = validation_counts.get(row["validation_level"], 0) + 1

    archetypes = []
    covered_arch = 0
    for group in MOTOR_ARCHETYPE_GROUPS:
        terms = tuple(term.lower() for term in group["terms"])
        matches = [
            row for row in motor_families
            if any(term in row["family"].lower() for term in terms)
        ]
        if matches:
            covered_arch += 1
        archetypes.append(
            {
                "name": group["name"],
                "families": [
                    {
                        "family": row["family"],
                        "cases": row["cases"],
                        "quality_label": row["quality_label"],
                        "validation_level": row["validation_level"],
                        "representative_paths": row["representative_paths"],
                    }
                    for row in matches
                ],
                "cases": sum(row["cases"] for row in matches),
                "radia_targets": list(group["radia_targets"]),
                "upgrade_focus": group["upgrade_focus"],
            }
        )

    observable_contract_families = [
        row for row in motor_families
        if row["quality_label"] == ENHANCED_OBSERVABLE_CONTRACT_LABEL["label"]
    ]
    gold_families = [
        row for row in motor_families
        if row["quality_label"] == "gold_numeric_invariant"
    ]
    total_cases = sum(row["cases"] for row in motor_families)
    gates = [
        _public_gate(
            "motor_case_volume_strong",
            total_cases >= 500,
            f"{total_cases} motor cases across {len(motor_families)} families",
        ),
        _public_gate(
            "motor_architecture_breadth_strong",
            covered_arch == len(MOTOR_ARCHETYPE_GROUPS),
            f"{covered_arch}/{len(MOTOR_ARCHETYPE_GROUPS)} archetype groups covered",
        ),
        _public_gate(
            "motor_observable_contracts_present",
            len(observable_contract_families) >= 12,
            f"{len(observable_contract_families)} motor families expose explicit observable contracts",
        ),
    ]
    gold_gate = {
        "gate": "motor_gold_numeric_anchors",
        "status": "PASS" if gold_families else "WARN",
        "detail": (
            f"{len(gold_families)} motor families have gold numeric invariants; "
            "add torque/back-EMF/Ld-Lq/slip-loss anchors before claiming full "
            "motor-solver numerical agreement."
        ),
    }
    motor_readiness = (
        "motor_coverage_ready_validation_upgrade_recommended"
        if all(gate["status"] == "PASS" for gate in gates)
        else "motor_coverage_needs_attention"
    )
    return {
        "schema_version": "elf-motor-readiness/v1",
        "motor_readiness": motor_readiness,
        "family_filter": family or "",
        "motor_families": len(motor_families),
        "motor_cases": total_cases,
        "quality_counts": quality_counts,
        "validation_counts": validation_counts,
        "observable_contract_families": len(observable_contract_families),
        "gold_numeric_motor_families": len(gold_families),
        "archetypes": archetypes,
        "gates": gates + [gold_gate],
        "recommended_next_work": [
            {
                "priority": 1,
                "task": "Promote selected PM/IPM/SPM families from proxy energy to numeric anchors.",
                "radia_mcp_targets": ["back_emf", "cogging_torque", "ld_lq", "mtpa"],
            },
            {
                "priority": 2,
                "task": "Promote induction-machine families with slip-loss and torque-slip trend anchors.",
                "radia_mcp_targets": ["induction_machine", "deep_bar", "airgap_eddy_machine"],
            },
            {
                "priority": 3,
                "task": "Promote SRM/SynRM families with angle-current torque and Ld/Lq saliency anchors.",
                "radia_mcp_targets": ["reluctance_torque", "synchronous_power_angle", "cross_saturation"],
            },
        ],
        "public_boundary": (
            "This audit uses public input-deck metadata only. It does not run "
            "ELF/MAGIC, publish solver outputs, or expose private validation provenance."
        ),
    }


def format_motor_readiness(summary: dict[str, Any], max_families: int = 5) -> str:
    """Format motor-specific readiness and strengthening gaps."""
    lines = [
        "# ELF/MAGIC motor readiness",
        "",
        f"- schema: `{summary['schema_version']}`",
        f"- readiness: `{summary['motor_readiness']}`",
        f"- family filter: {summary['family_filter'] or 'none'}",
        (
            f"- motor corpus: {summary['motor_cases']} cases across "
            f"{summary['motor_families']} families"
        ),
        f"- quality counts: {summary['quality_counts']}",
        f"- validation counts: {summary['validation_counts']}",
        f"- public boundary: {summary['public_boundary']}",
        "",
        "## Gates",
    ]
    for gate in summary["gates"]:
        lines.append(f"- {gate['status']} `{gate['gate']}`: {gate['detail']}")

    lines.extend(["", "## Archetype Coverage"])
    for row in summary["archetypes"]:
        status = "covered" if row["families"] else "gap"
        targets = ", ".join(f"`{item}`" for item in row["radia_targets"])
        lines.append(f"### {row['name']} ({status}, {row['cases']} cases)")
        lines.append(f"- radia-motor targets: {targets}")
        lines.append(f"- upgrade focus: {row['upgrade_focus']}")
        for fam in row["families"][:max_families]:
            reps = ", ".join(f"`{path}`" for path in fam["representative_paths"][:2])
            lines.append(
                f"- `{fam['family']}`: {fam['cases']} cases, "
                f"`{fam['quality_label']}`, `{fam['validation_level']}`"
            )
            if reps:
                lines.append(f"  representative: {reps}")
        if len(row["families"]) > max_families:
            lines.append(f"- ... {len(row['families']) - max_families} more families")

    lines.extend(["", "## Recommended Next Work"])
    for item in summary["recommended_next_work"]:
        targets = ", ".join(f"`{target}`" for target in item["radia_mcp_targets"])
        lines.append(f"{item['priority']}. {item['task']} radia targets: {targets}")
    return "\n".join(lines).rstrip()


def _motor_hybrid_family(goal: str) -> dict[str, Any]:
    g = goal.lower()
    if any(term in g for term in ("outer rotor bldc", "bldc outer", "outer-rotor bldc")):
        return {
            "family": "outer_rotor_bldc",
            "elf_query": "BLDC outer rotor motor",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='outer_rotor_bldc', electrical_angle_deg=...)",
            "age_targets": ["back_emf", "cogging_torque", "pm_airgap_flux"],
            "validation_focus": "outer-rotor radius ownership, magnet polarity, and phase EMF order",
        }
    if any(term in g for term in ("bldc", "six-step", "six step", "brushless dc")):
        return {
            "family": "bldc",
            "elf_query": "BLDC SPM motor flux linkage",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='bldc', electrical_angle_deg=...)",
            "age_targets": ["back_emf", "torque_angle", "harmonic_budget"],
            "validation_focus": "commutation sector, phase order, back-EMF, and torque ripple",
        }
    if any(term in g for term in ("afpm", "axial flux", "axial-flux", "face magnet")):
        return {
            "family": "afpm",
            "elf_query": "axial flux PM face magnet FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='afpm', electrical_angle_deg=...)",
            "age_targets": ["pm_airgap_flux", "back_emf", "skew_factor"],
            "validation_focus": "unfolded axial air-gap coordinates, face-magnet polarity, and skew offset",
        }
    if any(term in g for term in ("dfig", "doubly fed", "wound rotor generator")):
        return {
            "family": "dfig",
            "elf_query": "wound field rotor induction slip FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='dfig', slip_hz=...)",
            "age_targets": ["induction_machine", "slip_loss", "dq_control_layer"],
            "validation_focus": "stator/rotor frequency bases, slip sign, and power-balance residual",
        }
    if any(term in g for term in ("locked rotor", "blocked rotor")):
        return {
            "family": "locked_rotor_induction",
            "elf_query": "induction motor locked rotor OHM2 FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='locked_rotor_induction', slip_hz=...)",
            "age_targets": ["locked_rotor", "slip_loss", "deep_bar"],
            "validation_focus": "slip equals one, cage-loss positivity, and current scaling",
        }
    if any(term in g for term in ("line start", "line-start", "startup", "pull-in")):
        return {
            "family": "line_start_induction",
            "elf_query": "induction motor torque speed startup OHM2 FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='line_start_induction', slip_hz=...)",
            "age_targets": ["torque_speed", "induction_machine", "field_weakening"],
            "validation_focus": "startup slip grid, pull-in angle, cage loss, and final synchronous state",
        }
    if any(term in g for term in ("linear pm", "linear motor", "translator")):
        return {
            "family": "linear_pm",
            "elf_query": "linear PM motor translator offset FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='linear_pm', electrical_angle_deg=...)",
            "age_targets": ["linear_motor_force", "pm_airgap_flux", "force_report"],
            "validation_focus": "force unit dimension, translator offset, and PM track polarity",
        }
    if "stepper" in g:
        return {
            "family": "stepper",
            "elf_query": "stepper motor detent angle FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='stepper', electrical_angle_deg=...)",
            "age_targets": ["cogging_torque", "holding_torque", "pm_airgap_flux"],
            "validation_focus": "detent torque periodicity, phase excitation, and holding-torque sign",
        }
    if any(term in g for term in ("wound field", "wound-field", "rotor field")):
        return {
            "family": "wound_field_sync",
            "elf_query": "wound field synchronous motor rotor field FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='wound_field_sync', electrical_angle_deg=...)",
            "age_targets": ["synchronous_power_angle", "field_current", "flux_linkage"],
            "validation_focus": "rotor field current, stator phase current, and power-angle convention",
        }
    if any(term in g for term in ("induction", "slip", "cage", "deep bar")):
        return {
            "family": "induction",
            "elf_query": "induction motor cage slip OHM2 FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='induction', slip_hz=...)",
            "age_targets": ["induction_machine", "airgap_eddy_machine", "deep_bar"],
            "validation_focus": "rotor loss rises with slip, torque-slip peak, cage screening",
        }
    if any(term in g for term in ("srm", "switched reluctance", "sr motor")):
        return {
            "family": "srm",
            "elf_query": "SRM switched reluctance FLUM HBCU",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='srm', electrical_angle_deg=...)",
            "age_targets": ["reluctance_torque", "saturating_inductance"],
            "validation_focus": "angle-current torque sign, periodicity, nonlinear inductance",
        }
    if any(term in g for term in ("synrm", "reluctance motor")):
        return {
            "family": "synrm",
            "elf_query": "SynRM reluctance motor flux barrier FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='synrm', saliency_ratio_lq_over_ld=...)",
            "age_targets": ["synchronous_power_angle", "mtpa", "cross_saturation"],
            "validation_focus": "Ld/Lq saliency, reluctance torque, cross-saturation",
        }
    if any(term in g for term in ("vipm", "v-ipm", "v shaped", "v-shaped")):
        return {
            "family": "vipm",
            "elf_query": "V IPM barrier magnet saliency FLUM",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='vipm', electrical_angle_deg=...)",
            "age_targets": ["ld_lq", "mtpa", "demag_margin"],
            "validation_focus": "barrier angle, bridge saturation, magnet polarity, and saliency trend",
        }
    if any(term in g for term in ("ipm", "interior", "hairpin")):
        return {
            "family": "ipm",
            "elf_query": "IPM hairpin motor flux linkage",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='ipm', electrical_angle_deg=...)",
            "age_targets": ["ld_lq", "mtpa", "field_weakening", "demag_margin"],
            "validation_focus": "PM flux, saliency, MTPA current angle, demag margin",
        }
    if "hysteresis" in g:
        return {
            "family": "hysteresis",
            "elf_query": "hysteresis motor flux linkage",
            "mmm_call": "elf_motor_mmm_quick_check(motor_type='hysteresis')",
            "age_targets": ["hysteresis_motor_loss", "hysteresis_play"],
            "validation_focus": "separate geometry flux from stateful hysteresis loop loss",
        }
    return {
        "family": "spm",
        "elf_query": "SPM motor flux linkage sweep",
        "mmm_call": "elf_motor_mmm_quick_check(motor_type='spm', electrical_angle_deg=...)",
        "age_targets": ["back_emf", "cogging_torque", "ld_lq", "mtpa"],
        "validation_focus": "PM flux linkage, back-EMF constant, cogging order, Ld/Lq",
    }


def _motor_coupled_targets(family: str) -> list[str]:
    """Public-safe HDiv-MMM / HCurl eddy-bubble targets by motor family."""

    targets = {
        "induction": ["source_field", "reduced_fem_response", "force_or_torque_trend"],
        "locked_rotor_induction": ["source_field", "reduced_fem_response", "force_or_torque_trend"],
        "line_start_induction": ["source_field", "reduced_fem_response", "force_or_torque_trend"],
        "dfig": ["source_field", "reduced_fem_response", "pickup_flux"],
        "srm": ["pickup_flux", "force_or_torque_trend", "coenergy"],
        "synrm": ["pickup_flux", "coenergy", "reduced_fem_response"],
        "bldc": ["demag_field", "pickup_flux", "source_field"],
        "outer_rotor_bldc": ["demag_field", "source_field", "pickup_flux"],
        "afpm": ["demag_field", "pickup_flux", "source_field"],
        "linear_pm": ["source_field", "force_or_torque_trend", "pickup_flux"],
        "stepper": ["demag_field", "force_or_torque_trend", "pickup_flux"],
        "wound_field_sync": ["source_field", "pickup_flux", "coenergy"],
        "ipm": ["demag_field", "pickup_flux", "flux_linkage"],
        "vipm": ["demag_field", "source_field", "pickup_flux"],
        "hysteresis": ["demag_field", "source_field", "coenergy"],
        "spm": ["demag_field", "pickup_flux", "source_field"],
    }
    return targets.get(family, targets["spm"])


def build_motor_hybrid_router(goal: str) -> dict[str, Any]:
    """Route a motor prompt across ELF decks and both radia motor lanes."""
    plan = _motor_hybrid_family(goal)
    routes = route_sample_decks(plan["elf_query"], limit=3)
    readiness = build_motor_readiness(family=plan["family"])
    coupled_targets = _motor_coupled_targets(plan["family"])
    return {
        "schema_version": "elf-motor-hybrid-router/v2",
        "goal": goal,
        "inferred_family": plan["family"],
        "public_boundary": (
            "This router only selects public ELF decks and public radia-motor "
            "validation calls. It does not execute ELF/MAGIC, run NGSolve, or "
            "publish solver outputs."
        ),
        "elf_deck_routes": [
            {
                "family": route["family"],
                "title": route["title"],
                "quality_label": route["quality_label"],
                "validation_level": route["validation_level"],
                "representative_decks": route["representative_decks"],
                "next_public_calls": route["next_calls"],
            }
            for route in routes
        ],
        "mmm_quick_check": {
            "server": "mcp-server-motor",
            "call": plan["mmm_call"],
            "role": "first-order sign/scale sanity check before heavy solves",
        },
        "age_validation": {
            "server": "mcp-server-radia-ngsolve / mcp-server-motor",
            "calls": [f'ngsolve_usage("{target}")' for target in plan["age_targets"]],
            "lane": "ngsolve_age",
            "role": "independent 2D AGE / dq / eddy-current validation anchor",
        },
        "coupled_validation": {
            "server": "mcp-server-motor",
            "calls": [
                'motor_validation_lane_template("hdiv_mmm_hcurl_eddy_bubble")',
                'motor_validation_artifact_gate(..., "hdiv_mmm_hcurl_eddy_bubble")',
            ],
            "lane": "hdiv_mmm_hcurl_eddy_bubble",
            "targets": coupled_targets,
            "role": (
                "HDiv-MMM plus HCurl eddy-bubble lane for source field, demag, "
                "pickup flux, conducting-region response, and force/torque trends"
            ),
        },
        "local_elf_runner": {
            "call": f'elf_local_simulation_handoff("{goal}")',
            "role": "prepare a user-local ELF/MAGIC product run without exposing outputs",
        },
        "validation_focus": plan["validation_focus"],
        "motor_readiness": {
            "readiness": readiness["motor_readiness"],
            "motor_cases": readiness["motor_cases"],
            "motor_families": readiness["motor_families"],
            "gold_numeric_motor_families": readiness["gold_numeric_motor_families"],
        },
        "workflow": [
            "Select an ELF public deck route and inspect the representative .mai/.meg inputs.",
            "Run the radia-motor MMM quick check for sign and scale before spending solver time.",
            "Use ngsolve_age for the independent FE air-gap, torque, dq, and eddy validation target.",
            "Use hdiv_mmm_hcurl_eddy_bubble for source-field, pickup-flux, demag, conducting-region response, and force/torque trends.",
            "Run ELF/MAGIC locally only after the deck and reduced physics checks are coherent.",
            "Promote only reduced, public-safe validation labels; keep raw solver outputs private.",
        ],
    }


def format_motor_hybrid_router(route: dict[str, Any]) -> str:
    """Format the hybrid ELF/radia/MMM motor routing plan."""
    lines = [
        "# ELF/radia motor hybrid router",
        "",
        f"- schema: `{route['schema_version']}`",
        f"- goal: {route['goal']}",
        f"- inferred family: `{route['inferred_family']}`",
        f"- validation focus: {route['validation_focus']}",
        f"- public boundary: {route['public_boundary']}",
        (
            f"- motor readiness: `{route['motor_readiness']['readiness']}` "
            f"({route['motor_readiness']['motor_cases']} cases, "
            f"{route['motor_readiness']['motor_families']} families, "
            f"{route['motor_readiness']['gold_numeric_motor_families']} gold motor anchors)"
        ),
        "",
        "## ELF Deck Route",
    ]
    for index, deck in enumerate(route["elf_deck_routes"], 1):
        reps = ", ".join(f"`{path}`" for path in deck["representative_decks"]) or "none"
        lines.append(f"{index}. `{deck['family']}` -- {deck['title']}")
        lines.append(f"   quality: `{deck['quality_label']}`, validation: `{deck['validation_level']}`")
        lines.append(f"   representative decks: {reps}")

    lines.extend(["", "## MMM Quick Check"])
    mmm = route["mmm_quick_check"]
    lines.append(f"- server: `{mmm['server']}`")
    lines.append(f"- call: `{mmm['call']}`")
    lines.append(f"- role: {mmm['role']}")

    lines.extend(["", "## AGE Validation"])
    age = route["age_validation"]
    lines.append(f"- server: `{age['server']}`")
    lines.append(f"- lane: `{age['lane']}`")
    lines.append(f"- role: {age['role']}")
    lines.extend(f"- `{call}`" for call in age["calls"])

    lines.extend(["", "## HDiv-MMM / HCurl Eddy-Bubble Validation"])
    coupled = route["coupled_validation"]
    lines.append(f"- server: `{coupled['server']}`")
    lines.append(f"- lane: `{coupled['lane']}`")
    lines.append(f"- targets: {', '.join(f'`{target}`' for target in coupled['targets'])}")
    lines.append(f"- role: {coupled['role']}")
    lines.extend(f"- `{call}`" for call in coupled["calls"])

    lines.extend(["", "## Local ELF/MAGIC Runner"])
    lines.append(f"- `{route['local_elf_runner']['call']}`")
    lines.append(f"- role: {route['local_elf_runner']['role']}")

    lines.extend(["", "## Workflow"])
    for i, step in enumerate(route["workflow"], 1):
        lines.append(f"{i}. {step}")
    return "\n".join(lines).rstrip()


def build_motor_mmm_quick_check(
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
    winding_factor: float = 0.933,
    carter_factor: float = 1.1,
    recoil_mu_r: float = 1.05,
    saliency_ratio_lq_over_ld: float = 1.5,
    slip_hz: float = 5.0,
    rotor_time_constant_s: float = 0.05,
    rotor_resistance_ohm: float = 0.2,
) -> dict[str, Any]:
    """Public-safe first-order 2D MMM/BEM-like motor sanity check."""
    t = motor_type.strip().lower()
    if any(term in t for term in ("dfig", "locked_rotor", "line_start", "induction", "cage", "im")):
        family = "induction"
        age_targets = ["induction_machine", "airgap_eddy_machine", "deep_bar", "slip_loss"]
        primary = "slip_loss_proxy"
        applicability = "Slip-frequency trend only; use AGE for field validation."
    elif any(term in t for term in ("bldc", "outer_rotor", "afpm", "axial", "linear_pm", "stepper")):
        family = t
        age_targets = ["back_emf", "cogging_torque", "pm_airgap_flux"]
        primary = "pm_flux_linkage_proxy"
        applicability = "PM flux-linkage sign/scale only; use AGE for topology-specific torque and force."
    elif any(term in t for term in ("srm", "switched", "sr motor")):
        family = "srm"
        age_targets = ["reluctance_torque", "saturating_inductance"]
        primary = "reluctance_torque_proxy"
        applicability = "Saliency sign and angle trend only; use AGE for torque maps."
    elif any(term in t for term in ("synrm", "reluctance")):
        family = "synrm"
        age_targets = ["synchronous_power_angle", "mtpa", "cross_saturation"]
        primary = "reluctance_torque_proxy"
        applicability = "Ld/Lq saliency trend only; use AGE for saturation maps."
    elif "ipm" in t or "interior" in t:
        family = "ipm"
        age_targets = ["ld_lq", "mtpa", "field_weakening", "demag_margin"]
        primary = "pm_plus_reluctance_torque_proxy"
        applicability = "PM flux and saliency sanity only; use AGE for dq maps."
    elif any(term in t for term in ("wound_field", "wound field", "rotor field")):
        family = "wound_field_sync"
        age_targets = ["synchronous_power_angle", "field_current", "flux_linkage"]
        primary = "field_current_flux_proxy"
        applicability = "Rotor-field flux scale only; use AGE for power-angle validation."
    elif "hysteresis" in t:
        family = "hysteresis"
        age_targets = ["hysteresis_motor_loss", "hysteresis_play"]
        primary = "pm_flux_proxy"
        applicability = "Geometry flux sanity only; hysteresis needs a stateful model."
    else:
        family = "spm"
        age_targets = ["back_emf", "cogging_torque", "ld_lq", "mtpa"]
        primary = "pm_flux_linkage_proxy"
        applicability = "PM flux-linkage and EMF scale only; use AGE for slotting/cogging."

    p = max(1, int(pole_pairs))
    radius = max(float(airgap_radius_m), 1e-9)
    stack = max(float(stack_length_m), 1e-9)
    gap = max(float(airgap_m), 1e-9)
    turns = max(float(turns_per_phase), 1e-9)
    theta = math.radians(float(electrical_angle_deg))
    carter_gap = max(float(carter_factor), 1e-9) * gap
    pole_pitch = math.pi * radius / p
    pole_area = max(float(magnet_arc_fraction), 1e-9) * pole_pitch * stack
    magnet_thickness = max(float(magnet_thickness_m), 1e-9)
    bgap = float(magnet_br_t) * magnet_thickness / (
        magnet_thickness + max(float(recoil_mu_r), 1e-9) * carter_gap
    )
    phi_pole = bgap * pole_area
    lambda_pm_peak = turns * max(float(winding_factor), 1e-9) * phi_pole
    lambda_phase = lambda_pm_peak * math.cos(theta)
    emf_constant = p * lambda_pm_peak
    torque_constant = 1.5 * p * lambda_pm_peak
    ld = MU0 * turns * turns * pole_area / carter_gap
    lq = ld * max(float(saliency_ratio_lq_over_ld), 1e-9)
    current = float(phase_current_a)
    iq = current * math.cos(theta)
    id_current = -current * math.sin(theta)
    pm_torque = 1.5 * p * lambda_pm_peak * iq
    reluctance_torque = 1.5 * p * (ld - lq) * id_current * iq
    slip_rad_s = 2.0 * math.pi * abs(float(slip_hz))
    x = slip_rad_s * max(float(rotor_time_constant_s), 1e-12)
    rotor_loss = 3.0 * current * current * max(float(rotor_resistance_ohm), 0.0) * (
        x * x / (1.0 + x * x)
    )
    induction_torque = rotor_loss / max(slip_rad_s, 1e-12)

    warnings = [
        "first-order 2D magnetic-circuit quick check, not a production solver",
        "no saturation iteration, no motion band, no end effects, no skew",
    ]
    if family == "induction":
        warnings.append("cage/end-ring coupling is represented only by a single-pole proxy")
    if family in {"afpm", "outer_rotor_bldc", "linear_pm", "stepper"}:
        warnings.append("topology-specific force or torque requires the AGE validation lane")
    if family == "hysteresis":
        warnings.append("hysteresis loop area and vector history are not modeled")

    return {
        "schema_version": "elf-motor-mmm-quick/v1",
        "family": family,
        "primary_quantity": primary,
        "applicability": applicability,
        "outputs": {
            "carter_gap_m": carter_gap,
            "pole_pitch_m": pole_pitch,
            "pole_area_m2": pole_area,
            "airgap_flux_density_t": bgap,
            "flux_per_pole_wb": phi_pole,
            "lambda_pm_peak_wb": lambda_pm_peak,
            "lambda_phase_wb": lambda_phase,
            "back_emf_v_per_rad_s_mech": emf_constant,
            "torque_constant_nm_per_a_peak": torque_constant,
            "ld_h": ld,
            "lq_h": lq,
            "id_a": id_current,
            "iq_a": iq,
            "pm_torque_nm": pm_torque,
            "reluctance_torque_nm": reluctance_torque,
            "total_dq_torque_proxy_nm": pm_torque + reluctance_torque,
            "rotor_loss_proxy_w": rotor_loss,
            "induction_torque_proxy_nm": induction_torque,
        },
        "recommended_age_targets": age_targets,
        "warnings": warnings,
        "public_boundary": (
            "This is an open, approximate quick check. It does not call "
            "ELF/MAGIC, NGSolve, or any commercial solver, and it does not "
            "encode private benchmark numbers."
        ),
    }


def format_motor_mmm_quick_check(result: dict[str, Any]) -> str:
    """Format the public 2D MMM/BEM-like quick check."""
    out = result["outputs"]
    lines = [
        "# ELF motor 2D MMM/BEM-like quick check",
        "",
        f"- schema: `{result['schema_version']}`",
        f"- inferred family: `{result['family']}`",
        f"- primary quantity: `{result['primary_quantity']}`",
        f"- applicability: {result['applicability']}",
        f"- public boundary: {result['public_boundary']}",
        "",
        "## Key Estimates",
        f"- effective Carter gap: `{out['carter_gap_m']:.6g}` m",
        f"- air-gap flux density: `{out['airgap_flux_density_t']:.6g}` T",
        f"- flux per pole: `{out['flux_per_pole_wb']:.6g}` Wb",
        f"- PM flux-linkage peak: `{out['lambda_pm_peak_wb']:.6g}` Wb-turn",
        f"- phase flux-linkage at angle: `{out['lambda_phase_wb']:.6g}` Wb-turn",
        f"- back-EMF constant: `{out['back_emf_v_per_rad_s_mech']:.6g}` V/(rad/s mechanical)",
        f"- torque constant: `{out['torque_constant_nm_per_a_peak']:.6g}` N.m/A peak",
        f"- Ld/Lq proxy: `{out['ld_h']:.6g}` H / `{out['lq_h']:.6g}` H",
        f"- dq torque proxy: `{out['total_dq_torque_proxy_nm']:.6g}` N.m",
        f"- induction rotor-loss proxy: `{out['rotor_loss_proxy_w']:.6g}` W",
        "",
        "## Route To AGE Validation",
    ]
    lines.extend(f"- `ngsolve_usage(\"{target}\")`" for target in result["recommended_age_targets"])
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {warning}" for warning in result["warnings"])
    return "\n".join(lines).rstrip()


def get_sample_deck(rel_path: str, max_chars: int = 60000) -> dict[str, Any]:
    """Get full text of a public sample .mai/.meg deck."""
    max_chars = bounded_int(max_chars, name="max_chars", minimum=256, maximum=60_000)
    decks = load_sample_decks()
    deck = decks.get(rel_path)
    if deck is None and rel_path.startswith("motor/"):
        deck = decks.get(f"application/{rel_path}")
    if deck is None:
        candidates = [p for p in decks if p.endswith("/" + rel_path) or p == rel_path]
        if len(candidates) == 1:
            deck = decks[candidates[0]]
        else:
            return {
                "path": rel_path,
                "error": f"not found (try one of: {candidates[:5]})" if candidates
                else "not found in public sample decks",
            }
    text = deck.text
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[... truncated, full length: {deck.char_count} chars]"
    return {
        "path": deck.path,
        "family": deck.family,
        "case": deck.case,
        "ext": deck.ext,
        "text": text,
        "char_count": deck.char_count,
        "truncated": truncated,
    }


def _uniq(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _family_meta(family: str) -> dict[str, Any]:
    return FAMILY_META.get(
        family,
        {
            "title": family.rsplit("/", 1)[-1] if family else "sample deck",
            "tags": ("sample-deck",),
            "hint": "Use as a public ELF/MAGIC input deck for a local ELF installation.",
        },
    )


def build_sample_deck_cards(
    limit: int = 100,
    family: str | None = None,
    query: str | None = None,
    team28: bool = False,
) -> list[dict[str, Any]]:
    """Build compact cards over public ELF-runnable sample deck cases."""
    decks = load_sample_decks()
    mai_decks = [d for d in decks.values() if d.ext == "mai"]
    if team28:
        wanted = set(TEAM28_CASES)
        mai_decks = [d for d in mai_decks if (d.family, d.case) in wanted]
    if family:
        mai_decks = [d for d in mai_decks if family in d.family]

    cards = []
    for mai in sorted(mai_decks, key=lambda d: d.path):
        meg_path = mai.path[:-4] + ".meg"
        meg = decks.get(meg_path)
        meta = _family_meta(mai.family)
        haystack = " ".join(
            [
                mai.path,
                mai.family,
                mai.case,
                mai.text,
                meg.text if meg else "",
                " ".join(meta["tags"]),
            ]
        ).lower()
        if query:
            keywords = [k.lower() for k in query.split() if k.strip()]
            if not all(k in haystack for k in keywords):
                continue
        sol_blocks = _uniq(SOL_RE.findall(mai.text))
        pre_keywords = [kw for kw in KEYWORDS if re.search(rf"^\s*{kw}\b", mai.text, re.MULTILINE)]
        elements = _uniq(ELEMENT_RE.findall(meg.text if meg else ""))
        tags = list(meta["tags"])
        hint = meta["hint"]
        validation = get_family_validation(mai.family)
        if team28:
            hint = (
                "Use as a Python-interface seed/inspection deck; team28 is "
                "an orchestration manifest, not a normal ELF GUI/CLI "
                "deck-execution workflow."
            )
        cards.append(
            {
                "family": mai.family,
                "case": mai.case,
                "title": meta["title"],
                "tags": tags,
                "mai_path": mai.path,
                "meg_path": meg_path if meg else "",
                "sol_blocks": sol_blocks,
                "pre_keywords": pre_keywords,
                "elements": elements,
                "validation_level": validation["validation_level"],
                "validation_scope": validation["validation_scope"],
                "char_count": mai.char_count + (meg.char_count if meg else 0),
                "hint": hint,
            }
        )
    if team28:
        order = {key: i for i, key in enumerate(TEAM28_CASES)}
        cards.sort(key=lambda c: order[(c["family"], c["case"])])
    return cards[: max(0, limit)]


def build_team28_cards() -> list[dict[str, Any]]:
    """Build the curated 28-card Python-interface representative set."""
    return build_sample_deck_cards(limit=28, team28=True)


def build_representative_cards(area: str | None = None, limit: int = 36) -> list[dict[str, Any]]:
    """Build the curated public representative set across the 1600-case corpus."""
    area_filter = area.lower() if area else ""
    decks = load_sample_decks()
    cards = []
    for entry in REPRESENTATIVE_CASES:
        if area_filter and area_filter not in entry["area"].lower() and area_filter not in entry["family"].lower():
            continue
        family = entry["family"]
        case = entry["case"]
        mai_path = f"{family}/{case}/{case}.mai"
        meg_path = f"{family}/{case}/{case}.meg"
        mai = decks.get(mai_path)
        meg = decks.get(meg_path)
        if not mai or not meg:
            continue
        meta = _family_meta(family)
        validation = get_family_validation(family)
        quality = quality_label_for_family(family)
        sol_blocks = _uniq(SOL_RE.findall(mai.text))
        pre_keywords = [kw for kw in KEYWORDS if re.search(rf"^\s*{kw}\b", mai.text, re.MULTILINE)]
        elements = _uniq(ELEMENT_RE.findall(meg.text))
        cards.append(
            {
                "area": entry["area"],
                "family": family,
                "case": case,
                "title": meta["title"],
                "reason": entry["reason"],
                "tags": list(meta["tags"]),
                "mai_path": mai_path,
                "meg_path": meg_path,
                "sol_blocks": sol_blocks,
                "pre_keywords": pre_keywords,
                "elements": elements,
                "validation_level": validation["validation_level"],
                "validation_scope": validation["validation_scope"],
                "quality_label": quality["label"],
                "quality_display": quality["display"],
                "quality_meaning": quality["meaning"],
                "recommended_use": quality["recommended_use"],
            }
        )
    return cards[: max(0, limit)]


def representative_paths_for_family(family: str, limit: int = 3) -> list[str]:
    """Return curated representative .mai paths for a family, with fallback."""
    paths = [
        f"{entry['family']}/{entry['case']}/{entry['case']}.mai"
        for entry in REPRESENTATIVE_CASES
        if entry["family"] == family
    ]
    if not paths:
        paths = [d["path"] for d in list_sample_decks(family=family, ext="mai")]
    return paths[: max(0, limit)]


def format_representative_cards(cards: list[dict[str, Any]]) -> str:
    """Format representative sample cards as Markdown."""
    if not cards:
        return "# ELF public representative samples\n\nNo representative samples matched."
    lines = [
        f"# ELF public representative samples ({len(cards)} cards)",
        "",
        "Use these as first-stop examples before browsing the full 1600-case corpus.",
        "",
    ]
    for i, card in enumerate(cards, 1):
        lines.append(f"## {i}. {card['title']} / {card['case']}")
        lines.append(f"- area: `{card['area']}`")
        lines.append(f"- family: `{card['family']}`")
        lines.append(f"- files: `{card['mai_path']}` + `{card['meg_path']}`")
        lines.append(f"- why representative: {card['reason']}")
        lines.append(
            f"- quality: `{card['quality_label']}` ({card['quality_display']}) - "
            f"{card['quality_meaning']}"
        )
        lines.append(f"- validation: `{card['validation_level']}`")
        lines.append(f"- SOL: {', '.join(card['sol_blocks']) if card['sol_blocks'] else '(none)'}")
        lines.append(f"- PRE: {', '.join(card['pre_keywords']) if card['pre_keywords'] else '(none)'}")
        lines.append(f"- elements: {', '.join(card['elements']) if card['elements'] else '(none)'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_public_promotion(audience: str = "collaborator") -> str:
    """Return public-safe promotional copy for the 1600-case corpus."""
    audience_l = audience.lower()
    if audience_l in {"ja", "jp", "japanese", "yano", "collaborator"}:
        return (
            "# ELF-mcp-server public promotion draft\n\n"
            "ELF-mcp-server は、ELF/MAGIC の入力ファイル作成を支援するための "
            "公開 MCP サーバです。公開パッケージには、ELF/MAGIC で読みやすい "
            "`.mai` / `.meg` 入力デッキ 1600 例、合計 3200 入力ファイルを収録し、"
            "モータ、変圧器、MRI、WPT、誘導加熱、加速器用電磁石、アクチュエータ、"
            "磁気ギア、NDT、数値検証アンカーなどを横断的に扱えるようにしました。\n\n"
            "単なる例題集ではなく、MCP クライアントがユーザーのプロンプトから "
            "適切な入力デッキ family を選び、代表例を開き、検証レベルを確認し、"
            "次に見るべき recipe へ進めるための知識ベースとして整備しています。"
            "全 family は公開 manifest で `validation: passed` として管理され、"
            "674 例は `gold_numeric_invariant`、500 例は "
            "`silver_observable_contract`、426 例は `silver_proxy_energy` "
            "という品質ラベルで区別できます。\n\n"
            "公開境界も明確にしています。パッケージに含めるのは、入力デッキ、"
            "公開ドキュメント、recipe、validation metadata だけです。solver 出力、"
            "比較ログ、機械ローカル path、非公開 provenance は含めません。"
            "そのため、研究開発で育てた知見を安全に、かつ実用的に MCP から再利用できます。\n\n"
            "矢野様へ紹介する場合は、"
            "「ELF/MAGIC の使い方を AI agent が迷わず学べるよう、1600 件の公開入力例、"
            "500 件の observable-contract 品質強化、品質ラベル、代表例ルーティングを"
            "備えた MCP サーバとして整備しました」"
            "という一文が一番伝わりやすいです。"
        )
    return (
        "# ELF-mcp-server public promotion draft\n\n"
        "ELF-mcp-server is a public documentation MCP server for authoring "
        "ELF/MAGIC input files. It bundles 1600 public runnable `.mai`/`.meg` "
        "input-deck cases, 3200 input files total, spanning motors, transformers, "
        "MRI, WPT, induction heating, accelerator magnets, actuators, magnetic "
        "gears, NDT probes, and numeric validation anchors.\n\n"
        "The corpus is organized as an agent-facing knowledge base rather than "
        "a raw example dump: MCP clients can route a user prompt to a suitable "
        "sample family, inspect representative decks, check public validation "
        "levels, and continue into workflow recipes. Quality labels distinguish "
        "674 `gold_numeric_invariant` cases, 500 `silver_observable_contract` "
        "cases, and 426 `silver_proxy_energy` cases.\n\n"
        "The public boundary is explicit. The package contains input decks, "
        "public documentation, recipes, and validation metadata only; it does "
        "not bundle solver outputs, comparison logs, machine-local paths, or "
        "private provenance."
    )


def format_sample_deck_cards(cards: list[dict[str, Any]], title: str = "ELF public sample deck playbook") -> str:
    """Format compact sample deck cards as Markdown."""
    if not cards:
        return f"# {title}\n\nNo sample deck cards matched."
    lines = [f"# {title} ({len(cards)} cards)", ""]
    for i, card in enumerate(cards, 1):
        lines.append(f"## {i}. {card['title']} / {card['case']}")
        lines.append(f"- family: `{card['family']}`")
        lines.append(f"- files: `{card['mai_path']}` + `{card['meg_path']}`")
        lines.append(f"- tags: {', '.join(card['tags'])}")
        lines.append(f"- SOL: {', '.join(card['sol_blocks']) if card['sol_blocks'] else '(none)'}")
        lines.append(f"- PRE: {', '.join(card['pre_keywords']) if card['pre_keywords'] else '(none)'}")
        lines.append(f"- elements: {', '.join(card['elements']) if card['elements'] else '(none)'}")
        lines.append(
            f"- validation: `{card['validation_level']}` - {card['validation_scope']}"
        )
        lines.append(f"- hint: {card['hint']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_team28_cards(cards: list[dict[str, Any]]) -> str:
    """Format team28 cards with the required Python-interface manifest note."""
    body = format_sample_deck_cards(cards, title="ELF Python-interface team28")
    note = (
        "# team28 Python-interface seed manifest\n\n"
        "team28 is a Python-interface seed manifest, not a normal ELF GUI/CLI "
        "deck-execution workflow. The public `.mai`/`.meg` paths below are "
        "seed decks and inspection material; runtime orchestration belongs to "
        "the ELF Python interface, outside this documentation MCP server.\n\n"
    )
    return note + body
