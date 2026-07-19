from __future__ import annotations

from elf_mcp_server.v47_identity import MAO, RUN, validate_source_v47_identity


PROMOTED_CASE_IDS = {
    "v47_source_tool_mao_schema_column_case_index_order_duplicate_mismatch",
    "v47_source_tool_licensed_run_model_result_generation_batch_index_owner_mismatch",
}


def _identities() -> list[dict[str, object]]:
    mao_generation = "mao-v47"
    run_generation = "run-v47"
    return [
        {
            MAO: {
                "generation": mao_generation,
                **{
                    key: mao_generation
                    for key in (
                        "schema_generation",
                        "column_generation",
                        "case_index_generation",
                        "run_generation",
                        "result_generation",
                    )
                },
                "schema_version": "mao:v1",
                "replayed_schema_version": "mao:v1",
                "column_order": ["case_index", "force_n", "torque_nm", "power_w"],
                "replayed_column_order": ["case_index", "force_n", "torque_nm", "power_w"],
                "case_indices": [0, 1, 2],
                "replayed_case_indices": [0, 1, 2],
                "run_owner": "run:mao-v47",
                "replayed_run_owner": "run:mao-v47",
                "result_sha256": "1" * 64,
                "accepted_result_sha256": "1" * 64,
            },
            RUN: {
                "generation": run_generation,
                **{
                    key: run_generation
                    for key in (
                        "license_generation",
                        "model_generation",
                        "result_generation",
                        "batch_generation",
                        "owner_generation",
                    )
                },
                "session_attached": True,
                "result_session_attached": True,
                "model_generation_id": "model:run-v47",
                "replayed_model_generation_id": "model:run-v47",
                "result_generation_id": "result:run-v47",
                "replayed_result_generation_id": "result:run-v47",
                "batch_index": 7,
                "replayed_batch_index": 7,
                "run_owner": "run:run-v47",
                "replayed_run_owner": "run:run-v47",
                "result_sha256": "2" * 64,
                "accepted_result_sha256": "2" * 64,
            },
        }
    ]


def test_v47_positive_product_replay_is_accepted() -> None:
    assert all(validate_source_v47_identity(_identities()).values())


def test_v47_mao_schema_column_case_owner_mutation_is_rejected() -> None:
    identities = _identities()
    identities[0][MAO]["replayed_column_order"] = ["case_index", "torque_nm", "force_n", "force_n"]
    identities[0][MAO]["replayed_case_indices"] = [0, 2, 2]
    identities[0][MAO]["replayed_run_owner"] = "run:other"
    assert not all(validate_source_v47_identity(identities).values())


def test_v47_licensed_run_generation_batch_owner_mutation_is_rejected() -> None:
    identities = _identities()
    identities[0][RUN]["replayed_model_generation_id"] = "model:old"
    identities[0][RUN]["replayed_result_generation_id"] = "result:other"
    identities[0][RUN]["replayed_batch_index"] = 3
    identities[0][RUN]["replayed_run_owner"] = "run:other"
    assert not all(validate_source_v47_identity(identities).values())
