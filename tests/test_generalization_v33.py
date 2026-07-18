from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v32 import _summary_v32


_PROMOTED_CASE_IDS = (
    "v33_source_mag_material_variable_record_offset_count_unit_bh_monotonic_crc_mismatch",
    "v33_source_mao_transient_channel_header_sample_time_unit_event_completion_owner_mismatch",
)


def _summary_v33():
    summary = _summary_v32()
    for index, run in enumerate(summary["runs"]):
        generation = f"mag-material-{371 + index}"
        run[
            "mag_material_variable_record_offset_count_unit_bh_order_material_crc_model_file_identity"
        ] = {
            "material_generation": generation,
            **{
                key: generation
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
            },
            "record_offsets_bytes": [1024, 1064, 1120],
            "parsed_record_offsets_bytes": [1024, 1064, 1120],
            "point_count": 3,
            "parsed_point_count": 3,
            "field_unit": "A/m",
            "parsed_field_unit": "A/m",
            "flux_density_unit": "T",
            "parsed_flux_density_unit": "T",
            "bh_points": [[0.0, 0.0], [100.0, 0.5], [200.0, 1.0]],
            "parsed_bh_points": [[0.0, 0.0], [100.0, 0.5], [200.0, 1.0]],
            "material_id": 7,
            "parsed_material_id": 7,
            "record_crc32": "1a2b3c4d",
            "parsed_record_crc32": "1a2b3c4d",
            "model_generation_id": "model-371",
            "parsed_model_generation_id": "model-371",
            "file_sha256": "5" * 64,
            "parsed_file_sha256": "5" * 64,
        }
        generation = f"mao-transient-{371 + index}"
        rows = [[0.0, 0.0, 0.0], [0.001, 1.0, 5.0], [0.002, 0.0, 0.0]]
        run[
            "mao_transient_channel_header_sample_time_unit_event_completion_owner_count_digest_identity"
        ] = {
            "transient_generation": generation,
            **{
                key: generation
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
            },
            "channel_headers": ["time", "current", "force"],
            "parsed_channel_headers": ["time", "current", "force"],
            "channel_units": ["s", "A", "N"],
            "parsed_channel_units": ["s", "A", "N"],
            "sample_times_s": [0.0, 0.001, 0.002],
            "parsed_sample_times_s": [0.0, 0.001, 0.002],
            "rows": rows,
            "parsed_rows": [list(row) for row in rows],
            "event_row_index": 1,
            "parsed_event_row_index": 1,
            "solver_completed": True,
            "parsed_solver_completed": True,
            "model_owner": "model-371",
            "parsed_model_owner": "model-371",
            "run_owner": "run-371",
            "parsed_run_owner": "run-371",
            "row_count": 3,
            "parsed_row_count": 3,
            "artifact_sha256": "6" * 64,
            "parsed_artifact_sha256": "6" * 64,
        }
    return summary


def test_v33_source_positive_mag_material_and_mao_transient_tables():
    assert _gate(_summary_v33())["status"] == "ok"


def test_v33_source_mag_material_variable_record_offset_count_unit_bh_monotonic_crc_mismatch():
    summary = _summary_v33()
    record = summary["runs"][0][
        "mag_material_variable_record_offset_count_unit_bh_order_material_crc_model_file_identity"
    ]
    record.update(
        {
            "offset_generation": "mag-material-370",
            "bh_generation": "mag-material-369",
            "result_generation": "mag-material-368",
            "parsed_record_offsets_bytes": [1120, 1024, 1000],
            "parsed_point_count": 2,
            "parsed_field_unit": "Oe",
            "parsed_flux_density_unit": "G",
            "parsed_bh_points": [[200.0, 1.0], [100.0, 0.4], [0.0, 0.5]],
            "parsed_material_id": 9,
            "parsed_record_crc32": "deadbeef",
            "parsed_model_generation_id": "model-old",
            "parsed_file_sha256": "b" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mag_material_records_use_current_offsets_count_si_units_ordered_bh_material_crc_model_and_file"
    ]


def test_v33_source_mao_transient_channel_header_sample_time_unit_event_completion_owner_mismatch():
    summary = _summary_v33()
    record = summary["runs"][0][
        "mao_transient_channel_header_sample_time_unit_event_completion_owner_count_digest_identity"
    ]
    record.update(
        {
            "channel_generation": "mao-transient-370",
            "event_generation": "mao-transient-369",
            "result_generation": "mao-transient-368",
            "parsed_channel_headers": ["force", "time"],
            "parsed_channel_units": ["lbf", "ms"],
            "parsed_sample_times_s": [0.002, 0.001, 0.0],
            "parsed_rows": [[0.002, 0.0, 0.0], [0.001, 1.0, 5.0]],
            "parsed_event_row_index": 7,
            "parsed_solver_completed": False,
            "parsed_model_owner": "model-old",
            "parsed_run_owner": "run-old",
            "parsed_row_count": 2,
            "parsed_artifact_sha256": "c" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mao_transient_tables_use_current_channels_units_times_rows_event_completion_owners_count_and_digest"
    ]
