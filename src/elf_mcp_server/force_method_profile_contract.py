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


def _output_record_matches_version_endian_length_generation(run: dict) -> bool:
    identity = run.get(
        "output_record_version_endian_length_generation_identity"
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
    output_generation = str(identity.get("output_file_generation", ""))
    version = identity.get("record_version")
    byte_order = identity.get("byte_order")
    record_length = identity.get("record_length_bytes")
    payload_length = identity.get("payload_length_bytes")
    digest = str(identity.get("output_record_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(output_generation)
        and all(
            identity.get(key) == output_generation
            for key in (
                "record_version_output_file_generation",
                "byte_order_output_file_generation",
                "record_length_output_file_generation",
            )
        )
        and isinstance(version, int)
        and not isinstance(version, bool)
        and version > 0
        and identity.get("parsed_record_version") == version
        and byte_order in {"little", "big"}
        and identity.get("parsed_byte_order") == byte_order
        and isinstance(record_length, int)
        and not isinstance(record_length, bool)
        and record_length > 0
        and identity.get("parsed_record_length_bytes") == record_length
        and isinstance(payload_length, int)
        and not isinstance(payload_length, bool)
        and 0 < payload_length <= record_length
        and identity.get("parsed_payload_length_bytes") == payload_length
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("parsed_output_record_sha256", "")).lower()
        == digest
    )


def _winding_matches_turn_current_phase_region_generation(run: dict) -> bool:
    identity = run.get(
        "winding_turn_current_phase_region_map_generation_identity"
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
    model_generation = str(identity.get("model_generation", ""))
    phases = identity.get("phase_order")
    turns = identity.get("turn_counts")
    currents = identity.get("complex_currents_a")
    region_ids = identity.get("region_ids")
    region_map = identity.get("phase_region_map")
    digest = str(identity.get("winding_input_table_sha256", "")).lower()
    phases_ok = (
        isinstance(phases, list)
        and bool(phases)
        and all(bool(str(value).strip()) for value in phases)
        and len(set(phases)) == len(phases)
    )
    turns_ok = (
        isinstance(turns, list)
        and phases_ok
        and len(turns) == len(phases)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            for value in turns
        )
    )
    currents_ok = (
        isinstance(currents, list)
        and phases_ok
        and len(currents) == len(phases)
        and all(
            isinstance(value, list)
            and len(value) == 2
            and all(
                isinstance(component, (int, float))
                and not isinstance(component, bool)
                and math.isfinite(float(component))
                for component in value
            )
            for value in currents
        )
    )
    regions_ok = (
        isinstance(region_ids, list)
        and phases_ok
        and len(region_ids) == len(phases)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            for value in region_ids
        )
        and len(set(region_ids)) == len(region_ids)
    )
    expected_map = (
        [[phase, region] for phase, region in zip(phases, region_ids)]
        if phases_ok and regions_ok
        else []
    )
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(model_generation)
        and all(
            identity.get(key) == model_generation
            for key in (
                "turn_count_model_generation",
                "current_phase_model_generation",
                "region_map_model_generation",
            )
        )
        and phases_ok
        and identity.get("resolved_phase_order") == phases
        and turns_ok
        and identity.get("resolved_turn_counts") == turns
        and currents_ok
        and identity.get("resolved_complex_currents_a") == currents
        and regions_ok
        and identity.get("resolved_region_ids") == region_ids
        and region_map == expected_map
        and identity.get("resolved_phase_region_map") == region_map
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("resolved_winding_input_table_sha256", "")).lower()
        == digest
    )


def _bem_panel_material_region_matches_model_generation(run: dict) -> bool:
    identity = run.get(
        "bem_panel_group_material_permeability_region_generation_identity"
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
    model_generation = str(identity.get("model_generation", ""))
    panel_ids = identity.get("panel_group_ids")
    orientations = identity.get("region_orientations")
    permeabilities = identity.get("relative_permeabilities")
    region_map = identity.get("panel_material_region_map")
    digest = str(identity.get("panel_region_table_sha256", "")).lower()
    panels_ok = (
        isinstance(panel_ids, list)
        and bool(panel_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool) and value > 0
            for value in panel_ids
        )
        and len(set(panel_ids)) == len(panel_ids)
    )
    orientations_ok = (
        isinstance(orientations, list)
        and panels_ok
        and len(orientations) == len(panel_ids)
        and all(value in {-1, 1} for value in orientations)
    )
    permeability_ok = (
        isinstance(permeabilities, list)
        and panels_ok
        and len(permeabilities) == len(panel_ids)
        and all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            and float(value) > 0.0
            for value in permeabilities
        )
    )
    expected_map = (
        [
            [panel_id, material_index, orientation]
            for material_index, (panel_id, orientation) in enumerate(
                zip(panel_ids, orientations), start=1
            )
        ]
        if panels_ok and orientations_ok
        else []
    )
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(model_generation)
        and all(
            identity.get(key) == model_generation
            for key in (
                "panel_group_model_generation",
                "region_orientation_model_generation",
                "permeability_map_model_generation",
                "result_model_generation",
            )
        )
        and panels_ok
        and identity.get("result_panel_group_ids") == panel_ids
        and orientations_ok
        and identity.get("result_region_orientations") == orientations
        and permeability_ok
        and identity.get("result_relative_permeabilities") == permeabilities
        and region_map == expected_map
        and identity.get("result_panel_material_region_map") == region_map
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("result_panel_region_table_sha256", "")).lower()
        == digest
    )


def _position_sweep_force_rows_match_generation(run: dict) -> bool:
    identity = run.get("position_sweep_force_frame_unit_row_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    artifacts = run.get("output_artifacts")
    mao = artifacts.get(".mao") if isinstance(artifacts, dict) else {}
    terminal = mao.get("terminal_record") if isinstance(mao, dict) else {}
    terminal = terminal if isinstance(terminal, dict) else {}
    job_generation = str(identity.get("job_generation", ""))
    sweep_generation = str(identity.get("sweep_generation", ""))
    frame = str(identity.get("force_frame", ""))
    unit = str(identity.get("force_unit", ""))
    row_keys = identity.get("row_keys")
    digest = str(identity.get("position_force_table_sha256", "")).lower()
    try:
        positions = [float(value) for value in identity.get("positions_m", [])]
        result_positions = [
            float(value) for value in identity.get("result_positions_m", [])
        ]
        force_rows = [
            [float(value) for value in row]
            for row in identity.get("force_rows", [])
        ]
        result_force_rows = [
            [float(value) for value in row]
            for row in identity.get("result_force_rows", [])
        ]
    except (TypeError, ValueError):
        positions = result_positions = []
        force_rows = result_force_rows = []
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(sweep_generation)
        and all(
            identity.get(key) == sweep_generation
            for key in (
                "position_key_sweep_generation",
                "force_frame_sweep_generation",
                "unit_sweep_generation",
                "row_order_sweep_generation",
            )
        )
        and len(positions) >= 3
        and all(math.isfinite(value) for value in positions)
        and all(right > left for left, right in zip(positions, positions[1:]))
        and result_positions == positions
        and isinstance(row_keys, list)
        and len(row_keys) == len(positions)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in row_keys
        )
        and len(set(row_keys)) == len(row_keys)
        and identity.get("result_row_keys") == row_keys
        and frame in {"global_xyz", "local_xyz"}
        and identity.get("result_force_frame") == frame
        and unit in {"N", "kN"}
        and identity.get("result_force_unit") == unit
        and len(force_rows) == len(positions)
        and all(
            len(row) == 3 and all(math.isfinite(value) for value in row)
            for row in force_rows
        )
        and result_force_rows == force_rows
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("result_position_force_table_sha256", "")).lower()
        == digest
    )


