from __future__ import annotations

from test_generalization_v23 import _gate
from test_generalization_v37 import _summary_v37


_PROMOTED_CASE_IDS = (
    "v38_source_command_grammar_required_mutex_dependency_default_unit_release_citation_mismatch",
    "v38_source_vector_output_basis_component_order_handedness_unit_transform_owner_mismatch",
)


def _summary_v38():
    summary = _summary_v37()
    option_names = [
        "input", "output", "linear", "nonlinear", "tolerance", "frequency"
    ]
    transform = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    for index, run in enumerate(summary["runs"]):
        generation = f"command-grammar-{258 + index}"
        run[
            "command_grammar_required_mutex_dependency_default_unit_release_citation_owner_response_identity"
        ] = {
            "grammar_generation": generation,
            **{
                key: generation
                for key in (
                    "option_generation", "required_generation", "mutex_generation",
                    "dependency_generation", "default_generation", "unit_generation",
                    "release_generation", "citation_generation", "owner_generation",
                    "response_generation",
                )
            },
            "command_name": "ANALYZE",
            "resolved_command_name": "ANALYZE",
            "option_names": option_names,
            "resolved_option_names": option_names,
            "required_options": ["input", "output"],
            "resolved_required_options": ["input", "output"],
            "mutually_exclusive_groups": [["linear", "nonlinear"]],
            "resolved_mutually_exclusive_groups": [["linear", "nonlinear"]],
            "dependency_rules": [["nonlinear", "tolerance"]],
            "resolved_dependency_rules": [["nonlinear", "tolerance"]],
            "default_values": {"linear": True, "frequency": 0.0},
            "resolved_default_values": {"linear": True, "frequency": 0.0},
            "option_units": {"tolerance": "dimensionless", "frequency": "Hz"},
            "resolved_option_units": {
                "tolerance": "dimensionless", "frequency": "Hz"
            },
            "release_scope": "6.x",
            "resolved_release_scope": "6.x",
            "section_citation": "Command Reference > ANALYZE",
            "resolved_section_citation": "Command Reference > ANALYZE",
            "document_owner": "documentation:command-258",
            "resolved_document_owner": "documentation:command-258",
            "citation_sha256": "3" * 64,
            "resolved_citation_sha256": "3" * 64,
            "response_sha256": "4" * 64,
            "accepted_response_sha256": "4" * 64,
        }

        generation = f"vector-output-{258 + index}"
        run[
            "vector_output_basis_component_order_handedness_unit_transform_record_release_citation_response_identity"
        ] = {
            "vector_generation": generation,
            **{
                key: generation
                for key in (
                    "basis_generation", "component_generation",
                    "handedness_generation", "unit_generation",
                    "transform_generation", "record_generation",
                    "release_generation", "citation_generation",
                    "response_generation",
                )
            },
            "coordinate_basis": "global_cartesian",
            "resolved_coordinate_basis": "global_cartesian",
            "component_order": ["x", "y", "z"],
            "resolved_component_order": ["x", "y", "z"],
            "handedness": "right_handed",
            "resolved_handedness": "right_handed",
            "source_unit": "mT",
            "resolved_source_unit": "mT",
            "output_unit": "T",
            "resolved_output_unit": "T",
            "unit_scale": 0.001,
            "resolved_unit_scale": 0.001,
            "local_to_global_transform": transform,
            "resolved_local_to_global_transform": transform,
            "source_vector": [1000.0, 0.0, 0.0],
            "resolved_source_vector": [1000.0, 0.0, 0.0],
            "global_vector": [0.0, 1.0, 0.0],
            "resolved_global_vector": [0.0, 1.0, 0.0],
            "record_owner": "record:vector-output-258",
            "resolved_record_owner": "record:vector-output-258",
            "schema_release": "6.0",
            "resolved_schema_release": "6.0",
            "citation_sha256": "5" * 64,
            "resolved_citation_sha256": "5" * 64,
            "response_sha256": "6" * 64,
            "accepted_response_sha256": "6" * 64,
        }
    return summary


def test_v38_source_positive_command_grammar_and_vector_output_closure():
    assert _gate(_summary_v38())["status"] == "ok"


def test_v38_source_command_grammar_required_mutex_dependency_default_unit_release_citation_mismatch():
    summary = _summary_v38()
    row = summary["runs"][0][
        "command_grammar_required_mutex_dependency_default_unit_release_citation_owner_response_identity"
    ]
    row.update(
        {
            "required_generation": "command-grammar-257",
            "citation_generation": "command-grammar-256",
            "response_generation": "command-grammar-255",
            "resolved_required_options": ["old"],
            "resolved_mutually_exclusive_groups": [["linear", "tolerance"]],
            "resolved_dependency_rules": [["input", "old"]],
            "resolved_default_values": {"unknown": -1},
            "resolved_option_units": {"frequency": "rpm"},
            "resolved_release_scope": "internal",
            "resolved_section_citation": "Old Section",
            "resolved_document_owner": "private:old",
            "resolved_citation_sha256": "c" * 64,
            "accepted_response_sha256": "d" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "command_grammar_uses_current_required_mutex_dependency_defaults_units_release_citation_owner_and_response"
    ]


def test_v38_source_vector_output_basis_component_order_handedness_unit_transform_owner_mismatch():
    summary = _summary_v38()
    row = summary["runs"][0][
        "vector_output_basis_component_order_handedness_unit_transform_record_release_citation_response_identity"
    ]
    row.update(
        {
            "basis_generation": "vector-output-257",
            "transform_generation": "vector-output-256",
            "response_generation": "vector-output-255",
            "resolved_coordinate_basis": "local_cylindrical",
            "resolved_component_order": ["z", "y", "x"],
            "resolved_handedness": "left_handed",
            "resolved_output_unit": "mT",
            "resolved_unit_scale": 1000.0,
            "resolved_local_to_global_transform": [[1.0, 0.0], [0.0, 1.0]],
            "resolved_global_vector": [1000.0, 0.0, 0.0],
            "resolved_record_owner": "stale:record",
            "resolved_schema_release": "old",
            "resolved_citation_sha256": "e" * 64,
            "accepted_response_sha256": "f" * 64,
        }
    )
    result = _gate(summary)
    assert result["status"] == "needs_attention"
    assert not result["checks"][
        "vector_outputs_use_current_basis_component_order_handedness_units_transform_record_release_citation_and_response"
    ]


def test_v38_source_rejects_self_consistent_unknown_dependency_option():
    summary = _summary_v38()
    for run in summary["runs"]:
        row = run[
            "command_grammar_required_mutex_dependency_default_unit_release_citation_owner_response_identity"
        ]
        row["dependency_rules"] = [["nonlinear", "unknown"]]
        row["resolved_dependency_rules"] = [["nonlinear", "unknown"]]
    assert _gate(summary)["status"] == "needs_attention"


def test_v38_source_rejects_self_consistent_left_handed_vector_transform():
    summary = _summary_v38()
    reflection = [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for run in summary["runs"]:
        row = run[
            "vector_output_basis_component_order_handedness_unit_transform_record_release_citation_response_identity"
        ]
        row["local_to_global_transform"] = reflection
        row["resolved_local_to_global_transform"] = reflection
        row["global_vector"] = [-1.0, 0.0, 0.0]
        row["resolved_global_vector"] = [-1.0, 0.0, 0.0]
    assert _gate(summary)["status"] == "needs_attention"
