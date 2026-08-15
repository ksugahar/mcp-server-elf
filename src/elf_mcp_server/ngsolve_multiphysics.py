"""Public NGSolve multiphysics validation contracts for motor workflows.

This module is intentionally product-solver-free. It turns public motor design
inputs and parsed local RunResult observables into NGSolve validation jobs and
small runnable NGSolve scripts for thermal, NVH, and mechanical stress checks.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence
import json


LANES = ("thermal", "nvh", "stress")

LANE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "thermal": {
        "ngsolve_space": "H1 scalar heat equation",
        "required_inputs": (
            "total_loss_w",
            "thermal_conductivity_w_mk",
            "cooling_h_w_m2k",
            "ambient_temp_c",
            "outer_diameter_m",
            "stack_length_m",
        ),
        "runresult_observables": (
            "loss_proxy",
            "copper_loss_w",
            "iron_loss_w",
            "magnet_loss_w",
            "duty_cycle",
            "cooling_mode",
        ),
        "acceptance": (
            "peak_temperature_c is below material and insulation limits",
            "temperature_rise_c trend follows loss and cooling changes",
            "hot assumptions are recorded before prototype procurement",
        ),
    },
    "nvh": {
        "ngsolve_space": "H1 structural/acoustic modal proxy",
        "required_inputs": (
            "base_speed_rpm",
            "force_order",
            "torque_ripple_percent",
            "cogging_torque_nm",
            "outer_diameter_m",
        ),
        "runresult_observables": (
            "torque_ripple",
            "cogging_torque",
            "force_order_proxy",
            "airgap_harmonics",
        ),
        "acceptance": (
            "dominant electromagnetic order is separated from modal peaks",
            "torque ripple and cogging are below the target label",
            "risky orders are returned to the electromagnetic sweep matrix",
        ),
    },
    "stress": {
        "ngsolve_space": "VectorH1 linear elasticity",
        "required_inputs": (
            "max_speed_rpm",
            "rotor_radius_m",
            "density_kg_m3",
            "youngs_modulus_pa",
            "poisson_ratio",
            "yield_strength_pa",
            "outer_diameter_m",
        ),
        "runresult_observables": (
            "max_speed_rpm",
            "bridge_stress_proxy",
            "magnet_retention_proxy",
            "rotor_radius",
        ),
        "acceptance": (
            "yield_margin_proxy stays above the selected design margin",
            "rotor bridge, sleeve, magnet retention, shaft, and hub risks are flagged",
            "stress sign-off remains a downstream engineering responsibility",
        ),
    },
}


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _select_lanes(lanes: str | Sequence[str]) -> list[str]:
    if isinstance(lanes, str):
        raw = [part.strip().lower() for part in lanes.replace(";", ",").split(",")]
    else:
        raw = [str(part).strip().lower() for part in lanes]
    if not raw or "all" in raw:
        return list(LANES)
    selected = []
    for lane in raw:
        if lane and lane not in selected:
            selected.append(lane)
    return selected


def build_ngsolve_validation_spec(
    goal: str,
    lanes: str | Sequence[str] = "all",
    motor_type: str = "spm",
    rotor_topology: str = "outer_rotor",
    total_loss_w: float = 25.0,
    base_speed_rpm: float = 3500.0,
    max_speed_rpm: float = 12000.0,
    outer_diameter_mm: float = 80.0,
    stack_length_mm: float = 20.0,
    cooling_h_w_m2k: float = 35.0,
    thermal_conductivity_w_mk: float = 12.0,
    ambient_temp_c: float = 25.0,
    torque_ripple_percent: float = 5.0,
    cogging_torque_nm: float = 0.02,
    force_order: float = 12.0,
    density_kg_m3: float = 7800.0,
    youngs_modulus_gpa: float = 200.0,
    poisson_ratio: float = 0.30,
    yield_strength_mpa: float = 450.0,
    maxh_mm: float = 8.0,
    order: int = 1,
) -> dict[str, Any]:
    """Build a public NGSolve validation spec with SI-normalized values."""
    diameter_m = max(_to_float(outer_diameter_mm) * 1.0e-3, 0.0)
    stack_m = max(_to_float(stack_length_mm) * 1.0e-3, 0.0)
    selected = _select_lanes(lanes)
    return {
        "schema_version": "elf-ngsolve-multiphysics-spec/v1",
        "goal": goal,
        "motor_type": (motor_type or "spm").strip().lower(),
        "rotor_topology": (rotor_topology or "outer_rotor").strip().lower(),
        "lanes": selected,
        "inputs": {
            "total_loss_w": _to_float(total_loss_w),
            "base_speed_rpm": _to_float(base_speed_rpm),
            "max_speed_rpm": _to_float(max_speed_rpm),
            "outer_diameter_m": diameter_m,
            "stack_length_m": stack_m,
            "cooling_h_w_m2k": _to_float(cooling_h_w_m2k),
            "thermal_conductivity_w_mk": _to_float(thermal_conductivity_w_mk),
            "ambient_temp_c": _to_float(ambient_temp_c),
            "torque_ripple_percent": _to_float(torque_ripple_percent),
            "cogging_torque_nm": _to_float(cogging_torque_nm),
            "force_order": _to_float(force_order),
            "rotor_radius_m": 0.5 * diameter_m,
            "density_kg_m3": _to_float(density_kg_m3),
            "youngs_modulus_pa": _to_float(youngs_modulus_gpa) * 1.0e9,
            "poisson_ratio": _to_float(poisson_ratio),
            "yield_strength_pa": _to_float(yield_strength_mpa) * 1.0e6,
            "maxh_m": max(_to_float(maxh_mm) * 1.0e-3, 1.0e-4),
            "order": max(int(order), 1),
        },
        "public_boundary": (
            "Open NGSolve validation only. Product execution and raw product "
            "outputs remain user-local/private."
        ),
    }


def validate_ngsolve_validation_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Lint an NGSolve validation spec before script generation."""
    lanes = _select_lanes(spec.get("lanes", "all"))
    inputs = spec.get("inputs", {})
    if not isinstance(inputs, Mapping):
        inputs = {}
    issues: list[dict[str, str]] = []
    for lane in lanes:
        if lane not in LANES:
            issues.append(
                {"severity": "ERROR", "field": "lanes", "message": f"unknown lane {lane!r}"}
            )
            continue
        for field in LANE_REQUIREMENTS[lane]["required_inputs"]:
            if field == "ambient_temp_c":
                continue
            value = _to_float(inputs.get(field), 0.0)
            if value <= 0.0:
                issues.append(
                    {
                        "severity": "ERROR",
                        "field": field,
                        "message": f"{lane} validation requires a positive {field}",
                    }
                )
    poisson = _to_float(inputs.get("poisson_ratio"), 0.0)
    if "stress" in lanes and not (-0.95 < poisson < 0.49):
        issues.append(
            {
                "severity": "ERROR",
                "field": "poisson_ratio",
                "message": "stress validation expects -0.95 < poisson_ratio < 0.49",
            }
        )
    if "nvh" in lanes and _to_float(inputs.get("torque_ripple_percent"), -1.0) < 0.0:
        issues.append(
            {
                "severity": "ERROR",
                "field": "torque_ripple_percent",
                "message": "NVH validation expects non-negative torque ripple",
            }
        )
    return {
        "schema_version": "elf-ngsolve-multiphysics-lint/v1",
        "status": "FAIL" if any(item["severity"] == "ERROR" for item in issues) else "PASS",
        "lanes": lanes,
        "issues": issues,
        "required_observables": {
            lane: list(LANE_REQUIREMENTS[lane]["runresult_observables"])
            for lane in lanes
            if lane in LANES
        },
    }


