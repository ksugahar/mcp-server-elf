from __future__ import annotations

import json

from elf_mcp_server.force_method_profile_contract import (
    force_method_profile_contract_gate,
)
from test_generalization_v24 import _summary_v24


_PROMOTED_CASE_IDS = (
    "v25_source_result_manifest_component_column_unit_row_job_model_generation_mismatch",
    "v25_source_public_artifact_root_schema_observable_allowlist_redaction_mismatch",
)


def _summary_v25():
    summary = _summary_v24()
    for index, run in enumerate(summary["runs"]):
        terminal = run["output_artifacts"][".mao"]["terminal_record"]
        job_generation = terminal["job_generation"]
        generation = f"result-manifest-{201 + index}"
        run[
            "result_manifest_component_column_unit_row_job_model_generation_identity"
        ] = {
            "job_generation": job_generation,
            "result_job_generation": job_generation,
            "result_generation": generation,
            "component_result_generation": generation,
            "column_result_generation": generation,
            "unit_result_generation": generation,
            "row_result_generation": generation,
            "model_result_generation": generation,
            "manifest_result_generation": generation,
            "component_frame": "global_xyz",
            "result_component_frame": "global_xyz",
            "column_names": ["row_id", "force_x", "force_y", "force_z"],
            "parsed_column_names": ["row_id", "force_x", "force_y", "force_z"],
            "column_units": ["1", "N", "N", "N"],
            "parsed_column_units": ["1", "N", "N", "N"],
            "row_ids": [0, 1, 2],
            "parsed_row_ids": [0, 1, 2],
            "model_sha256": "4" * 64,
            "result_model_sha256": "4" * 64,
            "result_manifest_sha256": "5" * 64,
            "parsed_result_manifest_sha256": "5" * 64,
        }
        generation = f"public-manifest-{201 + index}"
        run[
            "public_artifact_root_schema_observable_allowlist_redaction_generation_identity"
        ] = {
            "job_generation": job_generation,
            "result_job_generation": job_generation,
            "manifest_generation": generation,
            "root_manifest_generation": generation,
            "schema_manifest_generation": generation,
            "allowlist_manifest_generation": generation,
            "redaction_manifest_generation": generation,
            "result_manifest_generation": generation,
            "artifact_root_id": "public_package_artifacts",
            "result_artifact_root_id": "public_package_artifacts",
            "relative_artifact_path": "artifacts/result_manifest.json",
            "result_relative_artifact_path": "artifacts/result_manifest.json",
            "public_schema": "elf-public-result-manifest/v1",
            "result_public_schema": "elf-public-result-manifest/v1",
            "observable_allowlist": ["force_vector_n", "torque_n_m"],
            "returned_observable_keys": ["force_vector_n"],
            "redacted_field_names": ["api_token", "license_key", "local_path"],
            "result_redacted_field_names": ["api_token", "license_key", "local_path"],
            "redaction_applied": True,
            "sensitive_fields_present": [],
            "public_manifest_sha256": "6" * 64,
            "result_public_manifest_sha256": "6" * 64,
        }
    return summary


def _gate(summary: dict) -> dict:
    return force_method_profile_contract_gate(json.dumps(summary))


def test_v25_source_positive_result_manifest_and_public_boundary() -> None:
    assert _gate(_summary_v25())["status"] == "ok"


def test_v25_source_result_manifest_identity_mismatch() -> None:
    summary = _summary_v25()
    identity = summary["runs"][0][
        "result_manifest_component_column_unit_row_job_model_generation_identity"
    ]
    identity.update(
        {
            "component_result_generation": "result-manifest-200",
            "column_result_generation": "result-manifest-199",
            "unit_result_generation": "result-manifest-198",
            "row_result_generation": "result-manifest-197",
            "model_result_generation": "result-manifest-196",
            "result_job_generation": "job-stale",
            "result_component_frame": "local_xyz",
            "parsed_column_names": ["row_id", "force_z", "force_y", "force_x"],
            "parsed_column_units": ["1", "mN", "N", "N"],
            "parsed_row_ids": [2, 1, 0],
            "result_model_sha256": "a" * 64,
            "parsed_result_manifest_sha256": "b" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "result_manifests_share_components_columns_units_rows_job_model_and_generation"
    ]


def test_v25_source_public_artifact_boundary_mismatch() -> None:
    summary = _summary_v25()
    identity = summary["runs"][0][
        "public_artifact_root_schema_observable_allowlist_redaction_generation_identity"
    ]
    identity.update(
        {
            "root_manifest_generation": "public-manifest-200",
            "schema_manifest_generation": "public-manifest-199",
            "allowlist_manifest_generation": "public-manifest-198",
            "redaction_manifest_generation": "public-manifest-197",
            "result_artifact_root_id": "arbitrary_local_path",
            "result_relative_artifact_path": "../private/result.json",
            "result_public_schema": "unrestricted-json/v1",
            "returned_observable_keys": ["force_vector_n", "api_token"],
            "result_redacted_field_names": [],
            "redaction_applied": False,
            "sensitive_fields_present": ["api_token", "local_path"],
            "result_public_manifest_sha256": "c" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "public_artifacts_stay_in_allowed_root_schema_allowlist_and_redaction"
    ]