def _mao_case_result_matches_generation(run: dict) -> bool:
    identity = run.get(
        "mao_case_model_version_calculation_revision_generation_identity"
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
    case_generation = str(identity.get("case_generation", ""))
    model_digest = str(identity.get("case_model_sha256", "")).lower()
    version = str(identity.get("product_version", "")).strip()
    revision = str(identity.get("calculation_revision", "")).strip()
    table_digest = str(identity.get("mao_case_table_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(case_generation)
        and all(
            identity.get(key) == case_generation
            for key in (
                "model_case_generation",
                "product_version_case_generation",
                "calculation_revision_case_generation",
                "completion_case_generation",
            )
        )
        and re.fullmatch(r"[0-9a-f]{64}", model_digest) is not None
        and str(identity.get("result_case_model_sha256", "")).lower()
        == model_digest
        and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", version) is not None
        and identity.get("result_product_version") == version
        and bool(revision)
        and identity.get("result_calculation_revision") == revision
        and identity.get("result_complete") is True
        and identity.get("parsed_result_complete") is True
        and re.fullmatch(r"[0-9a-f]{64}", table_digest) is not None
        and str(identity.get("parsed_mao_case_table_sha256", "")).lower()
        == table_digest
    )


def _mesh_result_matches_entity_map_generation(run: dict) -> bool:
    identity = run.get(
        "mesh_result_entity_count_material_map_solve_generation_identity"
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
    solve_generation = str(identity.get("solve_generation", ""))
    counts = identity.get("entity_counts")
    material_map = identity.get("material_region_map")
    frame = str(identity.get("coordinate_frame", "")).strip()
    mesh_digest = str(identity.get("mesh_sha256", "")).lower()
    result_digest = str(identity.get("result_table_sha256", "")).lower()
    counts_ok = (
        isinstance(counts, dict)
        and set(counts) == {"nodes", "elements", "regions"}
        and all(
            isinstance(value, int) and not isinstance(value, bool) and value > 0
            for value in counts.values()
        )
    )
    map_ok = (
        isinstance(material_map, list)
        and bool(material_map)
        and all(
            isinstance(row, list)
            and len(row) == 2
            and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
                for value in row
            )
            for row in material_map
        )
        and len({row[0] for row in material_map}) == len(material_map)
    )
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(solve_generation)
        and all(
            identity.get(key) == solve_generation
            for key in (
                "mesh_entity_solve_generation",
                "result_entity_solve_generation",
                "material_map_solve_generation",
                "coordinate_frame_solve_generation",
            )
        )
        and counts_ok
        and identity.get("result_entity_counts") == counts
        and map_ok
        and identity.get("result_material_region_map") == material_map
        and frame in {"global_xyz", "local_xyz", "rotor_dq"}
        and identity.get("result_coordinate_frame") == frame
        and re.fullmatch(r"[0-9a-f]{64}", mesh_digest) is not None
        and str(identity.get("result_mesh_sha256", "")).lower() == mesh_digest
        and re.fullmatch(r"[0-9a-f]{64}", result_digest) is not None
        and str(identity.get("parsed_result_table_sha256", "")).lower()
        == result_digest
    )


def _force_method_profile_matches_generation(run: dict) -> bool:
    identity = run.get(
        "force_method_profile_selection_surface_nodal_frame_result_generation_identity"
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
    generation = str(identity.get("force_profile_generation", ""))
    method = str(identity.get("force_method", "")).strip()
    selection_ids = identity.get("selection_scope_ids")
    surface_ids = identity.get("surface_ids")
    nodal_ids = identity.get("nodal_ids")
    frame = str(identity.get("component_frame", "")).strip()
    try:
        force = [float(item) for item in identity.get("force_vector_n", [])]
        result_force = [
            float(item) for item in identity.get("result_force_vector_n", [])
        ]
    except (TypeError, ValueError):
        return False
    digest = str(identity.get("force_profile_sha256", "")).lower()

    def positive_unique_ids(value: object) -> bool:
        return (
            isinstance(value, list)
            and bool(value)
            and all(
                isinstance(item, int) and not isinstance(item, bool) and item > 0
                for item in value
            )
            and len(set(value)) == len(value)
        )

    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "method_force_profile_generation",
                "selection_force_profile_generation",
                "surface_force_profile_generation",
                "nodal_force_profile_generation",
                "frame_force_profile_generation",
                "result_force_profile_generation",
            )
        )
        and method in {"virtual_work", "maxwell_stress", "nodal_force"}
        and identity.get("result_force_method") == method
        and positive_unique_ids(selection_ids)
        and identity.get("result_selection_scope_ids") == selection_ids
        and positive_unique_ids(surface_ids)
        and identity.get("result_surface_ids") == surface_ids
        and positive_unique_ids(nodal_ids)
        and identity.get("result_nodal_ids") == nodal_ids
        and frame in {"global_xyz", "local_xyz", "rotor_dq"}
        and identity.get("result_component_frame") == frame
        and len(force) == 3
        and all(math.isfinite(item) for item in force)
        and result_force == force
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("result_force_profile_sha256", "")).lower()
        == digest
    )


def _headless_result_finalization_matches_generation(run: dict) -> bool:
    identity = run.get(
        "headless_completion_dialog_exit_lock_log_final_artifact_generation_identity"
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
    generation = str(identity.get("headless_generation", ""))
    marker = str(identity.get("completion_log_marker", "")).strip()
    digest = str(identity.get("final_artifact_sha256", "")).lower()
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "dialog_headless_generation",
                "process_exit_headless_generation",
                "result_lock_headless_generation",
                "completion_log_headless_generation",
                "final_artifact_headless_generation",
            )
        )
        and identity.get("headless") is True
        and identity.get("modal_completion_dialog_shown") is False
        and identity.get("process_exited") is True
        and identity.get("process_exit_code") == 0
        and identity.get("result_lock_present") is False
        and bool(marker)
        and identity.get("parsed_completion_log_marker") == marker
        and identity.get("final_artifact_exists") is True
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("accepted_final_artifact_sha256", "")).lower()
        == digest
        and identity.get("owned_process_count_after") == 0
    )


def _result_manifest_matches_generation(run: dict) -> bool:
    identity = run.get(
        "result_manifest_component_column_unit_row_job_model_generation_identity"
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
    generation = str(identity.get("result_generation", ""))
    frame = str(identity.get("component_frame", ""))
    columns = identity.get("column_names")
    units = identity.get("column_units")
    row_ids = identity.get("row_ids")
    model_digest = str(identity.get("model_sha256", "")).lower()
    manifest_digest = str(identity.get("result_manifest_sha256", "")).lower()
    columns_ok = (
        isinstance(columns, list)
        and len(columns) >= 2
        and columns[0] == "row_id"
        and all(isinstance(item, str) and bool(item) for item in columns)
        and len(set(columns)) == len(columns)
    )
    units_ok = (
        isinstance(units, list)
        and columns_ok
        and len(units) == len(columns)
        and all(unit in {"1", "N", "N/m", "N m"} for unit in units)
        and units[0] == "1"
    )
    rows_ok = (
        isinstance(row_ids, list)
        and bool(row_ids)
        and all(
            isinstance(item, int) and not isinstance(item, bool) and item >= 0
            for item in row_ids
        )
        and row_ids == sorted(set(row_ids))
    )
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "component_result_generation",
                "column_result_generation",
                "unit_result_generation",
                "row_result_generation",
                "model_result_generation",
                "manifest_result_generation",
            )
        )
        and frame in {"global_xyz", "local_xyz", "rotor_dq"}
        and identity.get("result_component_frame") == frame
        and columns_ok
        and identity.get("parsed_column_names") == columns
        and units_ok
        and identity.get("parsed_column_units") == units
        and rows_ok
        and identity.get("parsed_row_ids") == row_ids
        and re.fullmatch(r"[0-9a-f]{64}", model_digest) is not None
        and str(identity.get("result_model_sha256", "")).lower() == model_digest
        and re.fullmatch(r"[0-9a-f]{64}", manifest_digest) is not None
        and str(identity.get("parsed_result_manifest_sha256", "")).lower()
        == manifest_digest
    )


def _public_artifact_manifest_is_bounded(run: dict) -> bool:
    identity = run.get(
        "public_artifact_root_schema_observable_allowlist_redaction_generation_identity"
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
    generation = str(identity.get("manifest_generation", ""))
    relative_path = str(identity.get("relative_artifact_path", ""))
    allowlist = identity.get("observable_allowlist")
    returned = identity.get("returned_observable_keys")
    redacted = identity.get("redacted_field_names")
    digest = str(identity.get("public_manifest_sha256", "")).lower()
    known_observables = {"force_vector_n", "torque_n_m", "demag_margin_ratio"}
    allowlist_ok = (
        isinstance(allowlist, list)
        and bool(allowlist)
        and all(isinstance(item, str) and item in known_observables for item in allowlist)
        and len(set(allowlist)) == len(allowlist)
    )
    returned_ok = (
        isinstance(returned, list)
        and allowlist_ok
        and all(isinstance(item, str) and item in allowlist for item in returned)
        and len(set(returned)) == len(returned)
    )
    redacted_ok = (
        isinstance(redacted, list)
        and {"api_token", "license_key", "local_path"}.issubset(set(redacted))
        and identity.get("result_redacted_field_names") == redacted
    )
    path_ok = (
        bool(relative_path)
        and not relative_path.startswith(("/", "\\"))
        and ":" not in relative_path
        and "\\" not in relative_path
        and ".." not in relative_path.split("/")
        and relative_path.endswith(".json")
    )
    return (
        bool(job_generation)
        and terminal.get("job_generation") == job_generation
        and identity.get("result_job_generation") == job_generation
        and bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "root_manifest_generation",
                "schema_manifest_generation",
                "allowlist_manifest_generation",
                "redaction_manifest_generation",
                "result_manifest_generation",
            )
        )
        and identity.get("artifact_root_id") == "public_package_artifacts"
        and identity.get("result_artifact_root_id")
        == identity.get("artifact_root_id")
        and path_ok
        and identity.get("result_relative_artifact_path") == relative_path
        and identity.get("public_schema") == "elf-public-result-manifest/v1"
        and identity.get("result_public_schema") == identity.get("public_schema")
        and allowlist_ok
        and returned_ok
        and redacted_ok
        and identity.get("redaction_applied") is True
        and identity.get("sensitive_fields_present") == []
        and re.fullmatch(r"[0-9a-f]{64}", digest) is not None
        and str(identity.get("result_public_manifest_sha256", "")).lower()
        == digest
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


def _document_index_identity_ok(run: dict) -> bool:
    identity = run.get(
        "document_index_release_section_anchor_topic_checksum_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("index_generation", "")).strip()
    release = str(identity.get("document_release", "")).strip()
    sections = identity.get("section_ids")
    anchors = identity.get("section_anchors")
    topics = identity.get("topic_ids")
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "release_index_generation", "section_index_generation", "anchor_index_generation",
            "topic_index_generation", "checksum_index_generation", "result_index_generation"))
        and bool(release) and identity.get("result_document_release") == release
        and isinstance(sections, list) and bool(sections)
        and all(isinstance(item, str) and item.strip() for item in sections)
        and len(set(sections)) == len(sections) and identity.get("result_section_ids") == sections
        and isinstance(anchors, list) and len(anchors) == len(sections)
        and all(isinstance(item, str) and item.strip() for item in anchors)
        and len(set(anchors)) == len(anchors) and identity.get("result_section_anchors") == anchors
        and isinstance(topics, list) and bool(topics)
        and all(isinstance(item, str) and item.strip() for item in topics)
        and len(set(topics)) == len(topics) and identity.get("result_topic_ids") == topics
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("document_sha256", "")).lower()) is not None
        and identity.get("indexed_document_sha256") == identity.get("document_sha256")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("index_sha256", "")).lower()) is not None
        and identity.get("result_index_sha256") == identity.get("index_sha256")
    )