def build_ngsolve_validation_plan(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Build lane jobs and script-generation calls for NGSolve validation."""
    lint = validate_ngsolve_validation_spec(spec)
    lanes = lint["lanes"]
    jobs = []
    for lane in lanes:
        if lane not in LANE_REQUIREMENTS:
            continue
        req = LANE_REQUIREMENTS[lane]
        jobs.append(
            {
                "lane": lane,
                "ngsolve_space": req["ngsolve_space"],
                "required_inputs": list(req["required_inputs"]),
                "runresult_observables": list(req["runresult_observables"]),
                "acceptance": list(req["acceptance"]),
                "script_tool_call": f'elf_python_ngsolve_validation_script(lane="{lane}")',
            }
        )
    return {
        "schema_version": "elf-ngsolve-multiphysics-plan/v1",
        "goal": spec.get("goal", ""),
        "status": lint["status"],
        "lanes": lanes,
        "lint": lint,
        "jobs": jobs,
        "implementation": (
            "Use the generated NGSolve Python script as the open validation "
            "runner after local electromagnetic observables are parsed."
        ),
        "public_boundary": spec.get("public_boundary", ""),
    }


def _script_config(spec: Mapping[str, Any], lane: str) -> dict[str, Any]:
    lanes = _select_lanes(spec.get("lanes", "all"))
    if lane != "all":
        lanes = _select_lanes(lane)
    inputs = dict(spec.get("inputs", {}))
    return {
        "schema_version": "elf-ngsolve-runtime-config/v1",
        "goal": spec.get("goal", ""),
        "lanes": lanes,
        **inputs,
    }


_SCRIPT_BODY = r'''
import json
from math import pi, sqrt

from ngsolve import *
from netgen.geom2d import SplineGeometry


def _safe(value: float, eps: float = 1.0e-18) -> float:
    return value if abs(value) > eps else eps


def _make_rect_mesh(config):
    width = max(float(config["outer_diameter_m"]), 1.0e-4)
    height = width
    maxh = max(float(config["maxh_m"]), width / 40.0)
    geom = SplineGeometry()
    geom.AddRectangle((0.0, 0.0), (width, height), bcs=("left", "right", "bottom", "top"))
    return Mesh(geom.GenerateMesh(maxh=maxh))


def run_thermal(config):
    mesh = _make_rect_mesh(config)
    order = int(config.get("order", 1))
    fes = H1(mesh, order=order)
    u, v = fes.TnT()
    conductivity = float(config["thermal_conductivity_w_mk"])
    cooling = float(config["cooling_h_w_m2k"])
    ambient = float(config["ambient_temp_c"])
    area = float(config["outer_diameter_m"]) ** 2
    volume = area * float(config["stack_length_m"])
    q_vol = float(config["total_loss_w"]) / _safe(volume)
    a = BilinearForm(fes)
    a += conductivity * grad(u) * grad(v) * dx + cooling * u * v * ds
    f = LinearForm(fes)
    f += q_vol * v * dx + cooling * ambient * v * ds
    a.Assemble()
    f.Assemble()
    gfu = GridFunction(fes)
    gfu.vec.data = a.mat.Inverse(fes.FreeDofs()) * f.vec
    mesh_area = Integrate(1, mesh)
    mean_temp = float(Integrate(gfu, mesh) / _safe(mesh_area))
    peak_temp = float(max(gfu.vec))
    return {
        "lane": "thermal",
        "elements": mesh.ne,
        "mean_temperature_c": mean_temp,
        "peak_temperature_c": peak_temp,
        "temperature_rise_c": peak_temp - ambient,
        "q_vol_w_m3": q_vol,
    }


def run_stress(config):
    mesh = _make_rect_mesh(config)
    order = int(config.get("order", 1))
    fes = VectorH1(mesh, order=order, dirichlet="left")
    u, v = fes.TnT()
    young = float(config["youngs_modulus_pa"])
    nu = float(config["poisson_ratio"])
    rho = float(config["density_kg_m3"])
    rpm = float(config["max_speed_rpm"])
    radius = float(config["rotor_radius_m"])
    omega = 2.0 * pi * rpm / 60.0
    mu = young / (2.0 * (1.0 + nu))
    lam = young * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))

    def eps(w):
        return Sym(Grad(w))

    def sigma(w):
        return 2.0 * mu * eps(w) + lam * Trace(eps(w)) * Id(2)

    body = CoefficientFunction((rho * omega * omega * radius, 0.0))
    a = BilinearForm(fes)
    a += InnerProduct(sigma(u), eps(v)) * dx
    f = LinearForm(fes)
    f += InnerProduct(body, v) * dx
    a.Assemble()
    f.Assemble()
    gfu = GridFunction(fes)
    gfu.vec.data = a.mat.Inverse(fes.FreeDofs()) * f.vec
    mesh_area = Integrate(1, mesh)
    stress_proxy = sqrt(InnerProduct(sigma(gfu), sigma(gfu)))
    mean_stress = float(Integrate(stress_proxy, mesh) / _safe(mesh_area))
    mean_disp = float(Integrate(Norm(gfu), mesh) / _safe(mesh_area))
    yield_strength = float(config["yield_strength_pa"])
    return {
        "lane": "stress",
        "elements": mesh.ne,
        "mean_displacement_m": mean_disp,
        "mean_stress_proxy_pa": mean_stress,
        "yield_margin_proxy": yield_strength / _safe(mean_stress),
        "omega_rad_s": omega,
    }


def run_nvh(config):
    mesh = _make_rect_mesh(config)
    order = max(int(config.get("order", 1)), 2)
    fes = H1(mesh, order=order, dirichlet="left|right|bottom|top")
    u, v = fes.TnT()
    stiffness_scale = float(config.get("structural_stiffness_scale", 1.0))
    mass_scale = float(config.get("structural_mass_scale", 1.0))
    a = BilinearForm(fes)
    a += stiffness_scale * grad(u) * grad(v) * dx
    m = BilinearForm(fes)
    m += mass_scale * u * v * dx
    a.Assemble()
    m.Assemble()
    gfu = GridFunction(fes)
    vecs = [gfu.vec.CreateVector() for _ in range(3)]
    for vec in vecs:
        vec.SetRandom()
    order_frequency = float(config["base_speed_rpm"]) * float(config["force_order"]) / 60.0
    shift = max((2.0 * pi * max(order_frequency, 1.0)) ** 2, 1.0)
    eigenvalues = ArnoldiSolver(a.mat, m.mat, fes.FreeDofs(), vecs, shift=shift)
    modal_freqs = [sqrt(abs(ev.real)) / (2.0 * pi) for ev in eigenvalues]
    nearest = min(modal_freqs, key=lambda item: abs(item - order_frequency)) if modal_freqs else 0.0
    separation = abs(nearest - order_frequency) / _safe(order_frequency)
    return {
        "lane": "nvh",
        "elements": mesh.ne,
        "order_frequency_hz": order_frequency,
        "modal_frequencies_hz": modal_freqs,
        "nearest_modal_frequency_hz": nearest,
        "relative_order_separation": separation,
        "torque_ripple_percent": float(config["torque_ripple_percent"]),
        "cogging_torque_nm": float(config["cogging_torque_nm"]),
    }


def main():
    runners = {
        "thermal": run_thermal,
        "nvh": run_nvh,
        "stress": run_stress,
    }
    results = []
    for lane in CONFIG["lanes"]:
        results.append(runners[lane](CONFIG))
    print(json.dumps({
        "schema_version": "elf-ngsolve-runtime-result/v1",
        "goal": CONFIG.get("goal", ""),
        "results": results,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
'''


def build_ngsolve_validation_script(
    spec: Mapping[str, Any],
    lane: str = "all",
) -> dict[str, Any]:
    """Return a runnable NGSolve Python validation script."""
    config = _script_config(spec, lane)
    invalid = [item for item in config["lanes"] if item not in LANES]
    if invalid:
        raise ValueError(f"unknown NGSolve validation lane(s): {invalid!r}")
    lint = validate_ngsolve_validation_spec(
        {"lanes": config["lanes"], "inputs": config}
    )
    if lint["status"] != "PASS":
        messages = "; ".join(
            f"{item['field']}: {item['message']}" for item in lint["issues"]
        )
        raise ValueError(f"NGSolve validation spec failed: {messages}")
    script = (
        "# Generated by ELF-mcp-server public NGSolve validation facade.\n"
        "# Save and run with a Python environment that has ngsolve/netgen installed.\n"
        "CONFIG = "
        + json.dumps(config, indent=2, sort_keys=True)
        + "\n"
        + _SCRIPT_BODY
    )
    return {
        "schema_version": "elf-ngsolve-validation-script/v1",
        "lane": lane,
        "lanes": config["lanes"],
        "lint": lint,
        "script": script,
        "expected_stdout": "JSON object with schema_version='elf-ngsolve-runtime-result/v1'",
        "public_boundary": (
            "The script uses NGSolve/Netgen only and does not call product "
            "software or require product outputs beyond parsed numeric inputs."
        ),
    }


def format_ngsolve_validation_plan(plan: Mapping[str, Any]) -> str:
    """Format an NGSolve validation plan as Markdown."""
    lint = plan["lint"]
    lines = [
        "# ELF Python NGSolve Multiphysics Validation Plan",
        "",
        f"- schema: `{plan['schema_version']}`",
        f"- goal: {plan.get('goal', '')}",
        f"- status: `{plan['status']}`",
        "- lanes: " + ", ".join(f"`{lane}`" for lane in plan["lanes"]),
        f"- implementation: {plan['implementation']}",
        f"- boundary: {plan['public_boundary']}",
        "",
        "## Lint",
    ]
    if lint["issues"]:
        for issue in lint["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['field']}`: {issue['message']}")
    else:
        lines.append("- PASS: inputs are sufficient for script generation")
    lines.extend(["", "## Jobs"])
    for job in plan["jobs"]:
        lines.append(f"### {job['lane']}")
        lines.append(f"- NGSolve space: {job['ngsolve_space']}")
        lines.append(
            "- required inputs: " + ", ".join(f"`{item}`" for item in job["required_inputs"])
        )
        lines.append(
            "- parsed observables: "
            + ", ".join(f"`{item}`" for item in job["runresult_observables"])
        )
        lines.append(f"- script call: `{job['script_tool_call']}`")
        lines.append("- acceptance:")
        lines.extend(f"  - {item}" for item in job["acceptance"])
    return "\n".join(lines).rstrip()


def format_ngsolve_validation_script(script_bundle: Mapping[str, Any]) -> str:
    """Format an NGSolve validation script as Markdown with a code fence."""
    lines = [
        "# ELF Python NGSolve Validation Script",
        "",
        f"- schema: `{script_bundle['schema_version']}`",
        f"- lane request: `{script_bundle['lane']}`",
        "- generated lanes: " + ", ".join(f"`{lane}`" for lane in script_bundle["lanes"]),
        f"- expected stdout: {script_bundle['expected_stdout']}",
        f"- boundary: {script_bundle['public_boundary']}",
        "",
        "```python",
        script_bundle["script"].rstrip(),
        "```",
    ]
    return "\n".join(lines).rstrip()
