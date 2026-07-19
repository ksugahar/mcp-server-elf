from __future__ import annotations

from copy import deepcopy

from elf_mcp_server.v49_identity import MAO, MATERIAL, validate_source_v49_identity


PROMOTED_CASE_IDS = {
    "v49_source_tool_mao_endian_float_precision_record_stride_column_offset_run_owner_mismatch",
    "v49_source_tool_material_include_relative_path_case_checksum_precedence_project_owner_mismatch",
}


def _identities() -> list[dict[str, object]]:
    mao_generation = "mao-layout-v49-901"
    material_generation = "material-include-v49-901"
    offsets = {"x": 0, "y": 8, "z": 16, "value": 24}
    paths = ["materials/base.mat", "materials/magnet.mat"]
    checksums = {"materials/base.mat": "5" * 64, "materials/magnet.mat": "6" * 64}
    identity = {
        MAO: {
            "generation": mao_generation,
            "endian_generation": mao_generation,
            "precision_generation": mao_generation,
            "layout_generation": mao_generation,
            "run_generation": mao_generation,
            "result_generation": mao_generation,
            "endianness": "little",
            "replayed_endianness": "little",
            "float_precision_bits": 64,
            "replayed_float_precision_bits": 64,
            "record_stride_bytes": 32,
            "replayed_record_stride_bytes": 32,
            "column_offsets_bytes": offsets,
            "replayed_column_offsets_bytes": offsets,
            "run_owner": "run:mao-v49-901",
            "replayed_run_owner": "run:mao-v49-901",
            "result_sha256": "4" * 64,
            "accepted_result_sha256": "4" * 64,
        },
        MATERIAL: {
            "generation": material_generation,
            "path_generation": material_generation,
            "case_generation": material_generation,
            "checksum_generation": material_generation,
            "precedence_generation": material_generation,
            "project_generation": material_generation,
            "result_generation": material_generation,
            "relative_include_paths": paths,
            "replayed_relative_include_paths": paths,
            "path_case_policy": "case_sensitive",
            "replayed_path_case_policy": "case_sensitive",
            "include_checksums": checksums,
            "replayed_include_checksums": checksums,
            "override_precedence": "last_include_wins",
            "replayed_override_precedence": "last_include_wins",
            "project_owner": "project:elf-v49-901",
            "replayed_project_owner": "project:elf-v49-901",
            "result_sha256": "7" * 64,
            "accepted_result_sha256": "7" * 64,
        },
    }
    return [deepcopy(identity), deepcopy(identity)]


def test_v49_positive_mao_and_material_replays_are_accepted() -> None:
    assert all(validate_source_v49_identity(_identities()).values())


def test_v49_mao_layout_and_run_owner_mutations_are_rejected() -> None:
    identities = _identities()
    identities[0][MAO]["replayed_endianness"] = "big"
    identities[0][MAO]["replayed_float_precision_bits"] = 32
    identities[0][MAO]["replayed_record_stride_bytes"] = 24
    identities[0][MAO]["replayed_run_owner"] = "run:old"
    assert validate_source_v49_identity(identities)["source_v49_mao_endian_precision_stride_offset_run_owner"] is False


def test_v49_material_path_checksum_precedence_and_owner_mutations_are_rejected() -> None:
    identities = _identities()
    identities[0][MATERIAL]["replayed_relative_include_paths"] = ["Materials/MAGNET.mat", "Materials/BASE.mat"]
    identities[0][MATERIAL]["replayed_include_checksums"] = {"Materials/BASE.mat": "8" * 64}
    identities[0][MATERIAL]["replayed_override_precedence"] = "first_include_wins"
    identities[0][MATERIAL]["replayed_project_owner"] = "project:old"
    assert validate_source_v49_identity(identities)["source_v49_material_path_case_checksum_precedence_project_owner"] is False
