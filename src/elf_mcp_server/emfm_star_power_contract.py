"""Public-safe contract for voltage-driven EMFM windings with a STAR group."""

from __future__ import annotations

import cmath
import json
import math
from typing import Any


_OUTPUT_ROLES = {
    ".meg": "geometry",
    ".meo": "mesh_log",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def _phasor(value: Any, name: str) -> complex:
    if isinstance(value, dict) and {"real", "imag"} <= set(value):
        result = complex(float(value["real"]), float(value["imag"]))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        result = complex(float(value[0]), float(value[1]))
    else:
        raise ValueError(f"{name} must be a real/imag mapping or pair")
    if not (math.isfinite(result.real) and math.isfinite(result.imag)):
        raise ValueError(f"{name} must be finite")
    return result


def _int_list(value: Any, name: str) -> list[int]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty list")
    result = [int(item) for item in value]
    if any(item <= 0 for item in result) or len(set(result)) != len(result):
        raise ValueError(f"{name} must contain unique positive material ids")
    return result


def _keyed_float(mapping: Any, mids: list[int], name: str) -> dict[int, float]:
    if not isinstance(mapping, dict):
        raise ValueError(f"{name} must be a mapping")
    result = {}
    for mid in mids:
        try:
            value = float(mapping[str(mid)])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{name} is missing material id {mid}") from exc
        if not math.isfinite(value):
            raise ValueError(f"{name}[{mid}] must be finite")
        result[mid] = value
    return result


def _keyed_phasor(mapping: Any, mids: list[int], name: str) -> dict[int, complex]:
    if not isinstance(mapping, dict):
        raise ValueError(f"{name} must be a mapping")
    result = {}
    for mid in mids:
        if str(mid) not in mapping:
            raise ValueError(f"{name} is missing material id {mid}")
        result[mid] = _phasor(mapping[str(mid)], f"{name}[{mid}]")
    return result


def _spread(values: list[complex]) -> float:
    magnitudes = [abs(value) for value in values]
    scale = max(magnitudes, default=0.0)
    return (max(magnitudes) - min(magnitudes)) / scale if scale > 0.0 else math.inf


def _zero_residual(values: list[complex]) -> float:
    scale = sum(abs(value) for value in values)
    return abs(sum(values)) / scale if scale > 0.0 else math.inf


def _phase_error(values: list[complex], expected_deg: float = -120.0) -> float:
    errors = []
    for left, right in zip(values, values[1:]):
        if abs(left) == 0.0 or abs(right) == 0.0:
            return math.inf
        actual = math.degrees(cmath.phase(right / left))
        errors.append(abs((actual - expected_deg + 180.0) % 360.0 - 180.0))
    return max(errors, default=math.inf)


def emfm_star_power_contract_gate(summary_json: str) -> dict[str, Any]:
    """Validate immutable execution metadata and EMFM/STAR phasor identities."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    source = summary.get("source_contract")
    result = summary.get("result_contract")
    if not isinstance(source, dict) or not isinstance(result, dict):
        raise ValueError("source_contract and result_contract must be objects")

    emfm_mids = _int_list(source.get("emfm_mids"), "emfm_mids")
    star_mids = _int_list(source.get("star_mids"), "star_mids")
    if len(star_mids) != 3:
        raise ValueError("star_mids must contain exactly three material ids")
    passive_mids = [mid for mid in emfm_mids if mid not in star_mids]
    if not passive_mids:
        raise ValueError("at least one passive EMFM winding is required")

    voltages = _keyed_phasor(source.get("voltage_phasors_by_mid"), emfm_mids, "voltages")
    currents = _keyed_phasor(result.get("current_phasors_by_mid"), emfm_mids, "currents")
    resistances = _keyed_float(source.get("resistance_ohm_by_mid"), emfm_mids, "resistances")
    turns = _keyed_float(source.get("turns_by_mid"), emfm_mids, "turns")
    if any(value <= 0.0 for value in resistances.values()):
        raise ValueError("all resistance values must be positive")
    if any(value <= 0.0 for value in turns.values()):
        raise ValueError("all turn counts must be positive")
    phasor_convention = str(source.get("phasor_convention") or "").strip()
    power_factor = 0.5 if phasor_convention == "complex_peak_amplitude" else 1.0

    star_voltages = [voltages[mid] for mid in star_mids]
    star_currents = [currents[mid] for mid in star_mids]
    input_currents = [-value for value in star_currents]
    input_power = power_factor * sum(
        voltage * current.conjugate()
        for voltage, current in zip(star_voltages, input_currents)
    )
    copper_loss = power_factor * sum(
        resistances[mid] * abs(currents[mid]) ** 2 for mid in emfm_mids
    )
    power_scale = max(abs(input_power.real), abs(copper_loss), 1.0e-300)
    power_residual = abs(input_power.real - copper_loss) / power_scale
    voltage_spread = _spread(star_voltages)
    current_spread = _spread(star_currents)
    voltage_zero = _zero_residual(star_voltages)
    current_zero = _zero_residual(star_currents)
    voltage_phase_error = _phase_error(star_voltages)
    current_phase_error = _phase_error(star_currents)
    neutral_voltage = _phasor(result.get("neutral_voltage"), "neutral_voltage")
    neutral_ratio = abs(neutral_voltage) / max(
        sum(abs(value) for value in star_voltages) / 3.0, 1.0e-300
    )

    checks = {
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "source_mai_mei_digests_recorded": summary.get("source_file_count") == 2
        and summary.get("source_digest_count") == 2,
        "source_copy_preserved": summary.get("source_copy_preserved") is True,
        "solver_and_mesh_exit_zero": summary.get("mesh_exit_code") == 0
        and summary.get("solver_exit_code") == 0,
        "solver_and_mesh_versions_recorded": bool(str(summary.get("solver_version") or "").strip())
        and bool(str(summary.get("mesh_version") or "").strip()),
        "run_date_recorded": bool(str(summary.get("run_date_utc") or "").strip()),
        "momc_frequency_contract": source.get("analysis") == "MOMC"
        and float(source.get("frequency_hz", 0.0)) > 0.0,
        "complex_peak_phasor_convention_recorded": phasor_convention
        == "complex_peak_amplitude",
        "emfm_and_star_membership_consistent": set(star_mids) < set(emfm_mids),
        "star_windings_are_voltage_driven": set(star_mids)
        <= set(_int_list(source.get("voltage_drive_mids"), "voltage_drive_mids")),
        "passive_windings_are_zero_volt": all(abs(voltages[mid]) <= 1.0e-12 for mid in passive_mids),
        "star_voltage_triplet_balanced": voltage_spread <= 1.0e-5,
        "star_voltage_phase_sequence": voltage_phase_error <= 1.0e-2,
        "star_voltage_zero_sequence_small": voltage_zero <= 1.0e-5,
        "star_current_triplet_balanced": current_spread <= 5.0e-3,
        "star_current_phase_sequence": current_phase_error <= 1.0,
        "star_current_kcl_closes": current_zero <= 1.0e-5,
        "emfm_current_orientation_recorded": result.get("current_orientation")
        == "positive_out_of_voltage_source",
        "neutral_voltage_finite": math.isfinite(neutral_ratio),
        "active_input_power_positive": input_power.real > 0.0,
        "copper_loss_positive": copper_loss > 0.0,
        "active_power_closes_to_all_emfm_copper_loss": power_residual <= 1.0e-3,
        "mao_real_imag_sections_paired": result.get("mao_real_imag_sections") == 2,
        "mao_complete_without_errors": result.get("mao_complete") is True
        and result.get("mao_error_count") == 0,
        "output_roles_complete_and_fresh": result.get("output_roles") == _OUTPUT_ROLES
        and result.get("all_outputs_fresh") is True,
        "solver_neutral_gate_closed": result.get("solver_neutral_gate_status") == "ok",
    }
    return {
        "schema": "elf-emfm-star-power-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "metrics": {
            "star_voltage_magnitude_relative_spread": voltage_spread,
            "star_current_magnitude_relative_spread": current_spread,
            "star_voltage_zero_sequence_residual": voltage_zero,
            "star_current_zero_sequence_residual": current_zero,
            "max_star_voltage_phase_step_error_deg": voltage_phase_error,
            "max_star_current_phase_step_error_deg": current_phase_error,
            "neutral_voltage_to_phase_voltage_ratio": neutral_ratio,
            "active_input_power_w": input_power.real,
            "reactive_input_power_var": input_power.imag,
            "all_emfm_copper_loss_w": copper_loss,
            "active_power_relative_residual": power_residual,
            "source_to_passive_turn_ratio": (
                sum(turns[mid] for mid in star_mids) / len(star_mids)
            )
            / (sum(turns[mid] for mid in passive_mids) / len(passive_mids)),
            "phasor_power_factor": power_factor,
        },
        "notes": [
            "EMFM output current is normalized positive out of the voltage source before terminal power is formed.",
            "STAR enforces current sum only for the listed material ids; unconnected passive windings are not forced to zero sequence.",
            "Pair the REAL and IMAGINARY .mao sections by EMFM material id before applying phasor identities.",
        ],
    }
