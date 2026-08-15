"""Regenerate exact public sample-deck digests in VALIDATED_MANIFEST.json."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "src" / "elf_mcp_server" / "public_samples"
MANIFEST = SAMPLES / "VALIDATED_MANIFEST.json"

SCOPES = {
    "static_input_contract": (
        "Public input-pair presence, syntax, readability, and forbidden-marker checks passed."
    ),
    "ngsolve_proxy_energy": (
        "Public input-contract checks passed and an independent open proxy-field energy sanity check was positive."
    ),
    "ngsolve_numeric_invariant": (
        "Public input-contract checks, analytic FLUM-contract invariants, and independent open proxy invariants passed."
    ),
}

ALLOWED_CHECKS = {
    "input_syntax_lint_passed",
    "mesh_input_readable",
    "forbidden_marker_scan_passed",
    "mai_meg_pair_present",
    "ngsolve_proxy_energy_positive",
    "analytic_flux_invariants_passed",
    "ngsolve_numeric_invariants_passed",
}


def digest(paths: list[Path]) -> str:
    value = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(SAMPLES).as_posix()):
        value.update(path.relative_to(SAMPLES).as_posix().encode("utf-8"))
        value.update(b"\0")
        value.update(path.read_bytes())
        value.update(b"\0")
    return "sha256:" + value.hexdigest()


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    all_files: list[Path] = []
    for family, entry in data["families"].items():
        unexpected = sorted(set(entry["checks"]) - ALLOWED_CHECKS)
        if unexpected:
            raise ValueError(f"{family}: unsupported public check names {unexpected!r}")
        entry["validation_scope"] = SCOPES[entry["validation_level"]]
        family_dir = SAMPLES / family
        files = sorted(
            path
            for path in family_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".mai", ".meg"}
        )
        entry["content_sha256"] = digest(files)
        all_files.extend(files)
    data["content_digest_algorithm"] = "sha256-path-and-bytes-v1"
    data["content_sha256"] = digest(all_files)
    MANIFEST.write_text(
        json.dumps(data, ensure_ascii=True, indent=2) + "\n",
        encoding="ascii",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
