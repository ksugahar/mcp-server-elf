from __future__ import annotations

from copy import deepcopy

from elf_mcp_server.v48_identity import BATCH, COMPLEX, validate_source_v48_identity


PROMOTED_CASE_IDS = {
    "v48_source_tool_mao_complex_encoding_phase_convention_unit_column_owner_mismatch",
    "v48_source_tool_batch_include_macro_override_precedence_workdir_run_owner_mismatch",
}


def _identities() -> list[dict[str, object]]:
    complex_generation = "mao-complex-v48-901"
    batch_generation = "batch-deck-v48-901"
    values = [[1.0, 0.5], [0.8, -0.2]]
    includes = ["base.deck", "materials.deck", "case.deck"]
    overrides = [{"name": "frequency_hz", "value": 50.0, "source": "case.deck"}]
    identity = {
        COMPLEX: {
            "generation": complex_generation,
            "encoding_generation": complex_generation,
            "phase_generation": complex_generation,
            "unit_generation": complex_generation,
            "column_generation": complex_generation,
            "result_generation": complex_generation,
            "complex_encoding": "real_imaginary",
            "replayed_complex_encoding": "real_imaginary",
            "phase_convention": "positive_lead_deg",
            "replayed_phase_convention": "positive_lead_deg",
            "column_name": "field_complex",
            "replayed_column_name": "field_complex",
            "column_unit": "A_per_m",
            "replayed_column_unit": "A_per_m",
            "complex_rows": values,
            "replayed_complex_rows": values,
            "column_owner": "column:field-complex-v48-901",
            "replayed_column_owner": "column:field-complex-v48-901",
            "result_sha256": "8" * 64,
            "accepted_result_sha256": "8" * 64,
        },
        BATCH: {
            "generation": batch_generation,
            "include_generation": batch_generation,
            "macro_generation": batch_generation,
            "workdir_generation": batch_generation,
            "run_generation": batch_generation,
            "result_generation": batch_generation,
            "include_order": includes,
            "replayed_include_order": includes,
            "macro_overrides": overrides,
            "replayed_macro_overrides": overrides,
            "override_precedence": "last_include_wins",
            "replayed_override_precedence": "last_include_wins",
            "working_directory_id": "workdir:batch-v48-901",
            "replayed_working_directory_id": "workdir:batch-v48-901",
            "run_owner": "run:batch-v48-901",
            "replayed_run_owner": "run:batch-v48-901",
            "result_sha256": "9" * 64,
            "accepted_result_sha256": "9" * 64,
        },
    }
    return [deepcopy(identity), deepcopy(identity)]


def test_v48_positive_complex_and_batch_replays_are_accepted() -> None:
    assert all(validate_source_v48_identity(_identities()).values())


def test_v48_complex_encoding_mutations_are_rejected() -> None:
    identities = _identities()
    identities[0][COMPLEX]["replayed_complex_encoding"] = "magnitude_phase"
    identities[0][COMPLEX]["replayed_column_unit"] = "mA_per_m"
    assert validate_source_v48_identity(identities)["source_v48_complex_encoding_phase_unit_column_owner"] is False


def test_v48_batch_precedence_mutations_are_rejected() -> None:
    identities = _identities()
    identities[0][BATCH]["replayed_include_order"] = list(reversed(identities[0][BATCH]["include_order"]))
    identities[0][BATCH]["replayed_run_owner"] = "run:old"
    assert validate_source_v48_identity(identities)["source_v48_batch_include_override_workdir_run_owner"] is False