def _public_query_identity_ok(run: dict) -> bool:
    identity = run.get(
        "query_category_schema_doc_version_observable_redaction_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("query_generation", "")).strip()
    category = str(identity.get("category", "")).strip()
    version = str(identity.get("document_version", "")).strip()
    allowlist = identity.get("observable_allowlist")
    returned = identity.get("returned_observable_keys")
    redacted = identity.get("redacted_field_names")
    known_observables = {"force_vector_n", "torque_n_m", "method_name", "demag_margin_ratio"}
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "category_query_generation", "schema_query_generation", "document_query_generation",
            "allowlist_query_generation", "redaction_query_generation", "result_query_generation"))
        and category in {"force_methods", "torque_methods", "demagnetization", "maglev"}
        and identity.get("result_category") == category
        and identity.get("query_schema") == "elf-public-query/v1"
        and identity.get("result_query_schema") == "elf-public-query/v1"
        and bool(version) and identity.get("result_document_version") == version
        and isinstance(allowlist, list) and bool(allowlist)
        and all(isinstance(item, str) and item in known_observables for item in allowlist)
        and len(set(allowlist)) == len(allowlist)
        and isinstance(returned, list) and all(item in allowlist for item in returned)
        and len(set(returned)) == len(returned)
        and isinstance(redacted, list)
        and {"api_token", "license_key", "local_path"}.issubset(set(redacted))
        and identity.get("result_redacted_field_names") == redacted
        and identity.get("redaction_applied") is True
        and identity.get("sensitive_fields_present") == []
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("result_sha256", "")).lower()) is not None
        and identity.get("accepted_result_sha256") == identity.get("result_sha256")
    )


def _document_evidence_identity_ok(run: dict) -> bool:
    identity = run.get(
        "document_edition_language_page_figure_table_anchor_checksum_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("evidence_generation", "")).strip()
    document_id = str(identity.get("document_id", "")).strip()
    edition = str(identity.get("edition", "")).strip()
    language = str(identity.get("language", "")).strip().lower()
    pages = identity.get("page_numbers")
    figures = identity.get("figure_ids")
    tables = identity.get("table_ids")
    anchors = identity.get("anchors")

    def unique_strings(value: object) -> bool:
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and item.strip() for item in value)
            and len(set(value)) == len(value)
        )

    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "edition_evidence_generation",
                "language_evidence_generation",
                "page_evidence_generation",
                "figure_evidence_generation",
                "table_evidence_generation",
                "anchor_evidence_generation",
                "checksum_evidence_generation",
                "result_evidence_generation",
            )
        )
        and bool(document_id)
        and identity.get("result_document_id") == document_id
        and bool(edition)
        and identity.get("result_edition") == edition
        and language in {"en", "ja"}
        and str(identity.get("result_language", "")).lower() == language
        and isinstance(pages, list)
        and bool(pages)
        and all(isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in pages)
        and len(set(pages)) == len(pages)
        and identity.get("result_page_numbers") == pages
        and unique_strings(figures)
        and identity.get("result_figure_ids") == figures
        and unique_strings(tables)
        and identity.get("result_table_ids") == tables
        and unique_strings(anchors)
        and identity.get("result_anchors") == anchors
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("document_sha256", "")).lower())
        is not None
        and identity.get("indexed_document_sha256") == identity.get("document_sha256")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("evidence_sha256", "")).lower())
        is not None
        and identity.get("accepted_evidence_sha256") == identity.get("evidence_sha256")
    )


def _public_query_citation_identity_ok(run: dict) -> bool:
    identity = run.get(
        "public_query_synonym_topic_category_version_citation_redaction_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("public_query_generation", "")).strip()
    query_term = str(identity.get("query_term", "")).strip()
    synonyms = identity.get("synonym_terms")
    resolved = str(identity.get("resolved_query_term", "")).strip()
    topic = str(identity.get("canonical_topic", "")).strip()
    category = str(identity.get("category", "")).strip()
    version = str(identity.get("document_version", "")).strip()
    citations = identity.get("citation_allowlist")
    returned = identity.get("returned_citation_ids")
    redacted = identity.get("redacted_field_names")
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "synonym_public_query_generation",
                "topic_public_query_generation",
                "category_public_query_generation",
                "version_public_query_generation",
                "citation_public_query_generation",
                "redaction_public_query_generation",
                "result_public_query_generation",
            )
        )
        and bool(query_term)
        and isinstance(synonyms, list)
        and bool(synonyms)
        and all(isinstance(item, str) and item.strip() for item in synonyms)
        and len(set(synonyms)) == len(synonyms)
        and resolved in {query_term, *synonyms}
        and bool(topic)
        and identity.get("result_canonical_topic") == topic
        and category in {"force_methods", "torque_methods", "demagnetization", "maglev"}
        and identity.get("result_category") == category
        and bool(version)
        and identity.get("result_document_version") == version
        and isinstance(citations, list)
        and bool(citations)
        and all(isinstance(item, str) and item.startswith("doc-") for item in citations)
        and len(set(citations)) == len(citations)
        and isinstance(returned, list)
        and bool(returned)
        and all(item in citations for item in returned)
        and len(set(returned)) == len(returned)
        and isinstance(redacted, list)
        and {"api_token", "license_key", "local_path"}.issubset(set(redacted))
        and identity.get("result_redacted_field_names") == redacted
        and identity.get("redaction_applied") is True
        and identity.get("sensitive_fields_present") == []
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("query_sha256", "")).lower())
        is not None
        and identity.get("result_query_sha256") == identity.get("query_sha256")
    )


def _document_glossary_identity_ok(run: dict) -> bool:
    identity = run.get(
        "document_glossary_alias_command_category_version_anchor_redaction_digest_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("glossary_generation", "")).strip()
    term = str(identity.get("glossary_term", "")).strip()
    aliases = identity.get("alias_terms")
    category = str(identity.get("command_category", "")).strip()
    version = str(identity.get("document_version", "")).strip()
    anchor = str(identity.get("section_anchor", "")).strip()
    redacted = identity.get("redacted_field_names")
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "alias_glossary_generation",
                "category_glossary_generation",
                "version_glossary_generation",
                "anchor_glossary_generation",
                "redaction_glossary_generation",
                "document_glossary_generation",
                "result_glossary_generation",
            )
        )
        and bool(term)
        and identity.get("result_glossary_term") == term
        and isinstance(aliases, list)
        and bool(aliases)
        and all(isinstance(item, str) and item.strip() for item in aliases)
        and len(set(aliases)) == len(aliases)
        and identity.get("resolved_alias_terms") == aliases
        and category in {
            "preprocessing-material",
            "preprocessing-winding",
            "postprocessing-force",
            "postprocessing-torque",
        }
        and identity.get("result_command_category") == category
        and bool(version)
        and identity.get("result_document_version") == version
        and bool(anchor)
        and identity.get("result_section_anchor") == anchor
        and isinstance(redacted, list)
        and {"api_token", "license_key", "local_path"}.issubset(set(redacted))
        and identity.get("result_redacted_field_names") == redacted
        and identity.get("redaction_applied") is True
        and identity.get("sensitive_fields_present") == []
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("document_sha256", "")).lower()
        )
        is not None
        and identity.get("indexed_document_sha256") == identity.get("document_sha256")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _bibliography_evidence_identity_ok(run: dict) -> bool:
    identity = run.get(
        "bibliography_citation_doi_edition_page_figure_allowlist_checksum_generation_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("bibliography_generation", "")).strip()
    bibliography_id = str(identity.get("bibliography_id", "")).strip()
    citation = str(identity.get("citation_text", "")).strip()
    doi = str(identity.get("doi", "")).strip().lower()
    edition = str(identity.get("edition", "")).strip()
    pages = identity.get("page_numbers")
    figures = identity.get("figure_ids")
    allowlist = identity.get("citation_allowlist")
    returned = identity.get("returned_citation_ids")
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "citation_bibliography_generation",
                "doi_bibliography_generation",
                "edition_bibliography_generation",
                "page_bibliography_generation",
                "figure_bibliography_generation",
                "allowlist_bibliography_generation",
                "checksum_bibliography_generation",
                "result_bibliography_generation",
            )
        )
        and bibliography_id.startswith("public-")
        and identity.get("result_bibliography_id") == bibliography_id
        and bool(citation)
        and identity.get("result_citation_text") == citation
        and re.fullmatch(r"10\.\d{4,9}/\S+", doi) is not None
        and str(identity.get("result_doi", "")).lower() == doi
        and bool(edition)
        and identity.get("result_edition") == edition
        and isinstance(pages, list)
        and bool(pages)
        and all(
            isinstance(item, int) and not isinstance(item, bool) and item > 0
            for item in pages
        )
        and len(set(pages)) == len(pages)
        and identity.get("result_page_numbers") == pages
        and isinstance(figures, list)
        and bool(figures)
        and all(isinstance(item, str) and item.strip() for item in figures)
        and len(set(figures)) == len(figures)
        and identity.get("result_figure_ids") == figures
        and isinstance(allowlist, list)
        and bibliography_id in allowlist
        and len(set(allowlist)) == len(allowlist)
        and isinstance(returned, list)
        and bool(returned)
        and all(item in allowlist for item in returned)
        and len(set(returned)) == len(returned)
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("source_sha256", "")).lower()
        )
        is not None
        and identity.get("indexed_source_sha256") == identity.get("source_sha256")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("evidence_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_evidence_sha256") == identity.get("evidence_sha256")
    )


