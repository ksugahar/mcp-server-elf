from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v30 import _summary_v30

_PROMOTED_CASE_IDS = (
    "v31_source_mao_record_schema_endian_offset_model_generation_observable_owner_mismatch",
    "v31_source_solver_entitlement_session_run_result_lineage_dongle_presence_not_provenance",
)

def _summary_v31():
    summary = _summary_v30()
    for index, run in enumerate(summary["runs"]):
        g = f"mao-record-{351 + index}"
        run["mao_record_schema_endian_offset_model_observable_unit_file_digest_identity"] = {
            "mao_generation": g, **{key: g for key in ("schema_mao_generation", "endian_mao_generation", "offset_mao_generation", "model_mao_generation", "observable_mao_generation", "unit_mao_generation", "digest_mao_generation", "result_mao_generation")},
            "record_schema": "mao-result-v6", "parsed_record_schema": "mao-result-v6", "byte_order": "little", "parsed_byte_order": "little", "record_offset_bytes": 128, "parsed_record_offset_bytes": 128,
            "model_generation": "model-351", "parsed_model_generation": "model-351", "observable_owner": "run-351:force-z", "parsed_observable_owner": "run-351:force-z",
            "unit_metadata": {"force_z": "N"}, "parsed_unit_metadata": {"force_z": "N"}, "file_sha256": "5" * 64, "parsed_file_sha256": "5" * 64,
        }
        g = f"lineage-{351 + index}"
        run["solver_entitlement_session_model_run_completion_result_lineage_identity"] = {
            "lineage_generation": g, **{key: g for key in ("session_lineage_generation", "model_lineage_generation", "run_lineage_generation", "completion_lineage_generation", "result_lineage_generation", "digest_lineage_generation")},
            "entitlement_present": True, "dongle_present": True, "entitlement_is_result_provenance": False,
            "solver_session_id": "session-351", "result_solver_session_id": "session-351", "model_owner": "model-351", "result_model_owner": "model-351", "run_owner": "run-351", "result_run_owner": "run-351",
            "completion_marker": "completed", "result_completion_marker": "completed", "result_generation": "result-351", "accepted_result_generation": "result-351", "artifact_sha256": "6" * 64, "accepted_artifact_sha256": "6" * 64,
        }
    return summary

def test_v31_source_positive_mao_schema_and_solver_lineage(): assert _gate(_summary_v31())["status"] == "ok"

def test_v31_source_mao_record_schema_endian_offset_model_generation_observable_owner_mismatch():
    summary = _summary_v31(); record = summary["runs"][0]["mao_record_schema_endian_offset_model_observable_unit_file_digest_identity"]
    record.update({"schema_mao_generation": "old", "parsed_record_schema": "mao-old", "parsed_byte_order": "big", "parsed_record_offset_bytes": 64, "parsed_model_generation": "old", "parsed_observable_owner": "other", "parsed_unit_metadata": {"force_z": "mN"}, "parsed_file_sha256": "b" * 64})
    result = _gate(summary); assert result["status"] == "needs_attention"; assert not result["checks"]["mao_records_use_current_schema_endian_offset_model_observable_units_and_digest"]

def test_v31_source_solver_entitlement_session_run_result_lineage_dongle_presence_not_provenance():
    summary = _summary_v31(); record = summary["runs"][0]["solver_entitlement_session_model_run_completion_result_lineage_identity"]
    record.update({"session_lineage_generation": "old", "entitlement_is_result_provenance": True, "result_solver_session_id": "", "result_model_owner": "old", "result_run_owner": "old", "result_completion_marker": "started", "accepted_result_generation": "old", "accepted_artifact_sha256": "c" * 64})
    result = _gate(summary); assert result["status"] == "needs_attention"; assert not result["checks"]["solver_results_use_session_model_run_completion_generation_and_artifact_lineage_not_entitlement"]
