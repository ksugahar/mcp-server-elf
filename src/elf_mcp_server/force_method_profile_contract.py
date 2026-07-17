"""Metadata-only contract for replayed magnetic-force method profiles."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime


_CASE_ROLES = {
    "element_force": "MR02_01",
    "maxwell_stress": "MR02_02",
    "combined_methods": "MR02_03",
}
_EXPECTED_SOURCE_NAMES = {
    f"{case_id}{suffix}"
    for case_id in _CASE_ROLES.values()
    for suffix in (".mai", ".mei")
}
_OUTPUT_ROLES = {
    ".meg": "geometry_mesh",
    ".mao": "run_log",
    ".mag": "field_result",
    ".mat": "matrix_state",
    ".mac": "mark_state",
}


def _output_artifacts_complete(run: dict) -> bool:
    artifacts = run.get("output_artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(_OUTPUT_ROLES):
        return False
    for suffix, expected_role in _OUTPUT_ROLES.items():
        row = artifacts.get(suffix)
        if not isinstance(row, dict):
            return False
        if not (
            row.get("role") == expected_role
            and row.get("fresh") is True
            and re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256") or ""))
            and bool(str(row.get("modified_at_utc") or "").strip())
        ):
            return False
    return True


def _process_lifecycle_closes(run: dict) -> bool:
    lifecycle = run.get("process_lifecycle")
    if not isinstance(lifecycle, dict):
        return False
    children = lifecycle.get("owned_solver_children_after")
    if not isinstance(children, list):
        return False
    alive = [row for row in children if isinstance(row, dict) and row.get("alive") is True]
    return (
        lifecycle.get("seat_released") is True
        and not alive
        and run.get("owned_process_count_after") == len(alive) == 0
    )


def _mao_terminal_record_flushed(run: dict) -> bool:
    artifacts = run.get("output_artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    mao = artifacts.get(".mao")
    mao = mao if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record")
    if terminal is None:
        return True
    if not isinstance(terminal, dict):
        return False

    def timestamp(value: object) -> float | None:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            return None

    solver_completed = timestamp(run.get("solver_completed_at_utc"))
    flush_completed = timestamp(terminal.get("flush_completed_at_utc"))
    return (
        bool(str(terminal.get("record_id", "")))
        and terminal.get("durably_flushed") is True
        and solver_completed is not None
        and flush_completed is not None
        and flush_completed >= solver_completed
    )


def _opened_result_matches_session_model(run: dict) -> bool:
    identity = run.get("session_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    solver_session = str(identity.get("solver_session_generation", ""))
    result_session = str(identity.get("result_open_session_generation", ""))
    session_model = str(identity.get("session_model_generation", ""))
    result_model = str(identity.get("opened_result_model_generation", ""))
    return (
        bool(solver_session)
        and solver_session == result_session
        and bool(session_model)
        and session_model == result_model
    )


def _result_material_matches_current_generation(run: dict) -> bool:
    identity = run.get("material_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    session = run.get("session_identity")
    session = session if isinstance(session, dict) else {}
    session_model = str(session.get("session_model_generation", ""))
    model_generation = str(identity.get("model_generation", ""))
    material_generation = str(identity.get("material_table_generation", ""))
    return (
        bool(session_model)
        and model_generation == session_model
        and str(identity.get("result_model_generation", "")) == model_generation
        and bool(material_generation)
        and str(identity.get("result_material_table_generation", ""))
        == material_generation
    )


def _terminal_convergence_recorded(run: dict) -> bool:
    artifacts = run.get("output_artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    mao = artifacts.get(".mao")
    mao = mao if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record")
    if terminal is None:
        return True
    if not isinstance(terminal, dict):
        return False
    convergence = terminal.get("convergence_record")
    if not isinstance(convergence, dict):
        return False
    try:
        iteration_count = int(convergence["iteration_count"])
        residual = float(convergence["final_residual_norm"])
    except (KeyError, TypeError, ValueError):
        return False
    return (
        convergence.get("status") == "converged"
        and convergence.get("solver_exit_code") == run.get("solver_exit_code") == 0
        and iteration_count >= 1
        and math.isfinite(residual)
        and residual >= 0.0
        and convergence.get("terminal_record_id") == terminal.get("record_id")
    )


def _mao_terminal_matches_current_job(run: dict) -> bool:
    artifacts = run.get("output_artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    mao = artifacts.get(".mao")
    mao = mao if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record")
    if terminal is None:
        return True
    if not isinstance(terminal, dict):
        return False
    try:
        block_index = int(terminal["terminal_block_index"])
        selected_index = int(terminal["selected_terminal_block_index"])
    except (KeyError, TypeError, ValueError):
        return False
    job_generation = str(terminal.get("job_generation", ""))
    return (
        bool(job_generation)
        and terminal.get("parsed_terminal_job_generation") == job_generation
        and block_index >= 0
        and selected_index == block_index
    )


def _force_surface_orientation_matches_remesh(run: dict) -> bool:
    identity = run.get("force_surface_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    surface_generation = str(identity.get("surface_mesh_generation", ""))
    orientation_digest = str(identity.get("surface_orientation_digest", ""))
    return (
        bool(surface_generation)
        and identity.get("orientation_sign_generation") == surface_generation
        and identity.get("force_integration_surface_generation")
        == surface_generation
        and bool(orientation_digest)
        and identity.get("force_orientation_digest") == orientation_digest
        and identity.get("surface_remeshed") is True
    )


def _mao_result_matches_live_model_digest(run: dict) -> bool:
    identity = run.get("mao_model_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    mao = artifacts.get(".mao")
    mao = mao if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record")
    terminal = terminal if isinstance(terminal, dict) else {}
    live_digest = str(identity.get("live_model_sha256", ""))
    embedded_digest = str(identity.get("mao_embedded_model_sha256", ""))
    job_generation = str(identity.get("job_generation", ""))
    return (
        bool(str(identity.get("job_name", "")).strip())
        and bool(re.fullmatch(r"[0-9a-f]{64}", live_digest))
        and embedded_digest == live_digest
        and bool(job_generation)
        and identity.get("mao_job_generation") == job_generation
        and terminal.get("job_generation") == job_generation
    )


def _linear_motor_terminal_sequence_matches_job(run: dict) -> bool:
    identity = run.get("linear_motor_terminal_sequence")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    mao = artifacts.get(".mao")
    mao = mao if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record")
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    terminals = identity.get("terminal_sequence")
    travel_direction = identity.get("positive_travel_direction")
    thrust_direction = identity.get("thrust_positive_direction")
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("terminal_sequence_job_generation") == job_generation
        and identity.get("thrust_observable_job_generation") == job_generation
        and terminals == ["U", "V", "W"]
        and len(set(terminals)) == 3
        and identity.get("travel_axis") in {"x", "y", "z"}
        and identity.get("thrust_axis") == identity.get("travel_axis")
        and type(travel_direction) is int
        and type(thrust_direction) is int
        and travel_direction in {-1, 1}
        and thrust_direction == travel_direction
    )


def _mao_subcase_selection_matches_current_run(run: dict) -> bool:
    identity = run.get("mao_subcase_selection_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    available_indices = identity.get("available_subcase_indices")
    requested_index = identity.get("current_requested_subcase_index")
    selected_index = identity.get("selected_subcase_index")
    digest = str(identity.get("selected_subcase_output_sha256", ""))
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("mao_result_job_generation") == job_generation
        and isinstance(available_indices, list)
        and bool(available_indices)
        and all(type(index) is int and index >= 0 for index in available_indices)
        and len(set(available_indices)) == len(available_indices)
        and type(requested_index) is int
        and requested_index in available_indices
        and selected_index == requested_index
        and identity.get("selected_subcase_job_generation") == job_generation
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
    )


def _terminal_convergence_matches_final_material_update(run: dict) -> bool:
    identity = run.get("terminal_convergence_material_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    material_generation = str(identity.get("final_material_update_generation", ""))
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("terminal_record_job_generation") == job_generation
        and bool(str(identity.get("terminal_record_id", "")))
        and identity.get("terminal_record_id") == terminal.get("record_id")
        and bool(material_generation)
        and identity.get("terminal_convergence_material_generation")
        == material_generation
    )


def _mao_record_count_trailer_matches_current_body(run: dict) -> bool:
    identity = run.get("mao_record_count_trailer_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    body_digest = str(identity.get("body_record_digest_sha256", ""))
    trailer_digest = str(identity.get("trailer_body_digest_sha256", ""))
    try:
        body_count = int(identity["parsed_body_record_count"])
        trailer_count = int(identity["declared_trailer_record_count"])
    except (KeyError, TypeError, ValueError):
        body_count = trailer_count = -1
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("mao_body_job_generation") == job_generation
        and identity.get("mao_trailer_job_generation") == job_generation
        and body_count > 0
        and trailer_count == body_count
        and re.fullmatch(r"[0-9a-f]{64}", body_digest) is not None
        and trailer_digest == body_digest
        and identity.get("trailer_present") is True
    )


def _nonlinear_scaled_residual_matches_current_iteration(run: dict) -> bool:
    identity = run.get("nonlinear_residual_scaled_norm_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    material_generation = str(identity.get("material_state_generation", ""))
    residual_generation = str(identity.get("residual_vector_generation", ""))
    try:
        terminal_iteration = int(identity["terminal_iteration_index"])
        residual_iteration = int(identity["residual_iteration_index"])
        scaling_iteration = int(identity["scaling_norm_iteration_index"])
        scaled_norm = float(identity["scaled_residual_norm"])
        tolerance = float(identity["terminal_tolerance"])
    except (KeyError, TypeError, ValueError):
        terminal_iteration = residual_iteration = scaling_iteration = -1
        scaled_norm = tolerance = math.nan
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and terminal_iteration >= 0
        and residual_iteration == terminal_iteration
        and scaling_iteration == terminal_iteration
        and bool(material_generation)
        and identity.get("residual_material_state_generation")
        == material_generation
        and identity.get("scaling_norm_material_state_generation")
        == material_generation
        and bool(residual_generation)
        and identity.get("scaled_norm_residual_generation") == residual_generation
        and math.isfinite(scaled_norm)
        and scaled_norm >= 0.0
        and math.isfinite(tolerance)
        and tolerance > 0.0
        and scaled_norm <= tolerance
    )


def _mao_record_precision_matches_header(run: dict) -> bool:
    identity = run.get("mao_record_precision_header_payload_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    record_generation = str(identity.get("record_generation", ""))
    precision = str(identity.get("header_float_precision", ""))
    expected_bytes = {"float32": 4, "float64": 8}.get(precision)
    try:
        header_bytes = int(identity.get("header_bytes_per_float"))
        payload_bytes = int(identity.get("payload_bytes_per_float"))
    except (TypeError, ValueError):
        header_bytes = payload_bytes = -1
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("record_header_job_generation") == job_generation
        and identity.get("record_payload_job_generation") == job_generation
        and bool(record_generation)
        and identity.get("header_record_generation") == record_generation
        and identity.get("payload_record_generation") == record_generation
        and expected_bytes is not None
        and identity.get("payload_float_precision") == precision
        and header_bytes == expected_bytes
        and payload_bytes == expected_bytes
        and identity.get("header_endianness") in {"little", "big"}
        and identity.get("payload_endianness") == identity.get("header_endianness")
    )


def _material_id_table_matches_current_model(run: dict) -> bool:
    identity = run.get("material_id_table_model_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    model_generation = str(identity.get("active_model_generation", ""))
    material_table = identity.get("material_id_table")
    result_ids = identity.get("result_region_material_ids")
    resolved_ids = identity.get("resolved_material_ids")
    table_digest = str(identity.get("material_id_table_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(model_generation)
        and identity.get("result_region_model_generation") == model_generation
        and identity.get("material_id_table_model_generation") == model_generation
        and isinstance(material_table, dict)
        and bool(material_table)
        and all(str(key).isdigit() and bool(str(value)) for key, value in material_table.items())
        and isinstance(result_ids, list)
        and bool(result_ids)
        and resolved_ids == result_ids
        and all(str(material_id) in material_table for material_id in result_ids)
        and re.fullmatch(r"[0-9a-f]{64}", table_digest) is not None
        and identity.get("result_material_mapping_sha256") == table_digest
    )


def _mao_section_offset_alignment_matches_payload(run: dict) -> bool:
    identity = run.get("mao_section_offset_byte_order_alignment_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    section_generation = str(identity.get("section_generation", ""))
    try:
        section_offset = int(identity.get("section_offset_bytes"))
        decoded_offset = int(identity.get("decoded_section_offset_bytes"))
        section_count = int(identity.get("section_byte_count"))
        decoded_count = int(identity.get("decoded_section_byte_count"))
        alignment = int(identity.get("section_alignment_bytes"))
        decoded_alignment = int(identity.get("decoded_section_alignment_bytes"))
    except (TypeError, ValueError):
        section_offset = decoded_offset = section_count = decoded_count = -1
        alignment = decoded_alignment = -1
    section_digest = str(identity.get("section_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(section_generation)
        and identity.get("section_header_generation") == section_generation
        and identity.get("section_payload_generation") == section_generation
        and section_offset >= 0
        and decoded_offset == section_offset
        and section_count > 0
        and decoded_count == section_count
        and identity.get("section_byte_order") in {"little", "big"}
        and identity.get("decoded_section_byte_order")
        == identity.get("section_byte_order")
        and alignment > 0
        and decoded_alignment == alignment
        and section_offset % alignment == 0
        and re.fullmatch(r"[0-9a-f]{64}", section_digest) is not None
        and str(identity.get("decoded_section_sha256", "")).lower()
        == section_digest
    )


def _material_temperature_interpolation_matches_table(run: dict) -> bool:
    identity = run.get("material_temperature_interpolation_table_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    material_generation = str(identity.get("material_generation", ""))
    table_generation = str(identity.get("temperature_table_generation", ""))
    try:
        requested = float(identity.get("requested_temperature_c"))
        lower = float(identity.get("lower_temperature_c"))
        upper = float(identity.get("upper_temperature_c"))
        weight = float(identity.get("interpolation_weight"))
    except (TypeError, ValueError):
        requested = lower = upper = weight = math.nan
    table_digest = str(identity.get("temperature_table_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(material_generation)
        and identity.get("resolved_material_generation") == material_generation
        and bool(table_generation)
        and identity.get("interpolation_weight_table_generation")
        == table_generation
        and identity.get("result_temperature_table_generation") == table_generation
        and all(math.isfinite(value) for value in (requested, lower, upper, weight))
        and lower < requested < upper
        and math.isclose(
            weight,
            (requested - lower) / (upper - lower),
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
        and re.fullmatch(r"[0-9a-f]{64}", table_digest) is not None
        and str(identity.get("interpolation_table_sha256", "")).lower()
        == table_digest
    )


def _mao_floating_precision_record_layout_matches(run: dict) -> bool:
    identity = run.get("mao_floating_precision_record_layout_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    layout_generation = str(identity.get("record_layout_generation", ""))
    try:
        scalar_bytes = int(identity.get("declared_scalar_bytes"))
        decoder_scalar_bytes = int(identity.get("decoder_scalar_bytes"))
        stride = int(identity.get("record_stride_bytes"))
        decoded_stride = int(identity.get("decoded_record_stride_bytes"))
    except (TypeError, ValueError):
        scalar_bytes = decoder_scalar_bytes = stride = decoded_stride = -1
    layout_digest = str(identity.get("record_layout_sha256", "")).lower()
    precision_bytes = {"float32": 4, "float64": 8}
    precision = identity.get("declared_floating_precision")
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(layout_generation)
        and identity.get("decoder_record_layout_generation") == layout_generation
        and precision in precision_bytes
        and identity.get("decoder_floating_precision") == precision
        and scalar_bytes == precision_bytes[precision]
        and decoder_scalar_bytes == scalar_bytes
        and stride > 0
        and stride % scalar_bytes == 0
        and decoded_stride == stride
        and re.fullmatch(r"[0-9a-f]{64}", layout_digest) is not None
        and str(identity.get("decoded_record_layout_sha256", "")).lower()
        == layout_digest
    )


def _nonlinear_history_residual_scaling_matches_mesh(run: dict) -> bool:
    identity = run.get("nonlinear_history_residual_scaling_mesh_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    mao = run.get("output_artifacts")
    mao = mao.get(".mao") if isinstance(mao, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    mesh_generation = str(identity.get("mesh_generation", ""))
    try:
        vector_size = int(identity.get("residual_scaling_vector_size"))
        dof_count = int(identity.get("active_dof_count"))
    except (TypeError, ValueError):
        vector_size = dof_count = -1
    scaling_digest = str(identity.get("residual_scaling_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(mesh_generation)
        and identity.get("nonlinear_history_mesh_generation") == mesh_generation
        and identity.get("residual_scaling_mesh_generation") == mesh_generation
        and identity.get("residual_norm_basis") == "scaled_l2"
        and identity.get("history_residual_norm_basis")
        == identity.get("residual_norm_basis")
        and vector_size > 0
        and vector_size == dof_count
        and re.fullmatch(r"[0-9a-f]{64}", scaling_digest) is not None
        and str(identity.get("history_residual_scaling_sha256", "")).lower()
        == scaling_digest
    )


def _mao_section_endian_marker_matches_decoder(run: dict) -> bool:
    identity = run.get("mao_section_endian_marker_decoder_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    layout_generation = str(identity.get("section_layout_generation", ""))
    marker_digest = str(identity.get("endian_marker_sha256", "")).lower()
    byte_order = identity.get("declared_byte_order")
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(layout_generation)
        and identity.get("endian_marker_section_layout_generation")
        == layout_generation
        and identity.get("decoder_section_layout_generation") == layout_generation
        and byte_order in {"little", "big"}
        and identity.get("endian_marker_byte_order") == byte_order
        and identity.get("decoder_byte_order") == byte_order
        and re.fullmatch(r"[0-9a-f]{64}", marker_digest) is not None
        and str(identity.get("decoded_endian_marker_sha256", "")).lower()
        == marker_digest
    )


def _coil_group_map_matches_current_numbering(run: dict) -> bool:
    identity = run.get("coil_group_map_model_numbering_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    numbering_generation = str(identity.get("model_numbering_generation", ""))
    conductor_ids = identity.get("conductor_ids")
    mapped_ids = identity.get("mapped_conductor_ids")
    group_ids = identity.get("coil_group_ids")
    map_digest = str(identity.get("coil_group_map_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(numbering_generation)
        and identity.get("conductor_result_model_numbering_generation")
        == numbering_generation
        and identity.get("coil_group_map_model_numbering_generation")
        == numbering_generation
        and isinstance(conductor_ids, list)
        and bool(conductor_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in conductor_ids
        )
        and len(set(conductor_ids)) == len(conductor_ids)
        and mapped_ids == conductor_ids
        and isinstance(group_ids, list)
        and len(group_ids) == len(conductor_ids)
        and all(isinstance(value, str) and bool(value) for value in group_ids)
        and len(set(group_ids)) == len(group_ids)
        and re.fullmatch(r"[0-9a-f]{64}", map_digest) is not None
        and str(identity.get("result_coil_group_map_sha256", "")).lower()
        == map_digest
    )


def _mao_record_stride_alignment_matches_section(run: dict) -> bool:
    identity = run.get("mao_record_stride_alignment_section_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    layout_generation = str(identity.get("section_layout_generation", ""))
    try:
        stride = int(identity.get("record_stride_bytes"))
        decoded_stride = int(identity.get("decoder_record_stride_bytes"))
        alignment = int(identity.get("record_alignment_bytes"))
        decoded_alignment = int(identity.get("decoder_record_alignment_bytes"))
    except (TypeError, ValueError):
        stride = decoded_stride = alignment = decoded_alignment = -1
    offsets = identity.get("record_offsets")
    decoded_offsets = identity.get("decoded_record_offsets")
    layout_digest = str(identity.get("section_layout_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(layout_generation)
        and identity.get("record_stride_section_layout_generation")
        == layout_generation
        and identity.get("alignment_section_layout_generation")
        == layout_generation
        and identity.get("decoder_section_layout_generation") == layout_generation
        and stride > 0
        and stride == decoded_stride
        and alignment > 0
        and alignment == decoded_alignment
        and stride % alignment == 0
        and isinstance(offsets, list)
        and len(offsets) >= 2
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value >= 0
            and value % alignment == 0
            for value in offsets
        )
        and all(right - left == stride for left, right in zip(offsets, offsets[1:]))
        and decoded_offsets == offsets
        and re.fullmatch(r"[0-9a-f]{64}", layout_digest) is not None
        and str(identity.get("decoded_section_layout_sha256", "")).lower()
        == layout_digest
    )


def _material_curve_region_map_matches_model_reorder(run: dict) -> bool:
    identity = run.get("material_curve_id_region_assignment_model_reorder_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    reorder_generation = str(identity.get("model_reorder_generation", ""))
    curve_ids = identity.get("material_curve_ids")
    region_ids = identity.get("region_ids")
    map_digest = str(
        identity.get("material_curve_region_map_sha256", "")
    ).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(reorder_generation)
        and identity.get("material_assignment_model_reorder_generation")
        == reorder_generation
        and identity.get("result_region_model_reorder_generation")
        == reorder_generation
        and isinstance(curve_ids, list)
        and isinstance(region_ids, list)
        and bool(curve_ids)
        and len(curve_ids) == len(region_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in curve_ids + region_ids
        )
        and len(set(curve_ids)) == len(curve_ids)
        and len(set(region_ids)) == len(region_ids)
        and identity.get("assigned_material_curve_ids") == curve_ids
        and identity.get("result_region_ids") == region_ids
        and re.fullmatch(r"[0-9a-f]{64}", map_digest) is not None
        and str(
            identity.get("result_material_curve_region_map_sha256", "")
        ).lower()
        == map_digest
    )


def _hysteresis_curve_branch_units_match_region_generation(run: dict) -> bool:
    identity = run.get("hysteresis_curve_branch_unit_region_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    material_generation = str(identity.get("material_generation", ""))
    region_generation = str(identity.get("region_map_generation", ""))
    branches = identity.get("curve_branches")
    units = identity.get("field_units")
    region_ids = identity.get("region_ids")
    map_digest = str(identity.get("curve_region_map_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(material_generation)
        and identity.get("result_material_generation") == material_generation
        and bool(region_generation)
        and identity.get("curve_branch_region_map_generation")
        == region_generation
        and identity.get("field_unit_region_map_generation")
        == region_generation
        and identity.get("result_region_map_generation") == region_generation
        and isinstance(branches, list)
        and bool(branches)
        and len(set(branches)) == len(branches)
        and all(branch in {"ascending", "descending"} for branch in branches)
        and identity.get("parsed_curve_branches") == branches
        and units == {"B": "T", "H": "A/m"}
        and identity.get("parsed_field_units") == units
        and isinstance(region_ids, list)
        and len(region_ids) == len(branches)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in region_ids
        )
        and len(set(region_ids)) == len(region_ids)
        and identity.get("curve_region_ids") == region_ids
        and re.fullmatch(r"[0-9a-f]{64}", map_digest) is not None
        and str(identity.get("result_curve_region_map_sha256", "")).lower()
        == map_digest
    )


def _run_result_iteration_table_matches_solver_generation(run: dict) -> bool:
    identity = run.get(
        "run_result_step_solver_iteration_table_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    solver_generation = str(identity.get("solver_run_generation", ""))
    step_ids = identity.get("step_ids")
    iteration_indices = identity.get("iteration_indices")
    convergence_rows = identity.get("convergence_rows")
    table_digest = str(
        identity.get("solver_iteration_table_sha256", "")
    ).lower()
    rows_valid = (
        isinstance(convergence_rows, list)
        and isinstance(step_ids, list)
        and isinstance(iteration_indices, list)
        and len(convergence_rows) == len(step_ids) == len(iteration_indices)
        and all(
            isinstance(row, dict)
            and row.get("step_id") == step_id
            and row.get("iteration_index") == iteration_index
            and row.get("converged") is True
            for row, step_id, iteration_index in zip(
                convergence_rows, step_ids, iteration_indices
            )
        )
    )
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(solver_generation)
        and identity.get("run_result_solver_generation") == solver_generation
        and identity.get("step_table_solver_generation") == solver_generation
        and identity.get("iteration_table_solver_generation")
        == solver_generation
        and identity.get("convergence_table_solver_generation")
        == solver_generation
        and isinstance(step_ids, list)
        and bool(step_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in step_ids
        )
        and len(set(step_ids)) == len(step_ids)
        and step_ids == sorted(step_ids)
        and identity.get("parsed_step_ids") == step_ids
        and isinstance(iteration_indices, list)
        and all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in iteration_indices
        )
        and iteration_indices == sorted(iteration_indices)
        and identity.get("parsed_iteration_indices") == iteration_indices
        and rows_valid
        and identity.get("parsed_convergence_rows") == convergence_rows
        and re.fullmatch(r"[0-9a-f]{64}", table_digest) is not None
        and str(
            identity.get("parsed_solver_iteration_table_sha256", "")
        ).lower()
        == table_digest
    )


def _material_region_property_table_matches_unit_index_generation(run: dict) -> bool:
    identity = run.get(
        "material_region_property_table_unit_index_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    table_generation = str(identity.get("material_table_generation", ""))
    region_ids = identity.get("region_ids")
    row_indices = identity.get("property_row_indices")
    units = identity.get("property_units")
    digest = str(identity.get("material_region_table_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(table_generation)
        and all(
            identity.get(key) == table_generation
            for key in (
                "region_material_table_generation",
                "unit_material_table_generation",
                "index_material_table_generation",
            )
        )
        and isinstance(region_ids, list)
        and bool(region_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in region_ids
        )
        and len(set(region_ids)) == len(region_ids)
        and identity.get("result_region_ids") == region_ids
        and isinstance(row_indices, list)
        and len(row_indices) == len(region_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in row_indices
        )
        and len(set(row_indices)) == len(row_indices)
        and identity.get("result_property_row_indices") == row_indices
        and isinstance(units, list)
        and len(units) == len(region_ids)
        and all(bool(str(value)) for value in units)
        and identity.get("result_property_units") == units
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("result_material_region_table_sha256", "")).lower()
        == digest
    )


def _result_observables_match_frame_unit_generation(run: dict) -> bool:
    identity = run.get(
        "result_scalar_vector_coordinate_frame_unit_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    observable_generation = str(identity.get("observable_generation", ""))
    scalar_names = identity.get("scalar_names")
    scalar_units = identity.get("scalar_units")
    vector_names = identity.get("vector_names")
    vector_units = identity.get("vector_units")
    frame = str(identity.get("coordinate_frame_id", ""))
    transform_digest = str(
        identity.get("coordinate_transform_sha256", "")
    ).lower()
    table_digest = str(identity.get("observable_table_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(observable_generation)
        and all(
            identity.get(key) == observable_generation
            for key in (
                "scalar_observable_generation",
                "vector_observable_generation",
                "frame_observable_generation",
                "unit_observable_generation",
            )
        )
        and isinstance(scalar_names, list)
        and bool(scalar_names)
        and len(set(scalar_names)) == len(scalar_names)
        and identity.get("parsed_scalar_names") == scalar_names
        and isinstance(scalar_units, list)
        and len(scalar_units) == len(scalar_names)
        and identity.get("parsed_scalar_units") == scalar_units
        and isinstance(vector_names, list)
        and bool(vector_names)
        and len(set(vector_names)) == len(vector_names)
        and identity.get("parsed_vector_names") == vector_names
        and isinstance(vector_units, list)
        and len(vector_units) == len(vector_names)
        and identity.get("parsed_vector_units") == vector_units
        and frame in {"global-cartesian", "body-local"}
        and identity.get("parsed_coordinate_frame_id") == frame
        and re.fullmatch(r"[0-9a-f]{64}", transform_digest) is not None
        and str(
            identity.get("parsed_coordinate_transform_sha256", "")
        ).lower()
        == transform_digest
        and re.fullmatch(r"[0-9a-f]{64}", table_digest) is not None
        and str(identity.get("parsed_observable_table_sha256", "")).lower()
        == table_digest
    )


def _source_manifest_complete(source_files: object) -> bool:
    if not isinstance(source_files, list) or len(source_files) != 6:
        return False
    names: set[str] = set()
    for row in source_files:
        if not isinstance(row, dict):
            return False
        name = str(row.get("name", ""))
        digest = str(row.get("sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            return False
        names.add(name)
    return names == _EXPECTED_SOURCE_NAMES


def force_method_profile_contract_gate(summary_json: str) -> dict:
    """Validate deck roles and GUI-free replay metadata without opening files."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    deck_roles = summary.get("deck_roles")
    if not isinstance(deck_roles, list) or len(deck_roles) != 3:
        raise ValueError("deck_roles must contain exactly three records")
    indexed_decks = {
        str(row.get("role", "")): row for row in deck_roles if isinstance(row, dict)
    }
    if set(indexed_decks) != set(_CASE_ROLES):
        raise ValueError(f"deck roles must be exactly {sorted(_CASE_ROLES)}")

    runs = summary.get("runs")
    if not isinstance(runs, list) or len(runs) != 6:
        raise ValueError("runs must contain exactly six records")

    expected_shapes = {
        "element_force": (6, 0),
        "maxwell_stress": (0, 6),
        "combined_methods": (6, 6),
    }
    role_replays: dict[str, set[int]] = {role: set() for role in _CASE_ROLES}
    run_contracts: list[bool] = []
    output_artifact_contracts: list[bool] = []
    process_lifecycle_contracts: list[bool] = []
    mao_flush_contracts: list[bool] = []
    session_model_contracts: list[bool] = []
    material_generation_contracts: list[bool] = []
    convergence_record_contracts: list[bool] = []
    terminal_job_contracts: list[bool] = []
    surface_orientation_contracts: list[bool] = []
    model_digest_contracts: list[bool] = []
    terminal_sequence_contracts: list[bool] = []
    subcase_selection_contracts: list[bool] = []
    convergence_material_contracts: list[bool] = []
    mao_record_count_trailer_contracts: list[bool] = []
    nonlinear_scaled_residual_contracts: list[bool] = []
    mao_record_precision_contracts: list[bool] = []
    material_id_table_contracts: list[bool] = []
    mao_section_offset_contracts: list[bool] = []
    material_temperature_interpolation_contracts: list[bool] = []
    mao_floating_precision_layout_contracts: list[bool] = []
    nonlinear_history_scaling_mesh_contracts: list[bool] = []
    mao_section_endian_marker_contracts: list[bool] = []
    coil_group_map_numbering_contracts: list[bool] = []
    mao_record_stride_alignment_contracts: list[bool] = []
    material_curve_region_map_contracts: list[bool] = []
    hysteresis_curve_region_contracts: list[bool] = []
    run_result_iteration_table_contracts: list[bool] = []
    material_region_property_table_contracts: list[bool] = []
    result_observable_frame_unit_contracts: list[bool] = []
    for run in runs:
        if not isinstance(run, dict):
            run_contracts.append(False)
            output_artifact_contracts.append(False)
            process_lifecycle_contracts.append(False)
            mao_flush_contracts.append(False)
            session_model_contracts.append(False)
            material_generation_contracts.append(False)
            convergence_record_contracts.append(False)
            terminal_job_contracts.append(False)
            surface_orientation_contracts.append(False)
            model_digest_contracts.append(False)
            terminal_sequence_contracts.append(False)
            subcase_selection_contracts.append(False)
            convergence_material_contracts.append(False)
            mao_record_count_trailer_contracts.append(False)
            nonlinear_scaled_residual_contracts.append(False)
            mao_record_precision_contracts.append(False)
            material_id_table_contracts.append(False)
            mao_section_offset_contracts.append(False)
            material_temperature_interpolation_contracts.append(False)
            mao_floating_precision_layout_contracts.append(False)
            nonlinear_history_scaling_mesh_contracts.append(False)
            mao_section_endian_marker_contracts.append(False)
            coil_group_map_numbering_contracts.append(False)
            mao_record_stride_alignment_contracts.append(False)
            material_curve_region_map_contracts.append(False)
            hysteresis_curve_region_contracts.append(False)
            run_result_iteration_table_contracts.append(False)
            material_region_property_table_contracts.append(False)
            result_observable_frame_unit_contracts.append(False)
            continue
        role = str(run.get("role", ""))
        parsed_rows = run.get("parsed_rows")
        parsed_rows = parsed_rows if isinstance(parsed_rows, dict) else {}
        output_roles = run.get("output_roles")
        output_roles = output_roles if isinstance(output_roles, dict) else {}
        expected_shape = expected_shapes.get(role)
        try:
            replay_id = int(run.get("replay", -1))
        except (TypeError, ValueError):
            replay_id = -1
        if role in role_replays:
            role_replays[role].add(replay_id)
        output_artifact_contracts.append(_output_artifacts_complete(run))
        process_lifecycle_contracts.append(_process_lifecycle_closes(run))
        mao_flush_contracts.append(_mao_terminal_record_flushed(run))
        session_model_contracts.append(_opened_result_matches_session_model(run))
        material_generation_contracts.append(
            _result_material_matches_current_generation(run)
        )
        convergence_record_contracts.append(_terminal_convergence_recorded(run))
        terminal_job_contracts.append(_mao_terminal_matches_current_job(run))
        surface_orientation_contracts.append(
            _force_surface_orientation_matches_remesh(run)
        )
        model_digest_contracts.append(_mao_result_matches_live_model_digest(run))
        terminal_sequence_contracts.append(
            _linear_motor_terminal_sequence_matches_job(run)
        )
        subcase_selection_contracts.append(
            _mao_subcase_selection_matches_current_run(run)
        )
        convergence_material_contracts.append(
            _terminal_convergence_matches_final_material_update(run)
        )
        mao_record_count_trailer_contracts.append(
            _mao_record_count_trailer_matches_current_body(run)
        )
        nonlinear_scaled_residual_contracts.append(
            _nonlinear_scaled_residual_matches_current_iteration(run)
        )
        mao_record_precision_contracts.append(
            _mao_record_precision_matches_header(run)
        )
        material_id_table_contracts.append(
            _material_id_table_matches_current_model(run)
        )
        mao_section_offset_contracts.append(
            _mao_section_offset_alignment_matches_payload(run)
        )
        material_temperature_interpolation_contracts.append(
            _material_temperature_interpolation_matches_table(run)
        )
        mao_floating_precision_layout_contracts.append(
            _mao_floating_precision_record_layout_matches(run)
        )
        nonlinear_history_scaling_mesh_contracts.append(
            _nonlinear_history_residual_scaling_matches_mesh(run)
        )
        mao_section_endian_marker_contracts.append(
            _mao_section_endian_marker_matches_decoder(run)
        )
        coil_group_map_numbering_contracts.append(
            _coil_group_map_matches_current_numbering(run)
        )
        mao_record_stride_alignment_contracts.append(
            _mao_record_stride_alignment_matches_section(run)
        )
        material_curve_region_map_contracts.append(
            _material_curve_region_map_matches_model_reorder(run)
        )
        hysteresis_curve_region_contracts.append(
            _hysteresis_curve_branch_units_match_region_generation(run)
        )
        run_result_iteration_table_contracts.append(
            _run_result_iteration_table_matches_solver_generation(run)
        )
        material_region_property_table_contracts.append(
            _material_region_property_table_matches_unit_index_generation(run)
        )
        result_observable_frame_unit_contracts.append(
            _result_observables_match_frame_unit_generation(run)
        )
        run_contracts.append(
            role in _CASE_ROLES
            and run.get("case_id") == _CASE_ROLES[role]
            and run.get("mesh_exit_code") == 0
            and run.get("solver_exit_code") == 0
            and run.get("source_copy_preserved") is True
            and run.get("all_outputs_fresh") is True
            and run.get("owned_process_count_after") == 0
            and output_roles == _OUTPUT_ROLES
            and expected_shape is not None
            and (parsed_rows.get("FORC"), parsed_rows.get("FORT")) == expected_shape
        )

    element_deck = indexed_decks["element_force"]
    stress_deck = indexed_decks["maxwell_stress"]
    combined_deck = indexed_decks["combined_methods"]
    replay = summary.get("replay")
    replay = replay if isinstance(replay, dict) else {}
    public_gate = summary.get("public_gate")
    public_gate = public_gate if isinstance(public_gate, dict) else {}
    source_files = summary.get("source_files")
    source_files = source_files if isinstance(source_files, list) else []
    checks = {
        "direct_mesh_and_solver_cli_without_launcher": summary.get("execution_route")
        == "direct_mesh_and_solver_exe_no_gui",
        "completion_dialog_disabled": summary.get("completion_dialog") is False,
        "solver_family_recorded": summary.get("solver_family") == "magnetostatic_bem",
        "mao_total_is_result_authority": summary.get("result_authority") == ".mao TOTAL",
        "source_manifest_names_and_digests_complete": _source_manifest_complete(
            summary.get("source_files")
        ),
        "element_deck_pins_all_body_forc_selection": element_deck.get("case_id")
        == _CASE_ROLES["element_force"]
        and element_deck.get("forc_steps") == 6
        and element_deck.get("fort_steps") == 0
        and element_deck.get("selection_scope") == "all_magnetic_bodies"
        and element_deck.get("stress_surface_recorded") is False,
        "stress_deck_pins_closed_surface_fort_selection": stress_deck.get("case_id")
        == _CASE_ROLES["maxwell_stress"]
        and stress_deck.get("forc_steps") == 0
        and stress_deck.get("fort_steps") == 6
        and stress_deck.get("selection_scope") == "closed_stress_surface"
        and stress_deck.get("stress_surface_recorded") is True,
        "combined_deck_pins_target_body_and_closed_surface": combined_deck.get("case_id")
        == _CASE_ROLES["combined_methods"]
        and combined_deck.get("forc_steps") == 6
        and combined_deck.get("fort_steps") == 6
        and combined_deck.get("selection_scope") == "moving_body_only"
        and combined_deck.get("stress_surface_recorded") is True,
        "six_fresh_headless_runs_are_complete": all(run_contracts),
        "each_output_role_has_fresh_digest_bound_artifact": all(
            output_artifact_contracts
        ),
        "seat_release_and_owned_solver_children_close": all(
            process_lifecycle_contracts
        ),
        "mao_terminal_record_is_durably_flushed": all(mao_flush_contracts),
        "opened_result_matches_current_session_model_generation": all(
            session_model_contracts
        ),
        "result_material_table_matches_current_model_generation": all(
            material_generation_contracts
        ),
        "terminal_success_includes_solver_convergence_record": all(
            convergence_record_contracts
        ),
        "mao_terminal_block_matches_current_job_generation": all(
            terminal_job_contracts
        ),
        "force_surface_orientation_matches_current_remesh": all(
            surface_orientation_contracts
        ),
        "mao_result_model_digest_matches_current_live_model": all(
            model_digest_contracts
        ),
        "linear_motor_terminal_sequence_matches_current_job": all(
            terminal_sequence_contracts
        ),
        "mao_selected_subcase_matches_current_run_generation": all(
            subcase_selection_contracts
        ),
        "terminal_convergence_matches_final_material_update_generation": all(
            convergence_material_contracts
        ),
        "mao_record_count_and_trailer_match_current_body_generation": all(
            mao_record_count_trailer_contracts
        ),
        "nonlinear_scaled_residual_uses_current_material_iteration": all(
            nonlinear_scaled_residual_contracts
        ),
        "mao_record_precision_matches_header_and_payload": all(
            mao_record_precision_contracts
        ),
        "material_id_table_matches_current_model_generation": all(
            material_id_table_contracts
        ),
        "mao_section_offset_uses_current_byte_order_and_alignment": all(
            mao_section_offset_contracts
        ),
        "material_temperature_interpolation_uses_current_table_generation": all(
            material_temperature_interpolation_contracts
        ),
        "mao_floating_precision_matches_current_record_layout": all(
            mao_floating_precision_layout_contracts
        ),
        "nonlinear_history_residual_scaling_matches_current_mesh": all(
            nonlinear_history_scaling_mesh_contracts
        ),
        "mao_section_endian_marker_matches_current_decoder_generation": all(
            mao_section_endian_marker_contracts
        ),
        "coil_group_map_matches_current_model_numbering_generation": all(
            coil_group_map_numbering_contracts
        ),
        "mao_record_stride_and_alignment_match_current_section_layout": all(
            mao_record_stride_alignment_contracts
        ),
        "material_curve_region_map_matches_current_model_reorder_generation": all(
            material_curve_region_map_contracts
        ),
        "hysteresis_curve_branches_and_units_match_current_region_generation": all(
            hysteresis_curve_region_contracts
        ),
        "run_result_iteration_table_matches_current_solver_generation": all(
            run_result_iteration_table_contracts
        ),
        "material_regions_use_current_property_rows_units_and_indices": all(
            material_region_property_table_contracts
        ),
        "result_observables_use_current_scalar_vector_frame_and_units": all(
            result_observable_frame_unit_contracts
        ),
        "two_replays_per_source_role": all(
            replays == {1, 2} for replays in role_replays.values()
        ),
        "parsed_force_rows_replay_exact": replay.get("parsed_force_rows_exact") is True,
        "binary_nonlog_outputs_replay_exact": replay.get(
            "binary_nonlog_outputs_exact"
        )
        is True,
        "public_force_method_gate_passed": public_gate.get("policy")
        == "magnetic_force_method_profile_gate_v1"
        and public_gate.get("status") == "ok",
    }
    return {
        "schema": "elf-force-method-profile-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "metrics": {
            "source_file_count": len(source_files),
            "run_count": len(runs),
            "replay_count_per_role": {
                role: len(replays) for role, replays in role_replays.items()
            },
        },
        "notes": [
            "FORC and FORT profiles are comparable only when body and closed-surface selections are explicit",
            "the .mao TOTAL rows are the result authority; .mei remains an input deck",
            "a complete .mao cannot make a stale .mag fresh; bind every output digest and close owned child processes as well as the seat",
            "this public documentation contract opens no paths and exposes no solved values",
        ],
    }