def _command_option_schema_identity_ok(run: dict) -> bool:
    identity = run.get("command_option_schema_document_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("command_generation", "")).strip()
    command = str(identity.get("command_name", "")).strip()
    options = identity.get("option_names")
    defaults = identity.get("default_values")
    enum_values = identity.get("enum_values")
    units = identity.get("unit_symbols")
    version = str(identity.get("document_version", "")).strip()
    anchor = str(identity.get("section_anchor", "")).strip()
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "option_command_generation", "default_command_generation",
            "enum_command_generation", "unit_command_generation",
            "document_command_generation", "anchor_command_generation",
            "result_command_generation"))
        and bool(command) and identity.get("result_command_name") == command
        and isinstance(options, list) and bool(options)
        and len(set(options)) == len(options)
        and all(isinstance(item, str) and item.strip() for item in options)
        and identity.get("result_option_names") == options
        and isinstance(defaults, dict) and set(defaults).issubset(set(options))
        and identity.get("result_default_values") == defaults
        and isinstance(enum_values, dict) and set(enum_values).issubset(set(options))
        and all(isinstance(values, list) and values for values in enum_values.values())
        and identity.get("result_enum_values") == enum_values
        and isinstance(units, dict) and set(units).issubset(set(options))
        and all(isinstance(item, str) and item.strip() for item in units.values())
        and identity.get("result_unit_symbols") == units
        and bool(version) and identity.get("result_document_version") == version
        and bool(anchor) and identity.get("result_section_anchor") == anchor
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("document_sha256", "")).lower()) is not None
        and identity.get("indexed_document_sha256") == identity.get("document_sha256")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()) is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _mao_section_schema_identity_ok(run: dict) -> bool:
    identity = run.get("mao_section_header_column_unit_locale_row_owner_generation_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("mao_generation", "")).strip()
    header = str(identity.get("section_header", "")).strip()
    columns = identity.get("column_names")
    units = identity.get("unit_symbols")
    owner = str(identity.get("section_owner_id", "")).strip()
    try:
        row_count = int(identity.get("row_count"))
        parsed_row_count = int(identity.get("parsed_row_count"))
        rows = [[float(item) for item in row] for row in identity.get("rows", [])]
        parsed_rows = [[float(item) for item in row] for row in identity.get("parsed_rows", [])]
    except (TypeError, ValueError):
        return False
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "header_mao_generation", "column_mao_generation", "unit_mao_generation",
            "locale_mao_generation", "row_mao_generation", "owner_mao_generation",
            "result_mao_generation"))
        and bool(header) and identity.get("parsed_section_header") == header
        and isinstance(columns, list) and bool(columns)
        and len(set(columns)) == len(columns)
        and all(isinstance(item, str) and item.strip() for item in columns)
        and identity.get("parsed_column_names") == columns
        and isinstance(units, list) and len(units) == len(columns)
        and all(isinstance(item, str) and item.strip() for item in units)
        and identity.get("parsed_unit_symbols") == units
        and identity.get("numeric_locale") == "C-dot"
        and identity.get("parsed_numeric_locale") == "C-dot"
        and row_count >= 1 and parsed_row_count == row_count
        and len(rows) == row_count
        and all(len(row) == len(columns) for row in rows)
        and all(math.isfinite(item) for row in rows for item in row)
        and parsed_rows == rows
        and bool(owner) and identity.get("parsed_section_owner_id") == owner
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("section_sha256", "")).lower()) is not None
        and identity.get("parsed_section_sha256") == identity.get("section_sha256")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("result_sha256", "")).lower()) is not None
        and identity.get("accepted_result_sha256") == identity.get("result_sha256")
    )


def _command_alias_platform_identity_ok(run: dict) -> bool:
    identity = run.get("command_alias_platform_option_version_anchor_document_digest_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("command_generation", "")).strip()
    command = str(identity.get("canonical_command", "")).strip()
    aliases = identity.get("command_aliases")
    options = identity.get("available_options")
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "alias_command_generation", "platform_command_generation", "option_command_generation",
            "version_command_generation", "anchor_command_generation", "document_command_generation",
            "result_command_generation"))
        and bool(command) and identity.get("resolved_canonical_command") == command
        and isinstance(aliases, list) and bool(aliases) and len(set(aliases)) == len(aliases)
        and all(isinstance(item, str) and item.strip() for item in aliases)
        and identity.get("resolved_command_aliases") == aliases
        and identity.get("platform") == "windows-x64"
        and identity.get("resolved_platform") == "windows-x64"
        and isinstance(options, list) and bool(options) and len(set(options)) == len(options)
        and identity.get("resolved_available_options") == options
        and bool(identity.get("product_version"))
        and identity.get("resolved_product_version") == identity.get("product_version")
        and bool(identity.get("section_anchor"))
        and identity.get("resolved_section_anchor") == identity.get("section_anchor")
        and bool(identity.get("document_owner"))
        and identity.get("resolved_document_owner") == identity.get("document_owner")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("document_sha256", "")).lower()) is not None
        and identity.get("indexed_document_sha256") == identity.get("document_sha256")
    )


def _mao_vector_schema_identity_ok(run: dict) -> bool:
    identity = run.get("mao_vector_component_frame_unit_point_owner_digest_identity")
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("mao_generation", "")).strip()
    components = identity.get("component_order")
    units = identity.get("unit_symbols")
    points = identity.get("point_ids")
    try:
        vectors = [[float(item) for item in row] for row in identity.get("vectors", [])]
        parsed_vectors = [[float(item) for item in row] for row in identity.get("parsed_vectors", [])]
    except (TypeError, ValueError):
        return False
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "component_mao_generation", "frame_mao_generation", "unit_mao_generation",
            "point_mao_generation", "owner_mao_generation", "digest_mao_generation",
            "result_mao_generation"))
        and components == ["x", "y", "z"] and identity.get("parsed_component_order") == components
        and identity.get("coordinate_frame") == "global_cartesian"
        and identity.get("parsed_coordinate_frame") == "global_cartesian"
        and units == ["N", "N", "N"] and identity.get("parsed_unit_symbols") == units
        and isinstance(points, list) and bool(points) and len(set(points)) == len(points)
        and all(isinstance(item, int) and item > 0 for item in points)
        and identity.get("parsed_point_ids") == points
        and len(vectors) == len(points) and all(len(row) == 3 for row in vectors)
        and all(math.isfinite(item) for row in vectors for item in row)
        and parsed_vectors == vectors
        and bool(identity.get("section_owner_id"))
        and identity.get("parsed_section_owner_id") == identity.get("section_owner_id")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("section_sha256", "")).lower()) is not None
        and identity.get("parsed_section_sha256") == identity.get("section_sha256")
    )


def _mao_record_schema_identity_ok(run: dict) -> bool:
    identity = run.get("mao_record_schema_endian_offset_model_observable_unit_file_digest_identity")
    if identity is None: return True
    if not isinstance(identity, dict): return False
    generation = str(identity.get("mao_generation", "")).strip()
    return (
        bool(generation) and all(identity.get(key) == generation for key in ("schema_mao_generation", "endian_mao_generation", "offset_mao_generation", "model_mao_generation", "observable_mao_generation", "unit_mao_generation", "digest_mao_generation", "result_mao_generation"))
        and identity.get("record_schema") == "mao-result-v6" and identity.get("parsed_record_schema") == identity.get("record_schema")
        and identity.get("byte_order") == "little" and identity.get("parsed_byte_order") == "little"
        and isinstance(identity.get("record_offset_bytes"), int) and identity.get("record_offset_bytes") >= 0 and identity.get("parsed_record_offset_bytes") == identity.get("record_offset_bytes")
        and bool(identity.get("model_generation")) and identity.get("parsed_model_generation") == identity.get("model_generation")
        and bool(identity.get("observable_owner")) and identity.get("parsed_observable_owner") == identity.get("observable_owner")
        and isinstance(identity.get("unit_metadata"), dict) and bool(identity.get("unit_metadata")) and identity.get("parsed_unit_metadata") == identity.get("unit_metadata")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("file_sha256", "")).lower()) is not None
        and identity.get("parsed_file_sha256") == identity.get("file_sha256")
    )


def _solver_result_lineage_identity_ok(run: dict) -> bool:
    identity = run.get("solver_entitlement_session_model_run_completion_result_lineage_identity")
    if identity is None: return True
    if not isinstance(identity, dict): return False
    generation = str(identity.get("lineage_generation", "")).strip()
    return (
        bool(generation) and all(identity.get(key) == generation for key in ("session_lineage_generation", "model_lineage_generation", "run_lineage_generation", "completion_lineage_generation", "result_lineage_generation", "digest_lineage_generation"))
        and isinstance(identity.get("entitlement_present"), bool) and isinstance(identity.get("dongle_present"), bool)
        and identity.get("entitlement_is_result_provenance") is False
        and bool(identity.get("solver_session_id")) and identity.get("result_solver_session_id") == identity.get("solver_session_id")
        and bool(identity.get("model_owner")) and identity.get("result_model_owner") == identity.get("model_owner")
        and bool(identity.get("run_owner")) and identity.get("result_run_owner") == identity.get("run_owner")
        and identity.get("completion_marker") == "completed" and identity.get("result_completion_marker") == "completed"
        and bool(identity.get("result_generation")) and identity.get("accepted_result_generation") == identity.get("result_generation")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("artifact_sha256", "")).lower()) is not None
        and identity.get("accepted_artifact_sha256") == identity.get("artifact_sha256")
    )


