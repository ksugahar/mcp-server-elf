"""Public-package policy lint for ELF-mcp-server.

The public ELF MCP package is a documentation/input-deck server. This lint
guards the publish boundary that matters most for the public repository:
no private validation provenance, no machine-local paths, no unrelated
commercial-tool promotion, and no unsafe bundled solver outputs in public
samples.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
import sys
import zipfile


TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".txt", ".mai", ".meg", ".yaml", ".yml"}

CURATED_PATHS = (
    ".github",
    "LICENSE",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "docs",
    "pyproject.toml",
    "scripts",
    "src/elf_mcp_server",
    "tests",
)

PRIVATE_MARKERS = (
    "S:\\",
    "S:/",
    "W:\\",
    "W:/",
    "C:\\temp",
    "C:\\ELF600",
    "C:/ELF600",
    "_crossval",
    "internal:",
    "LAB private",
    "COMSOL_Multiphysics_MCP",
    "FEMM",
    "JMAG",
    "elf_converter",
    "Math" + "Works",
    "MAT" + "LAB MCP Server",
)

SAMPLE_OUTPUT_SUFFIXES = (".mao", ".mag", ".mat", ".mac")
SAMPLE_OUTPUT_MARKERS = SAMPLE_OUTPUT_SUFFIXES + ("summary.csv",)
FORBIDDEN_BUNDLED_NAMES = {
    "help_dump.json",
    "examples_dump.json",
    "wiki_dump.json",
    "python_dump.json",
}
MANIFEST_NAME = "VALIDATED_MANIFEST.json"
PUBLICATION_BATCHES_NAME = "PUBLICATION_BATCHES.json"
PUBLICATION_CHECKPOINT_SIZE = 100
VALIDATION_LEVELS = {
    "static_input_contract",
    "ngsolve_proxy_energy",
    "ngsolve_numeric_invariant",
}
LEVEL_REQUIRED_CHECKS = {
    "static_input_contract": {
        "input_syntax_lint_passed",
        "mesh_input_readable",
        "forbidden_marker_scan_passed",
        "mai_meg_pair_present",
    },
    "ngsolve_proxy_energy": {
        "input_syntax_lint_passed",
        "mesh_input_readable",
        "forbidden_marker_scan_passed",
        "mai_meg_pair_present",
        "ngsolve_proxy_energy_positive",
    },
    "ngsolve_numeric_invariant": {
        "input_syntax_lint_passed",
        "mesh_input_readable",
        "forbidden_marker_scan_passed",
        "mai_meg_pair_present",
        "analytic_flux_invariants_passed",
        "ngsolve_numeric_invariants_passed",
    },
}


def _iter_text_files(root: Path, rel_roots: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for rel in rel_roots:
        path = root / rel
        if not path.exists():
            continue
        if path.is_file():
            candidates = [path]
        else:
            candidates = [p for p in path.rglob("*") if p.is_file()]
        for candidate in candidates:
            if candidate.name == "policy_lint.py":
                continue
            if candidate.suffix.lower() in TEXT_SUFFIXES:
                files.append(candidate)
    return sorted(set(files))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp932", errors="replace")


def _sample_families(samples: Path) -> dict[str, list[Path]]:
    """Return public sample family -> case directories for bundled decks."""
    families: dict[str, list[Path]] = {}
    if not samples.exists():
        return families
    for family_dir in sorted(p for p in samples.rglob("*") if p.is_dir()):
        cases = []
        for candidate in sorted(p for p in family_dir.iterdir() if p.is_dir()):
            case = candidate.name
            if (candidate / f"{case}.mai").exists() and (candidate / f"{case}.meg").exists():
                cases.append(candidate)
        if cases:
            families[family_dir.relative_to(samples).as_posix()] = cases
    return families


def _content_digest(paths: list[Path], base: Path) -> str:
    """Bind paths and LF-normalized text bytes into one SHA-256 digest."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(base).as_posix()):
        digest.update(path.relative_to(base).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _validate_public_sample_manifest(repo: Path, samples: Path) -> list[str]:
    """Ensure bundled sample decks are exactly the validation-passed manifest."""
    issues: list[str] = []
    actual = _sample_families(samples)
    manifest_path = samples / MANIFEST_NAME
    rel_manifest = manifest_path.relative_to(repo).as_posix()
    if not manifest_path.exists():
        return [f"{rel_manifest}: missing validated sample manifest"]

    manifest_text = _read_text(manifest_path)
    for marker in PRIVATE_MARKERS:
        if marker in manifest_text:
            issues.append(f"{rel_manifest}: contains private marker {marker!r}")

    try:
        manifest = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        return [f"{rel_manifest}: invalid JSON ({exc})"]

    manifest_families = manifest.get("families")
    if not isinstance(manifest_families, dict):
        return [f"{rel_manifest}: missing families object"]

    actual_names = set(actual)
    manifest_names = set(manifest_families)
    for family in sorted(actual_names - manifest_names):
        issues.append(f"{rel_manifest}: sample family {family!r} is not listed as validated")
    for family in sorted(manifest_names - actual_names):
        issues.append(f"{rel_manifest}: listed family {family!r} is not present in public_samples")

    total_cases = 0
    total_input_files = 0
    for family in sorted(actual_names & manifest_names):
        entry = manifest_families[family]
        if not isinstance(entry, dict):
            issues.append(f"{rel_manifest}: family {family!r} entry must be an object")
            continue
        if entry.get("validation") != "passed":
            issues.append(f"{rel_manifest}: family {family!r} is not marked validation='passed'")
        level = entry.get("validation_level")
        if level not in VALIDATION_LEVELS:
            issues.append(
                f"{rel_manifest}: family {family!r} has invalid validation_level={level!r}"
            )
        checks = entry.get("checks")
        if not isinstance(checks, list) or not all(isinstance(c, str) for c in checks):
            issues.append(f"{rel_manifest}: family {family!r} checks must be a string list")
            checks_set = set()
        else:
            checks_set = set(checks)
        if level in LEVEL_REQUIRED_CHECKS:
            missing = sorted(LEVEL_REQUIRED_CHECKS[level] - checks_set)
            if missing:
                issues.append(
                    f"{rel_manifest}: family {family!r} validation_level={level!r} "
                    f"missing checks {missing!r}"
                )
        scope = entry.get("validation_scope")
        if not isinstance(scope, str) or not scope.strip():
            issues.append(f"{rel_manifest}: family {family!r} missing validation_scope")
        if "ngsolve_proxy_energy_positive" in checks_set and level != "ngsolve_proxy_energy":
            issues.append(
                f"{rel_manifest}: family {family!r} has ngsolve proxy check but "
                f"validation_level={level!r}"
            )
        if "ngsolve_numeric_invariants_passed" in checks_set and level != "ngsolve_numeric_invariant":
            issues.append(
                f"{rel_manifest}: family {family!r} has numeric invariant check but "
                f"validation_level={level!r}"
            )
        cases = actual[family]
        actual_count = len(cases)
        total_cases += actual_count
        total_input_files += actual_count * 2
        if entry.get("cases") != actual_count:
            issues.append(
                f"{rel_manifest}: family {family!r} cases={entry.get('cases')!r} "
                f"does not match actual {actual_count}"
            )
        if entry.get("input_files") != actual_count * 2:
            issues.append(
                f"{rel_manifest}: family {family!r} input_files={entry.get('input_files')!r} "
                f"does not match actual {actual_count * 2}"
            )
        family_files = [
            case_dir / f"{case_dir.name}{suffix}"
            for case_dir in cases
            for suffix in (".mai", ".meg")
        ]
        expected_family_digest = _content_digest(family_files, samples)
        if entry.get("content_sha256") != expected_family_digest:
            issues.append(
                f"{rel_manifest}: family {family!r} content_sha256 does not match files"
            )
        for case_dir in cases:
            case = case_dir.name
            for suffix in (".mai", ".meg"):
                expected = case_dir / f"{case}{suffix}"
                if not expected.exists():
                    rel = expected.relative_to(repo).as_posix()
                    issues.append(f"{rel}: missing required public input-deck pair file")

    if manifest.get("total_cases") != total_cases:
        issues.append(
            f"{rel_manifest}: total_cases={manifest.get('total_cases')!r} "
            f"does not match actual {total_cases}"
        )
    if manifest.get("total_input_files") != total_input_files:
        issues.append(
            f"{rel_manifest}: total_input_files={manifest.get('total_input_files')!r} "
            f"does not match actual {total_input_files}"
        )
    all_input_files = [
        case_dir / f"{case_dir.name}{suffix}"
        for cases in actual.values()
        for case_dir in cases
        for suffix in (".mai", ".meg")
    ]
    if manifest.get("content_digest_algorithm") != "sha256-path-and-lf-normalized-bytes-v1":
        issues.append(f"{rel_manifest}: unsupported or missing content_digest_algorithm")
    if manifest.get("content_sha256") != _content_digest(all_input_files, samples):
        issues.append(f"{rel_manifest}: top-level content_sha256 does not match files")
    issues.extend(
        _validate_publication_batches(
            repo=repo,
            samples=samples,
            actual=actual,
            manifest_families=manifest_families,
            total_cases=total_cases,
        )
    )

    return issues


def _validate_publication_batches(
    repo: Path,
    samples: Path,
    actual: dict[str, list[Path]],
    manifest_families: dict[str, dict],
    total_cases: int,
) -> list[str]:
    """Validate the public 100-case publication checkpoint manifest."""
    issues: list[str] = []
    batches_path = samples / PUBLICATION_BATCHES_NAME
    rel_batches = batches_path.relative_to(repo).as_posix()
    if not batches_path.exists():
        return [f"{rel_batches}: missing 100-case publication batch manifest"]

    batches_text = _read_text(batches_path)
    for marker in PRIVATE_MARKERS:
        if marker in batches_text:
            issues.append(f"{rel_batches}: contains private marker {marker!r}")
    try:
        data = json.loads(batches_text)
    except json.JSONDecodeError as exc:
        return [f"{rel_batches}: invalid JSON ({exc})"]

    checkpoint_size = data.get("checkpoint_size")
    if checkpoint_size != PUBLICATION_CHECKPOINT_SIZE:
        issues.append(
            f"{rel_batches}: checkpoint_size={checkpoint_size!r} "
            f"must be {PUBLICATION_CHECKPOINT_SIZE}"
        )
        checkpoint_size = PUBLICATION_CHECKPOINT_SIZE

    actual_paths: dict[str, str] = {}
    for family, case_dirs in actual.items():
        level = manifest_families.get(family, {}).get("validation_level")
        for case_dir in case_dirs:
            case = case_dir.name
            rel_path = (case_dir / f"{case}.mai").relative_to(samples).as_posix()
            actual_paths[rel_path] = level

    batches = data.get("batches")
    if not isinstance(batches, list) or not batches:
        return [f"{rel_batches}: batches must be a non-empty list"]

    seen: list[str] = []
    full_batches = 0
    remainder_cases = 0
    expected_start = 1
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            issues.append(f"{rel_batches}: batch #{index + 1} must be an object")
            continue
        paths = batch.get("case_paths")
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            issues.append(f"{rel_batches}: {batch.get('batch_id', index + 1)!r} case_paths must be a string list")
            paths = []
        case_count = len(paths)
        if batch.get("case_count") != case_count:
            issues.append(
                f"{rel_batches}: {batch.get('batch_id', index + 1)!r} "
                f"case_count={batch.get('case_count')!r} does not match {case_count}"
            )
        if batch.get("case_start") != expected_start:
            issues.append(
                f"{rel_batches}: {batch.get('batch_id', index + 1)!r} "
                f"case_start={batch.get('case_start')!r} does not match {expected_start}"
            )
        expected_end = expected_start + case_count - 1
        if batch.get("case_end") != expected_end:
            issues.append(
                f"{rel_batches}: {batch.get('batch_id', index + 1)!r} "
                f"case_end={batch.get('case_end')!r} does not match {expected_end}"
            )
        expected_start = expected_end + 1

        is_last = index == len(batches) - 1
        if case_count == checkpoint_size:
            full_batches += 1
            expected_kind = "full_100"
        elif is_last and 0 < case_count < checkpoint_size:
            remainder_cases = case_count
            expected_kind = "release_remainder"
        else:
            issues.append(
                f"{rel_batches}: {batch.get('batch_id', index + 1)!r} "
                f"has invalid checkpoint size {case_count}"
            )
            expected_kind = batch.get("batch_kind")
        if batch.get("batch_kind") != expected_kind:
            issues.append(
                f"{rel_batches}: {batch.get('batch_id', index + 1)!r} "
                f"batch_kind={batch.get('batch_kind')!r} should be {expected_kind!r}"
            )

        level_counts: dict[str, int] = {}
        for rel_path in paths:
            level = actual_paths.get(rel_path)
            if level is None:
                issues.append(f"{rel_batches}: {rel_path!r} is not a public .mai sample path")
            else:
                level_counts[level] = level_counts.get(level, 0) + 1
        if batch.get("validation_level_counts") != dict(sorted(level_counts.items())):
            issues.append(
                f"{rel_batches}: {batch.get('batch_id', index + 1)!r} "
                "validation_level_counts does not match manifest levels"
            )
        seen.extend(paths)

    seen_set = set(seen)
    actual_set = set(actual_paths)
    if len(seen) != len(seen_set):
        issues.append(f"{rel_batches}: case_paths contain duplicates")
    for path in sorted(actual_set - seen_set)[:10]:
        issues.append(f"{rel_batches}: missing public case path {path!r}")
    for path in sorted(seen_set - actual_set)[:10]:
        issues.append(f"{rel_batches}: unknown public case path {path!r}")

    expected_remainder = total_cases % checkpoint_size
    if data.get("total_cases") != total_cases:
        issues.append(f"{rel_batches}: total_cases={data.get('total_cases')!r} does not match actual {total_cases}")
    if data.get("total_batches") != len(batches):
        issues.append(f"{rel_batches}: total_batches={data.get('total_batches')!r} does not match {len(batches)}")
    if data.get("full_100_case_batches") != full_batches:
        issues.append(
            f"{rel_batches}: full_100_case_batches={data.get('full_100_case_batches')!r} "
            f"does not match {full_batches}"
        )
    if data.get("remainder_cases") != expected_remainder:
        issues.append(
            f"{rel_batches}: remainder_cases={data.get('remainder_cases')!r} "
            f"does not match {expected_remainder}"
        )
    expected_next = total_cases + checkpoint_size if expected_remainder == 0 else total_cases + (checkpoint_size - expected_remainder)
    if data.get("next_checkpoint_cases") != expected_next:
        issues.append(
            f"{rel_batches}: next_checkpoint_cases={data.get('next_checkpoint_cases')!r} "
            f"does not match {expected_next}"
        )
    expected_needed = expected_next - total_cases
    if data.get("additional_cases_needed_for_next_100_case_checkpoint") != expected_needed:
        issues.append(
            f"{rel_batches}: additional_cases_needed_for_next_100_case_checkpoint="
            f"{data.get('additional_cases_needed_for_next_100_case_checkpoint')!r} "
            f"does not match {expected_needed}"
        )
    if remainder_cases != expected_remainder:
        issues.append(
            f"{rel_batches}: release-remainder batch has {remainder_cases} cases, "
            f"expected {expected_remainder}"
        )
    return issues


def _validate_mcp_quality_gates() -> list[str]:
    """Mirror the MCP-visible publication gates in policy lint."""
    issues: list[str] = []
    try:
        from .sample_decks import build_public_quality_gates
    except ImportError:
        src_root = Path(__file__).resolve().parents[1]
        if str(src_root) not in sys.path:
            sys.path.insert(0, str(src_root))
        try:
            from elf_mcp_server.sample_decks import build_public_quality_gates
        except Exception as exc:  # pragma: no cover - defensive CLI import guard.
            return [f"public quality gates could not be loaded: {exc}"]
    except Exception as exc:  # pragma: no cover - defensive CLI import guard.
        return [f"public quality gates could not be loaded: {exc}"]

    for gate in build_public_quality_gates():
        if gate.get("status") != "PASS":
            issues.append(
                f"public quality gate {gate.get('gate', '<unknown>')!r} failed: "
                f"{gate.get('detail', '')}"
            )
    return issues


def run_policy_lint(root: Path | str | None = None) -> list[str]:
    """Return policy-lint issue strings for a repository root."""
    repo = Path(root) if root is not None else Path.cwd()
    repo = repo.resolve()
    issues: list[str] = []

    for path in repo.rglob("*"):
        if path.is_file() and path.name.lower() in FORBIDDEN_BUNDLED_NAMES:
            issues.append(
                f"{path.relative_to(repo).as_posix()}: product-derived dump is not allowed"
            )

    for path in _iter_text_files(repo, CURATED_PATHS):
        rel = path.relative_to(repo).as_posix()
        text = _read_text(path)
        for marker in PRIVATE_MARKERS:
            if marker in text:
                issues.append(f"{rel}: contains private marker {marker!r}")

    samples = repo / "src" / "elf_mcp_server" / "public_samples"
    if samples.exists():
        issues.extend(_validate_public_sample_manifest(repo, samples))
        issues.extend(_validate_mcp_quality_gates())
        for path in sorted(p for p in samples.rglob("*") if p.is_file()):
            rel = path.relative_to(repo).as_posix()
            suffix = path.suffix.lower()
            if suffix in SAMPLE_OUTPUT_SUFFIXES or path.name.lower() == "summary.csv":
                issues.append(f"{rel}: solver output file is not allowed")
            if suffix in {".mai", ".meg"}:
                text = _read_text(path)
                for marker in SAMPLE_OUTPUT_MARKERS + PRIVATE_MARKERS:
                    if marker in text:
                        issues.append(f"{rel}: contains forbidden marker {marker!r}")

    return issues


def audit_wheel(wheel: Path | str) -> list[str]:
    """Audit the files that will actually be installed from a wheel."""
    path = Path(wheel).resolve()
    issues: list[str] = []
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        return [f"{path.name}: invalid wheel ({exc})"]
    with archive:
        names = archive.namelist()
        lower_names = {name.lower() for name in names}
        if not any(name.endswith("/THIRD_PARTY_NOTICES.md") for name in names):
            issues.append(f"{path.name}: THIRD_PARTY_NOTICES.md is missing from wheel")
        for name in names:
            pure = Path(name)
            lower = name.lower()
            if pure.name.lower() in FORBIDDEN_BUNDLED_NAMES:
                issues.append(f"{path.name}:{name}: product-derived dump is not allowed")
            if lower.endswith(SAMPLE_OUTPUT_SUFFIXES) or lower.endswith("summary.csv"):
                issues.append(f"{path.name}:{name}: solver output file is not allowed")
            if lower == "elf_mcp_server/policy_lint.py":
                # The lint module necessarily contains the marker dictionary.
                # Repository sources are audited separately, excluding this file.
                continue
            if pure.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                text = archive.read(name).decode("utf-8")
            except (KeyError, UnicodeDecodeError):
                issues.append(f"{path.name}:{name}: declared text file is not UTF-8")
                continue
            for marker in PRIVATE_MARKERS:
                if marker in text:
                    issues.append(f"{path.name}:{name}: contains private marker {marker!r}")
        required = {
            "elf_mcp_server/runtime.py",
            "elf_mcp_server/handlers.py",
            "elf_mcp_server/tool_definitions.py",
            "elf_mcp_server/mcp_resources.py",
            "elf_mcp_server/models.py",
        }
        missing = sorted(item for item in required if item.lower() not in lower_names)
        issues.extend(f"{path.name}: missing required runtime file {item}" for item in missing)
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the public repository and built wheel")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--wheel", action="append", default=[], help="Wheel path or glob; repeatable")
    parsed = parser.parse_args(sys.argv[1:] if argv is None else argv)
    issues = run_policy_lint(parsed.root)
    wheel_paths: list[str] = []
    for pattern in parsed.wheel:
        matches = glob.glob(pattern)
        wheel_paths.extend(matches or [pattern])
    for wheel in wheel_paths:
        issues.extend(audit_wheel(wheel))
    if issues:
        print("ELF MCP policy lint FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("ELF MCP policy lint PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
