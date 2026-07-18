from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v31 import _summary_v31


_PROMOTED_CASE_IDS = (
    "v32_source_mag_block_record_endian_index_connectivity_material_offset_checksum_mismatch",
    "v32_source_mao_stepped_parameter_tuple_row_order_convergence_owner_digest_mismatch",
)


def _summary_v32():
    summary = _summary_v31()
    for index, run in enumerate(summary["runs"]):
        generation = f"mag-block-{361 + index}"
        run[
            "mag_block_schema_endian_index_connectivity_material_offset_model_checksum_identity"
        ] = {
            "mag_generation": generation,
            **{
                key: generation
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
            },
            "record_schema": "mag-model-block-v6",
            "parsed_record_schema": "mag-model-block-v6",
            "byte_order": "little",
            "parsed_byte_order": "little",
            "index_base": 0,
            "parsed_index_base": 0,
            "connectivity": [0, 1, 2, 3],
            "parsed_connectivity": [0, 1, 2, 3],
            "material_id": 7,
            "parsed_material_id": 7,
            "block_offset_bytes": 256,
            "parsed_block_offset_bytes": 256,
            "model_generation": "model-361",
            "parsed_model_generation": "model-361",
            "file_sha256": "5" * 64,
            "parsed_file_sha256": "5" * 64,
        }
        generation = f"mao-step-{361 + index}"
        tuples = [[100.0, 0.0], [100.0, 15.0], [200.0, 0.0], [200.0, 15.0]]
        run[
            "mao_stepped_parameter_tuple_row_convergence_unit_owner_count_digest_identity"
        ] = {
            "step_generation": generation,
            **{
                key: generation
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
            },
            "parameter_names": ["current_a", "angle_deg"],
            "parsed_parameter_names": ["current_a", "angle_deg"],
            "parameter_tuples": tuples,
            "parsed_parameter_tuples": [list(row) for row in tuples],
            "row_order": [0, 1, 2, 3],
            "parsed_row_order": [0, 1, 2, 3],
            "converged": [True, True, True, True],
            "parsed_converged": [True, True, True, True],
            "observable_unit": "N*m",
            "parsed_observable_unit": "N*m",
            "model_owner": "model-361",
            "parsed_model_owner": "model-361",
            "run_owner": "run-361",
            "parsed_run_owner": "run-361",
            "row_count": 4,
            "parsed_row_count": 4,
            "artifact_sha256": "6" * 64,
            "parsed_artifact_sha256": "6" * 64,
        }
    return summary


def test_v32_source_positive_mag_block_and_mao_parameter_table():
    assert _gate(_summary_v32())["status"] == "ok"


def test_v32_source_mag_block_record_endian_index_connectivity_material_offset_checksum_mismatch():
    summary = _summary_v32()
    record = summary["runs"][0][
        "mag_block_schema_endian_index_connectivity_material_offset_model_checksum_identity"
    ]
    record.update(
        {
            "schema_mag_generation": "mag-block-360",
            "model_mag_generation": "mag-block-359",
            "result_mag_generation": "mag-block-358",
            "parsed_record_schema": "mag-model-block-v5",
            "parsed_byte_order": "big",
            "parsed_index_base": 1,
            "parsed_connectivity": [3, 2, 1, 0],
            "parsed_material_id": 9,
            "parsed_block_offset_bytes": 128,
            "parsed_model_generation": "model-old",
            "parsed_file_sha256": "b" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mag_blocks_use_current_schema_endian_zero_based_connectivity_material_offset_model_and_checksum"
    ]


def test_v32_source_mao_stepped_parameter_tuple_row_order_convergence_owner_digest_mismatch():
    summary = _summary_v32()
    record = summary["runs"][0][
        "mao_stepped_parameter_tuple_row_convergence_unit_owner_count_digest_identity"
    ]
    record.update(
        {
            "tuple_step_generation": "mao-step-360",
            "owner_step_generation": "mao-step-359",
            "result_step_generation": "mao-step-358",
            "parsed_parameter_names": ["angle_deg", "current_a"],
            "parsed_parameter_tuples": [[0.0, 100.0], [15.0, 100.0]],
            "parsed_row_order": [3, 2, 1, 0],
            "parsed_converged": [True, False, True, False],
            "parsed_observable_unit": "lbf*ft",
            "parsed_model_owner": "model-old",
            "parsed_run_owner": "run-old",
            "parsed_row_count": 2,
            "parsed_artifact_sha256": "c" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "mao_parameter_tables_use_current_tuples_row_order_convergence_unit_owners_count_and_digest"
    ]