def _mag_block_record_identity_ok(run: dict) -> bool:
    identity = run.get(
        "mag_block_schema_endian_index_connectivity_material_offset_model_checksum_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("mag_generation", "")).strip()
    connectivity = identity.get("connectivity")
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "schema_mag_generation",
                "endian_mag_generation",
                "index_mag_generation",
                "connectivity_mag_generation",
                "material_mag_generation",
                "offset_mag_generation",
                "model_mag_generation",
                "result_mag_generation",
            )
        )
        and identity.get("record_schema") == "mag-model-block-v6"
        and identity.get("parsed_record_schema") == identity.get("record_schema")
        and identity.get("byte_order") == "little"
        and identity.get("parsed_byte_order") == "little"
        and identity.get("index_base") == 0
        and identity.get("parsed_index_base") == 0
        and isinstance(connectivity, list)
        and len(connectivity) >= 4
        and all(isinstance(item, int) and item >= 0 for item in connectivity)
        and len(set(connectivity)) == len(connectivity)
        and identity.get("parsed_connectivity") == connectivity
        and isinstance(identity.get("material_id"), int)
        and identity.get("material_id") >= 0
        and identity.get("parsed_material_id") == identity.get("material_id")
        and isinstance(identity.get("block_offset_bytes"), int)
        and identity.get("block_offset_bytes") >= 0
        and identity.get("parsed_block_offset_bytes")
        == identity.get("block_offset_bytes")
        and bool(str(identity.get("model_generation", "")).strip())
        and identity.get("parsed_model_generation") == identity.get("model_generation")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("file_sha256", "")).lower()
        )
        is not None
        and identity.get("parsed_file_sha256") == identity.get("file_sha256")
    )


def _mao_stepped_parameter_table_identity_ok(run: dict) -> bool:
    identity = run.get(
        "mao_stepped_parameter_tuple_row_convergence_unit_owner_count_digest_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("step_generation", "")).strip()
    names = identity.get("parameter_names")
    tuples = identity.get("parameter_tuples")
    row_order = identity.get("row_order")
    converged = identity.get("converged")
    if not (
        isinstance(names, list)
        and names
        and all(isinstance(item, str) and item.strip() for item in names)
        and len(set(names)) == len(names)
        and isinstance(tuples, list)
        and tuples
        and all(isinstance(row, list) and len(row) == len(names) for row in tuples)
    ):
        return False
    try:
        numeric_tuples = [[float(item) for item in row] for row in tuples]
    except (TypeError, ValueError):
        return False
    row_count = len(numeric_tuples)
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "tuple_step_generation",
                "row_step_generation",
                "convergence_step_generation",
                "unit_step_generation",
                "owner_step_generation",
                "count_step_generation",
                "digest_step_generation",
                "result_step_generation",
            )
        )
        and identity.get("parsed_parameter_names") == names
        and all(math.isfinite(item) for row in numeric_tuples for item in row)
        and identity.get("parsed_parameter_tuples") == numeric_tuples
        and row_order == list(range(row_count))
        and identity.get("parsed_row_order") == row_order
        and isinstance(converged, list)
        and len(converged) == row_count
        and all(item is True for item in converged)
        and identity.get("parsed_converged") == converged
        and bool(str(identity.get("observable_unit", "")).strip())
        and identity.get("parsed_observable_unit") == identity.get("observable_unit")
        and bool(str(identity.get("model_owner", "")).strip())
        and identity.get("parsed_model_owner") == identity.get("model_owner")
        and bool(str(identity.get("run_owner", "")).strip())
        and identity.get("parsed_run_owner") == identity.get("run_owner")
        and identity.get("row_count") == row_count
        and identity.get("parsed_row_count") == row_count
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("artifact_sha256", "")).lower()
        )
        is not None
        and identity.get("parsed_artifact_sha256")
        == identity.get("artifact_sha256")
    )


def _mag_material_variable_record_identity_ok(run: dict) -> bool:
    identity = run.get(
        "mag_material_variable_record_offset_count_unit_bh_order_material_crc_model_file_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("material_generation", "")).strip()
    try:
        offsets = [int(item) for item in identity.get("record_offsets_bytes", [])]
        parsed_offsets = [
            int(item) for item in identity.get("parsed_record_offsets_bytes", [])
        ]
        point_count = int(identity.get("point_count"))
        parsed_point_count = int(identity.get("parsed_point_count"))
        points = [
            [float(item) for item in row] for row in identity.get("bh_points", [])
        ]
        parsed_points = [
            [float(item) for item in row]
            for row in identity.get("parsed_bh_points", [])
        ]
        material_id = int(identity.get("material_id"))
        parsed_material_id = int(identity.get("parsed_material_id"))
    except (TypeError, ValueError):
        return False
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "offset_generation",
                "count_generation",
                "unit_generation",
                "bh_generation",
                "order_generation",
                "index_generation",
                "crc_generation",
                "model_generation",
                "file_generation",
                "result_generation",
            )
        )
        and len(offsets) == point_count
        and point_count >= 2
        and offsets[0] >= 0
        and all(left < right for left, right in zip(offsets, offsets[1:]))
        and parsed_offsets == offsets
        and parsed_point_count == point_count
        and identity.get("field_unit") == "A/m"
        and identity.get("parsed_field_unit") == identity.get("field_unit")
        and identity.get("flux_density_unit") == "T"
        and identity.get("parsed_flux_density_unit")
        == identity.get("flux_density_unit")
        and len(points) == point_count
        and all(len(row) == 2 for row in points)
        and all(math.isfinite(item) for row in points for item in row)
        and all(left[0] < right[0] for left, right in zip(points, points[1:]))
        and all(left[1] <= right[1] for left, right in zip(points, points[1:]))
        and parsed_points == points
        and material_id >= 0
        and parsed_material_id == material_id
        and re.fullmatch(
            r"[0-9a-f]{8}", str(identity.get("record_crc32", "")).lower()
        )
        is not None
        and identity.get("parsed_record_crc32") == identity.get("record_crc32")
        and bool(str(identity.get("model_generation_id", "")).strip())
        and identity.get("parsed_model_generation_id")
        == identity.get("model_generation_id")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("file_sha256", "")).lower()
        )
        is not None
        and identity.get("parsed_file_sha256") == identity.get("file_sha256")
    )


def _mao_transient_table_identity_ok(run: dict) -> bool:
    identity = run.get(
        "mao_transient_channel_header_sample_time_unit_event_completion_owner_count_digest_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("transient_generation", "")).strip()
    headers = [str(item).strip() for item in identity.get("channel_headers", [])]
    parsed_headers = [
        str(item).strip() for item in identity.get("parsed_channel_headers", [])
    ]
    units = [str(item).strip() for item in identity.get("channel_units", [])]
    parsed_units = [
        str(item).strip() for item in identity.get("parsed_channel_units", [])
    ]
    try:
        sample_times = [
            float(item) for item in identity.get("sample_times_s", [])
        ]
        parsed_sample_times = [
            float(item) for item in identity.get("parsed_sample_times_s", [])
        ]
        rows = [[float(item) for item in row] for row in identity.get("rows", [])]
        parsed_rows = [
            [float(item) for item in row] for row in identity.get("parsed_rows", [])
        ]
        event_row = int(identity.get("event_row_index"))
        parsed_event_row = int(identity.get("parsed_event_row_index"))
        row_count = int(identity.get("row_count"))
        parsed_row_count = int(identity.get("parsed_row_count"))
    except (TypeError, ValueError):
        return False
    expected_event_row = (
        max(range(len(rows)), key=lambda index: abs(rows[index][1]))
        if rows and all(len(row) >= 2 for row in rows)
        else -1
    )
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "channel_generation",
                "sample_generation",
                "unit_generation",
                "event_generation",
                "completion_generation",
                "owner_generation",
                "count_generation",
                "digest_generation",
                "result_generation",
            )
        )
        and headers == ["time", "current", "force"]
        and len(set(headers)) == len(headers)
        and parsed_headers == headers
        and units == ["s", "A", "N"]
        and parsed_units == units
        and len(sample_times) >= 3
        and all(math.isfinite(item) for item in sample_times)
        and all(
            left < right for left, right in zip(sample_times, sample_times[1:])
        )
        and parsed_sample_times == sample_times
        and len(rows) == row_count == len(sample_times)
        and all(len(row) == len(headers) for row in rows)
        and all(math.isfinite(item) for row in rows for item in row)
        and all(
            math.isclose(row[0], time, rel_tol=0.0, abs_tol=1.0e-15)
            for row, time in zip(rows, sample_times)
        )
        and parsed_rows == rows
        and event_row == expected_event_row
        and parsed_event_row == event_row
        and identity.get("solver_completed") is True
        and identity.get("parsed_solver_completed") is True
        and bool(str(identity.get("model_owner", "")).strip())
        and identity.get("parsed_model_owner") == identity.get("model_owner")
        and bool(str(identity.get("run_owner", "")).strip())
        and identity.get("parsed_run_owner") == identity.get("run_owner")
        and parsed_row_count == row_count
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("artifact_sha256", "")).lower()
        )
        is not None
        and identity.get("parsed_artifact_sha256")
        == identity.get("artifact_sha256")
    )


