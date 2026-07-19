from __future__ import annotations

from copy import deepcopy

from elf_mcp_server.v50_identity import DECK, SPARSE, validate_source_v50_identity


PROMOTED_CASE_IDS = {
    "v50_source_tool_input_deck_continuation_include_encoding_newline_checksum_owner_mismatch",
    "v50_source_tool_mao_sparse_table_sentinel_missing_row_exponent_unit_owner_mismatch",
}


def _identities() -> list[dict[str, object]]:
    deck_generation = "input-deck-v50-901"
    sparse_generation = "mao-sparse-v50-901"
    paths = ["materials/base.inc", "loads/motion.inc"]
    missing = [0, 5, 9]
    identity = {
        DECK: {
            "generation": deck_generation, "continuation_generation": deck_generation, "include_generation": deck_generation,
            "encoding_generation": deck_generation, "newline_generation": deck_generation, "checksum_generation": deck_generation,
            "result_generation": deck_generation, "continuation_marker": "&", "replayed_continuation_marker": "&",
            "include_paths": paths, "replayed_include_paths": paths,
            "encoding": "utf-8", "replayed_encoding": "utf-8",
            "newline_convention": "crlf", "replayed_newline_convention": "crlf",
            "deck_sha256": "3" * 64, "replayed_deck_sha256": "3" * 64,
            "run_owner": "run:deck-v50-901", "replayed_run_owner": "run:deck-v50-901",
            "result_sha256": "4" * 64, "accepted_result_sha256": "4" * 64,
        },
        SPARSE: {
            "generation": sparse_generation, "sentinel_generation": sparse_generation, "row_generation": sparse_generation,
            "exponent_generation": sparse_generation, "unit_generation": sparse_generation, "result_generation": sparse_generation,
            "missing_value_sentinel": "-9.999000E+99", "replayed_missing_value_sentinel": "-9.999000E+99",
            "missing_row_indices": missing, "replayed_missing_row_indices": missing,
            "exponent_notation": "E", "replayed_exponent_notation": "E",
            "value_unit": "T", "replayed_value_unit": "T",
            "result_owner": "result:mao-v50-901", "replayed_result_owner": "result:mao-v50-901",
            "result_sha256": "5" * 64, "accepted_result_sha256": "5" * 64,
        },
    }
    return [deepcopy(identity), deepcopy(identity)]


def test_v50_positive_deck_and_sparse_replays_are_accepted() -> None:
    assert all(validate_source_v50_identity(_identities()).values())


def test_v50_deck_continuation_include_encoding_newline_checksum_and_owner_drift_is_rejected() -> None:
    identities = _identities()
    identities[0][DECK]["replayed_continuation_marker"] = "+"
    identities[0][DECK]["replayed_include_paths"] = list(reversed(identities[0][DECK]["include_paths"]))
    identities[0][DECK]["replayed_encoding"] = "shift_jis"
    identities[0][DECK]["replayed_deck_sha256"] = "6" * 64
    identities[0][DECK]["replayed_run_owner"] = "run:foreign"
    assert validate_source_v50_identity(identities)["source_v50_deck_continuation_include_encoding_newline_checksum_owner"] is False


def test_v50_sparse_sentinel_rows_exponent_unit_and_owner_drift_is_rejected() -> None:
    identities = _identities()
    identities[0][SPARSE]["replayed_missing_value_sentinel"] = "NaN"
    identities[0][SPARSE]["replayed_missing_row_indices"] = [1, 2]
    identities[0][SPARSE]["replayed_exponent_notation"] = "D"
    identities[0][SPARSE]["replayed_value_unit"] = "mT"
    identities[0][SPARSE]["replayed_result_owner"] = "result:foreign"
    assert validate_source_v50_identity(identities)["source_v50_mao_sparse_sentinel_rows_exponent_unit_owner"] is False