def _mao_table_graph_identity_ok(run: dict) -> bool:
    identity = run.get(
        "mao_table_graph_axis_unit_case_solver_version_timestamp_export_owner_digest_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("mao_view_generation", "")).strip()
    try:
        case_row = identity.get("case_row", [])
        parsed_case_row = identity.get("parsed_case_row", [])
        if len(case_row) != 3 or len(parsed_case_row) != 3:
            return False
        normalized_case_row = [
            str(case_row[0]).strip(),
            float(case_row[1]),
            float(case_row[2]),
        ]
        normalized_parsed_case_row = [
            str(parsed_case_row[0]).strip(),
            float(parsed_case_row[1]),
            float(parsed_case_row[2]),
        ]
        exported_at = datetime.fromisoformat(
            str(identity.get("exported_at_utc", "")).replace("Z", "+00:00")
        )
        parsed_exported_at = datetime.fromisoformat(
            str(identity.get("parsed_exported_at_utc", "")).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return False
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "table_generation",
                "graph_generation",
                "x_axis_generation",
                "y_axis_generation",
                "case_generation",
                "solver_generation",
                "timestamp_generation",
                "export_generation",
                "owner_generation",
                "digest_generation",
                "result_generation",
            )
        )
        and bool(str(identity.get("table_id", "")).strip())
        and identity.get("parsed_table_id") == identity.get("table_id")
        and bool(str(identity.get("graph_id", "")).strip())
        and identity.get("parsed_graph_id") == identity.get("graph_id")
        and identity.get("x_axis_name") == "position"
        and identity.get("parsed_x_axis_name") == identity.get("x_axis_name")
        and identity.get("x_axis_unit") == "mm"
        and identity.get("parsed_x_axis_unit") == identity.get("x_axis_unit")
        and identity.get("y_axis_name") == "force"
        and identity.get("parsed_y_axis_name") == identity.get("y_axis_name")
        and identity.get("y_axis_unit") == "N"
        and identity.get("parsed_y_axis_unit") == identity.get("y_axis_unit")
        and bool(normalized_case_row[0])
        and all(math.isfinite(item) for item in normalized_case_row[1:])
        and normalized_parsed_case_row == normalized_case_row
        and re.fullmatch(r"\d+\.\d+(?:\.\d+)?", str(identity.get("solver_version", "")))
        is not None
        and identity.get("parsed_solver_version") == identity.get("solver_version")
        and exported_at.tzinfo is not None
        and parsed_exported_at == exported_at
        and bool(str(identity.get("export_generation_id", "")).strip())
        and identity.get("parsed_export_generation_id")
        == identity.get("export_generation_id")
        and bool(str(identity.get("source_owner", "")).strip())
        and identity.get("parsed_source_owner") == identity.get("source_owner")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("artifact_sha256", "")).lower()
        )
        is not None
        and identity.get("parsed_artifact_sha256") == identity.get("artifact_sha256")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _document_option_identity_ok(run: dict) -> bool:
    identity = run.get(
        "document_option_enum_default_version_scope_example_revision_boundary_response_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("document_option_generation", "")).strip()
    enum_members = [str(item).strip() for item in identity.get("enum_members", [])]
    resolved_enum_members = [
        str(item).strip() for item in identity.get("resolved_enum_members", [])
    ]
    default_value = str(identity.get("default_value", "")).strip()
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "option_generation",
                "enum_generation",
                "default_generation",
                "version_generation",
                "scope_generation",
                "example_generation",
                "revision_generation",
                "boundary_generation",
                "response_generation",
            )
        )
        and bool(str(identity.get("option_name", "")).strip())
        and identity.get("resolved_option_name") == identity.get("option_name")
        and len(enum_members) >= 2
        and all(enum_members)
        and len(set(enum_members)) == len(enum_members)
        and resolved_enum_members == enum_members
        and default_value in enum_members
        and identity.get("resolved_default_value") == default_value
        and re.fullmatch(
            r"\d+\.\d+(?:\.\d+)?",
            str(identity.get("available_since_version", "")),
        )
        is not None
        and identity.get("resolved_available_since_version")
        == identity.get("available_since_version")
        and bool(str(identity.get("argument_scope", "")).strip())
        and identity.get("resolved_argument_scope") == identity.get("argument_scope")
        and re.fullmatch(
            r"[0-9a-f]{64}",
            str(identity.get("documented_example_sha256", "")).lower(),
        )
        is not None
        and identity.get("resolved_documented_example_sha256")
        == identity.get("documented_example_sha256")
        and bool(str(identity.get("documentation_revision", "")).strip())
        and identity.get("resolved_documentation_revision")
        == identity.get("documentation_revision")
        and identity.get("public_boundary") == "documentation_only"
        and identity.get("resolved_public_boundary")
        == identity.get("public_boundary")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _input_schema_identity_ok(run: dict) -> bool:
    identity = run.get(
        "input_section_continuation_encoding_unit_dependency_enum_release_owner_schema_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("input_schema_generation", "")).strip()
    sections = identity.get("section_order")
    continuations = identity.get("continuation_markers")
    release = str(identity.get("available_since_release", "")).strip()
    owner = str(identity.get("document_owner", "")).strip()
    scope = str(identity.get("enum_scope", "")).strip()
    dependency = str(identity.get("dependency_expression", "")).strip()
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "section_generation",
                "continuation_generation",
                "encoding_generation",
                "unit_generation",
                "dependency_generation",
                "enum_generation",
                "release_generation",
                "owner_generation",
                "schema_generation",
                "response_generation",
            )
        )
        and isinstance(sections, list)
        and len(sections) >= 2
        and all(isinstance(item, str) and item.strip() for item in sections)
        and len(set(sections)) == len(sections)
        and identity.get("parsed_section_order") == sections
        and isinstance(continuations, list)
        and bool(continuations)
        and len(continuations) <= 4
        and all(isinstance(item, str) and item for item in continuations)
        and len(set(continuations)) == len(continuations)
        and identity.get("parsed_continuation_markers") == continuations
        and identity.get("text_encoding") in {"utf-8", "shift_jis"}
        and identity.get("parsed_text_encoding") == identity.get("text_encoding")
        and identity.get("length_unit") in {"m", "cm", "mm"}
        and identity.get("parsed_length_unit") == identity.get("length_unit")
        and bool(str(identity.get("dependent_option", "")).strip())
        and identity.get("parsed_dependent_option") == identity.get("dependent_option")
        and bool(dependency)
        and identity.get("parsed_dependency_expression") == dependency
        and bool(scope)
        and not scope.startswith("private.")
        and identity.get("parsed_enum_scope") == scope
        and re.fullmatch(r"\d+\.\d+", release) is not None
        and identity.get("parsed_available_since_release") == release
        and bool(owner)
        and not owner.startswith("private/")
        and identity.get("parsed_document_owner") == owner
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("schema_sha256", "")).lower()
        )
        is not None
        and identity.get("parsed_schema_sha256") == identity.get("schema_sha256")
        and identity.get("public_boundary") == "documentation_only"
        and identity.get("resolved_public_boundary") == identity.get("public_boundary")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _bilingual_citation_identity_ok(run: dict) -> bool:
    identity = run.get(
        "bilingual_keyword_alias_section_page_release_scope_citation_boundary_owner_response_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("bilingual_index_generation", "")).strip()
    japanese_alias = str(identity.get("japanese_keyword_alias", "")).strip()
    english_alias = str(identity.get("english_keyword_alias", "")).strip()
    section = str(identity.get("document_section", "")).strip()
    release = str(identity.get("document_release", "")).strip()
    scope = str(identity.get("option_scope", "")).strip()
    owner = str(identity.get("source_owner", "")).strip()
    page = identity.get("document_page")
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "alias_generation",
                "section_generation",
                "page_generation",
                "release_generation",
                "scope_generation",
                "citation_generation",
                "boundary_generation",
                "owner_generation",
                "response_generation",
            )
        )
        and bool(japanese_alias)
        and bool(english_alias)
        and japanese_alias != english_alias
        and identity.get("resolved_japanese_keyword_alias") == japanese_alias
        and identity.get("resolved_english_keyword_alias") == english_alias
        and bool(section)
        and not section.startswith("private/")
        and identity.get("resolved_document_section") == section
        and isinstance(page, int)
        and not isinstance(page, bool)
        and page > 0
        and identity.get("resolved_document_page") == page
        and re.fullmatch(r"\d+\.\d+", release) is not None
        and identity.get("resolved_document_release") == release
        and bool(scope)
        and not scope.startswith("private.")
        and identity.get("resolved_option_scope") == scope
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("cited_excerpt_sha256", "")).lower()
        )
        is not None
        and identity.get("resolved_cited_excerpt_sha256")
        == identity.get("cited_excerpt_sha256")
        and identity.get("public_boundary") == "documentation_only"
        and identity.get("resolved_public_boundary") == identity.get("public_boundary")
        and bool(owner)
        and not owner.startswith("private/")
        and identity.get("resolved_source_owner") == owner
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _document_equation_identity_ok(run: dict) -> bool:
    identity = run.get(
        "document_equation_symbol_unit_sign_section_release_citation_owner_response_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("equation_generation", "")).strip()
    symbols = identity.get("symbols")
    units = identity.get("symbol_units")
    page = identity.get("document_page")
    section = str(identity.get("document_section", "")).strip()
    owner = str(identity.get("document_owner", "")).strip()
    if not isinstance(symbols, list) or not isinstance(units, list):
        return False
    unit_rows_ok = all(
        isinstance(row, list)
        and len(row) == 2
        and isinstance(row[0], str)
        and row[0].strip()
        and isinstance(row[1], str)
        and row[1].strip()
        for row in units
    )
    unit_symbols = [row[0] for row in units] if unit_rows_ok else []
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "symbol_generation",
                "unit_generation",
                "sign_generation",
                "section_generation",
                "release_generation",
                "citation_generation",
                "owner_generation",
                "response_generation",
            )
        )
        and bool(str(identity.get("equation_id", "")).strip())
        and identity.get("resolved_equation_id") == identity.get("equation_id")
        and len(symbols) >= 2
        and all(isinstance(item, str) and item.strip() for item in symbols)
        and len(set(symbols)) == len(symbols)
        and identity.get("resolved_symbols") == symbols
        and unit_rows_ok
        and len(unit_symbols) == len(symbols)
        and set(unit_symbols) == set(symbols)
        and len(set(unit_symbols)) == len(unit_symbols)
        and identity.get("resolved_symbol_units") == units
        and bool(str(identity.get("sign_convention", "")).strip())
        and identity.get("resolved_sign_convention") == identity.get("sign_convention")
        and bool(section)
        and not section.startswith("private/")
        and identity.get("resolved_document_section") == section
        and isinstance(page, int)
        and not isinstance(page, bool)
        and page > 0
        and identity.get("resolved_document_page") == page
        and re.fullmatch(r"\d+\.\d+", str(identity.get("document_release", "")))
        is not None
        and identity.get("resolved_document_release") == identity.get("document_release")
        and identity.get("release_scope") == "documentation_only"
        and identity.get("resolved_release_scope") == identity.get("release_scope")
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("citation_sha256", "")).lower()
        )
        is not None
        and identity.get("resolved_citation_sha256") == identity.get("citation_sha256")
        and bool(owner)
        and not owner.startswith("private/")
        and identity.get("resolved_document_owner") == owner
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _input_region_reference_identity_ok(run: dict) -> bool:
    identity = run.get(
        "input_region_material_source_boundary_numbering_continuation_unit_release_owner_response_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("input_generation", "")).strip()
    regions = identity.get("region_numbers")
    materials = identity.get("material_references")
    sources = identity.get("source_references")
    boundaries = identity.get("boundary_references")
    continuations = identity.get("continuation_markers")
    owner = str(identity.get("document_owner", "")).strip()
    if not isinstance(regions, list):
        return False

    def reference_rows(value: object, prefix: str) -> bool:
        return (
            isinstance(value, list)
            and bool(value)
            and all(
                isinstance(row, list)
                and len(row) == 2
                and isinstance(row[0], int)
                and not isinstance(row[0], bool)
                and row[0] in regions
                and isinstance(row[1], str)
                and row[1].startswith(prefix)
                and len(row[1]) > len(prefix)
                for row in value
            )
        )

    material_ok = reference_rows(materials, "material:")
    source_ok = reference_rows(sources, "source:")
    boundary_ok = reference_rows(boundaries, "boundary:")
    material_regions = {row[0] for row in materials} if material_ok else set()
    return (
        bool(generation)
        and all(
            identity.get(key) == generation
            for key in (
                "region_generation",
                "material_generation",
                "source_generation",
                "boundary_generation",
                "continuation_generation",
                "unit_generation",
                "release_generation",
                "owner_generation",
                "response_generation",
            )
        )
        and len(regions) >= 2
        and all(
            isinstance(item, int) and not isinstance(item, bool) and item > 0
            for item in regions
        )
        and len(set(regions)) == len(regions)
        and regions == sorted(regions)
        and identity.get("parsed_region_numbers") == regions
        and material_ok
        and material_regions == set(regions)
        and identity.get("parsed_material_references") == materials
        and source_ok
        and identity.get("parsed_source_references") == sources
        and boundary_ok
        and identity.get("parsed_boundary_references") == boundaries
        and isinstance(continuations, list)
        and bool(continuations)
        and len(continuations) <= 4
        and all(item in {"\\", "&"} for item in continuations)
        and len(set(continuations)) == len(continuations)
        and identity.get("parsed_continuation_markers") == continuations
        and identity.get("length_unit") in {"m", "cm", "mm"}
        and identity.get("parsed_length_unit") == identity.get("length_unit")
        and re.fullmatch(r"\d+\.\d+", str(identity.get("schema_release", "")))
        is not None
        and identity.get("parsed_schema_release") == identity.get("schema_release")
        and bool(owner)
        and not owner.startswith("private/")
        and identity.get("parsed_document_owner") == owner
        and re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower()
        )
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


def _mao_output_identity_ok(run: dict) -> bool:
    identity = run.get(
        "mao_output_section_record_unit_case_iteration_owner_input_output_digest_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("mao_generation", "")).strip()
    section = str(identity.get("section_name", "")).strip()
    units = identity.get("unit_convention")
    owner = str(identity.get("run_owner", "")).strip()
    try:
        record_count = int(identity.get("record_count"))
        iteration = int(identity.get("nonlinear_iteration"))
    except (TypeError, ValueError):
        return False
    mirrored = (
        "output_extension", "section_name", "record_count", "unit_convention",
        "analysis_case", "nonlinear_iteration", "run_owner", "input_sha256",
        "output_sha256",
    )
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "section_generation", "record_generation", "unit_generation",
            "case_generation", "iteration_generation", "owner_generation",
            "input_generation", "output_generation", "response_generation"))
        and identity.get("output_extension") == ".mao"
        and bool(section)
        and record_count > 0
        and isinstance(units, list)
        and len(units) >= 2
        and all(isinstance(item, str) and item.strip() for item in units)
        and bool(str(identity.get("analysis_case", "")).strip())
        and iteration >= 0
        and bool(owner)
        and not owner.startswith("private/")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("input_sha256", "")).lower())
        is not None
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("output_sha256", "")).lower())
        is not None
        and all(identity.get(f"parsed_{field}") == identity.get(field) for field in mirrored)
    )


def _document_table_identity_ok(run: dict) -> bool:
    identity = run.get(
        "document_table_interpolation_axis_order_row_column_unit_release_selected_row_owner_citation_response_identity"
    )
    if identity is None:
        return True
    if not isinstance(identity, dict):
        return False
    generation = str(identity.get("table_generation", "")).strip()
    axis = str(identity.get("interpolation_axis", "")).strip()
    order = str(identity.get("interpolation_order", "")).strip()
    owner = str(identity.get("document_owner", "")).strip()
    rows = identity.get("selected_row")
    row_ok = (
        isinstance(rows, list)
        and len(rows) >= 2
        and all(
            isinstance(row, list)
            and len(row) == 2
            and isinstance(row[0], str)
            and row[0].strip()
            and isinstance(row[1], (int, float))
            and not isinstance(row[1], bool)
            and math.isfinite(float(row[1]))
            for row in rows
        )
    )
    return (
        bool(generation)
        and all(identity.get(key) == generation for key in (
            "axis_generation", "order_generation", "unit_generation",
            "release_generation", "row_generation", "owner_generation",
            "citation_generation", "response_generation"))
        and axis.endswith("_hz")
        and identity.get("resolved_interpolation_axis") == axis
        and order in {"linear", "nearest"}
        and identity.get("resolved_interpolation_order") == order
        and identity.get("row_unit") == "Hz"
        and identity.get("resolved_row_unit") == identity.get("row_unit")
        and bool(str(identity.get("column_unit", "")).strip())
        and identity.get("resolved_column_unit") == identity.get("column_unit")
        and re.fullmatch(r"\d+\.\d+", str(identity.get("document_release", "")))
        is not None
        and identity.get("resolved_document_release") == identity.get("document_release")
        and identity.get("release_applicability") == "6.x"
        and identity.get("resolved_release_applicability")
        == identity.get("release_applicability")
        and row_ok
        and identity.get("resolved_selected_row") == rows
        and bool(owner)
        and not owner.startswith("private/")
        and identity.get("resolved_document_owner") == owner
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("citation_sha256", "")).lower())
        is not None
        and identity.get("resolved_citation_sha256") == identity.get("citation_sha256")
        and re.fullmatch(r"[0-9a-f]{64}", str(identity.get("response_sha256", "")).lower())
        is not None
        and identity.get("accepted_response_sha256") == identity.get("response_sha256")
    )


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
    output_record_layout_contracts: list[bool] = []
    winding_input_contracts: list[bool] = []
    bem_panel_region_contracts: list[bool] = []
    position_sweep_force_contracts: list[bool] = []
    mao_case_result_contracts: list[bool] = []
    mesh_result_entity_map_contracts: list[bool] = []
    force_method_profile_generation_contracts: list[bool] = []
    headless_result_finalization_contracts: list[bool] = []
    result_manifest_generation_contracts: list[bool] = []
    public_artifact_boundary_contracts: list[bool] = []
    document_index_contracts: list[bool] = []
    public_query_contracts: list[bool] = []
    document_evidence_contracts: list[bool] = []
    public_query_citation_contracts: list[bool] = []
    document_glossary_contracts: list[bool] = []
    bibliography_evidence_contracts: list[bool] = []
    command_option_schema_contracts: list[bool] = []
    mao_section_schema_contracts: list[bool] = []
    command_alias_platform_contracts: list[bool] = []
    mao_vector_schema_contracts: list[bool] = []
    mao_record_schema_contracts: list[bool] = []
    solver_result_lineage_contracts: list[bool] = []
    mag_block_record_contracts: list[bool] = []
    mao_stepped_parameter_table_contracts: list[bool] = []
    mag_material_variable_record_contracts: list[bool] = []
    mao_transient_table_contracts: list[bool] = []
    mao_table_graph_contracts: list[bool] = []
    document_option_contracts: list[bool] = []
    input_schema_contracts: list[bool] = []
    bilingual_citation_contracts: list[bool] = []
    document_equation_contracts: list[bool] = []
    input_region_reference_contracts: list[bool] = []
    mao_output_identity_contracts: list[bool] = []
    document_table_identity_contracts: list[bool] = []
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
            output_record_layout_contracts.append(False)
            winding_input_contracts.append(False)
            bem_panel_region_contracts.append(False)
            position_sweep_force_contracts.append(False)
            mao_case_result_contracts.append(False)
            mesh_result_entity_map_contracts.append(False)
            force_method_profile_generation_contracts.append(False)
            headless_result_finalization_contracts.append(False)
            result_manifest_generation_contracts.append(False)
            public_artifact_boundary_contracts.append(False)
            document_index_contracts.append(False)
            public_query_contracts.append(False)
            document_evidence_contracts.append(False)
            public_query_citation_contracts.append(False)
            document_glossary_contracts.append(False)
            bibliography_evidence_contracts.append(False)
            command_option_schema_contracts.append(False)
            mao_section_schema_contracts.append(False)
            command_alias_platform_contracts.append(False)
            mao_vector_schema_contracts.append(False)
            mao_record_schema_contracts.append(False)
            solver_result_lineage_contracts.append(False)
            mag_block_record_contracts.append(False)
            mao_stepped_parameter_table_contracts.append(False)
            mag_material_variable_record_contracts.append(False)
            mao_transient_table_contracts.append(False)
            mao_table_graph_contracts.append(False)
            document_option_contracts.append(False)
            input_schema_contracts.append(False)
            bilingual_citation_contracts.append(False)
            document_equation_contracts.append(False)
            input_region_reference_contracts.append(False)
            mao_output_identity_contracts.append(False)
            document_table_identity_contracts.append(False)
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
        output_record_layout_contracts.append(
            _output_record_matches_version_endian_length_generation(run)
        )
        winding_input_contracts.append(
            _winding_matches_turn_current_phase_region_generation(run)
        )
        bem_panel_region_contracts.append(
            _bem_panel_material_region_matches_model_generation(run)
        )
        position_sweep_force_contracts.append(
            _position_sweep_force_rows_match_generation(run)
        )
        mao_case_result_contracts.append(
            _mao_case_result_matches_generation(run)
        )
        mesh_result_entity_map_contracts.append(
            _mesh_result_matches_entity_map_generation(run)
        )
        force_method_profile_generation_contracts.append(
            _force_method_profile_matches_generation(run)
        )
        headless_result_finalization_contracts.append(
            _headless_result_finalization_matches_generation(run)
        )
        result_manifest_generation_contracts.append(
            _result_manifest_matches_generation(run)
        )
        public_artifact_boundary_contracts.append(
            _public_artifact_manifest_is_bounded(run)
        )
        document_index_contracts.append(_document_index_identity_ok(run))
        public_query_contracts.append(_public_query_identity_ok(run))
        document_evidence_contracts.append(_document_evidence_identity_ok(run))
        public_query_citation_contracts.append(_public_query_citation_identity_ok(run))
        document_glossary_contracts.append(_document_glossary_identity_ok(run))
        bibliography_evidence_contracts.append(_bibliography_evidence_identity_ok(run))
        command_option_schema_contracts.append(_command_option_schema_identity_ok(run))
        mao_section_schema_contracts.append(_mao_section_schema_identity_ok(run))
        command_alias_platform_contracts.append(_command_alias_platform_identity_ok(run))
        mao_vector_schema_contracts.append(_mao_vector_schema_identity_ok(run))
        mao_record_schema_contracts.append(_mao_record_schema_identity_ok(run))
        solver_result_lineage_contracts.append(_solver_result_lineage_identity_ok(run))
        mag_block_record_contracts.append(_mag_block_record_identity_ok(run))
        mao_stepped_parameter_table_contracts.append(
            _mao_stepped_parameter_table_identity_ok(run)
        )
        mag_material_variable_record_contracts.append(
            _mag_material_variable_record_identity_ok(run)
        )
        mao_transient_table_contracts.append(
            _mao_transient_table_identity_ok(run)
        )
        mao_table_graph_contracts.append(_mao_table_graph_identity_ok(run))
        document_option_contracts.append(_document_option_identity_ok(run))
        input_schema_contracts.append(_input_schema_identity_ok(run))
        bilingual_citation_contracts.append(_bilingual_citation_identity_ok(run))
        document_equation_contracts.append(_document_equation_identity_ok(run))
        input_region_reference_contracts.append(
            _input_region_reference_identity_ok(run)
        )
        mao_output_identity_contracts.append(_mao_output_identity_ok(run))
        document_table_identity_contracts.append(_document_table_identity_ok(run))
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
        "output_records_use_current_version_endian_length_and_file_generation": all(
            output_record_layout_contracts
        ),
        "windings_use_current_turns_currents_phases_and_region_map": all(
            winding_input_contracts
        ),
        "bem_panels_use_current_groups_materials_permeabilities_and_regions": all(
            bem_panel_region_contracts
        ),
        "position_sweep_uses_current_rows_force_frame_and_units": all(
            position_sweep_force_contracts
        ),
        "mao_results_use_current_model_version_revision_and_completion": all(
            mao_case_result_contracts
        ),
        "mesh_results_use_current_entity_counts_material_map_and_frame": all(
            mesh_result_entity_map_contracts
        ),
        "force_profiles_use_current_method_selection_surface_nodal_frame_and_result": all(
            force_method_profile_generation_contracts
        ),
        "headless_runs_close_dialog_process_lock_log_and_final_artifact_state": all(
            headless_result_finalization_contracts
        ),
        "result_manifests_share_components_columns_units_rows_job_model_and_generation": all(
            result_manifest_generation_contracts
        ),
        "public_artifacts_stay_in_allowed_root_schema_allowlist_and_redaction": all(
            public_artifact_boundary_contracts
        ),
        "document_index_uses_current_release_sections_anchors_topics_checksums_and_generation": all(
            document_index_contracts
        ),
        "public_queries_use_current_category_schema_document_allowlist_redaction_and_result": all(
            public_query_contracts
        ),
        "document_evidence_uses_current_edition_language_pages_figures_tables_anchors_and_checksums": all(
            document_evidence_contracts
        ),
        "public_queries_use_current_synonyms_topics_categories_versions_citations_and_redaction": all(
            public_query_citation_contracts
        ),
        "document_glossary_uses_current_aliases_categories_versions_anchors_redaction_and_digests": all(
            document_glossary_contracts
        ),
        "bibliography_evidence_uses_current_citation_doi_edition_pages_figures_allowlist_and_checksums": all(
            bibliography_evidence_contracts
        ),
        "command_guidance_uses_current_option_schema_defaults_enums_units_document_and_anchor": all(
            command_option_schema_contracts
        ),
        "mao_sections_use_current_header_columns_units_locale_rows_owner_and_checksums": all(
            mao_section_schema_contracts
        ),
        "command_guidance_uses_current_alias_platform_options_version_anchor_document_and_digest": all(
            command_alias_platform_contracts
        ),
        "mao_vectors_use_current_components_frame_units_point_order_owner_and_digest": all(
            mao_vector_schema_contracts
        ),
        "mao_records_use_current_schema_endian_offset_model_observable_units_and_digest": all(
            mao_record_schema_contracts
        ),
        "solver_results_use_session_model_run_completion_generation_and_artifact_lineage_not_entitlement": all(
            solver_result_lineage_contracts
        ),
        "mag_blocks_use_current_schema_endian_zero_based_connectivity_material_offset_model_and_checksum": all(
            mag_block_record_contracts
        ),
        "mao_parameter_tables_use_current_tuples_row_order_convergence_unit_owners_count_and_digest": all(
            mao_stepped_parameter_table_contracts
        ),
        "mag_material_records_use_current_offsets_count_si_units_ordered_bh_material_crc_model_and_file": all(
            mag_material_variable_record_contracts
        ),
        "mao_transient_tables_use_current_channels_units_times_rows_event_completion_owners_count_and_digest": all(
            mao_transient_table_contracts
        ),
        "mao_result_views_use_current_table_graph_axes_units_case_solver_timestamp_export_owner_and_digests": all(
            mao_table_graph_contracts
        ),
        "document_options_use_current_enum_default_version_scope_example_revision_public_boundary_and_response": all(
            document_option_contracts
        ),
        "input_descriptions_use_current_sections_continuations_encoding_units_dependencies_enums_release_owner_schema_and_boundary": all(
            input_schema_contracts
        ),
        "bilingual_documentation_uses_current_aliases_section_page_release_scope_citation_boundary_owner_and_response": all(
            bilingual_citation_contracts
        ),
        "document_equations_use_current_symbols_units_sign_section_release_citation_owner_and_response": all(
            document_equation_contracts
        ),
        "input_regions_use_current_numbering_material_source_boundary_continuation_unit_release_owner_and_response": all(
            input_region_reference_contracts
        ),
        "mao_outputs_use_current_section_records_units_case_iteration_owner_input_and_output_digests": all(
            mao_output_identity_contracts
        ),
        "document_tables_use_current_axis_order_units_release_row_owner_citation_and_response": all(
            document_table_identity_contracts
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
