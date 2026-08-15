"""Fail unless a release tag exactly matches the package version."""
from __future__ import annotations

import argparse
from pathlib import Path
import tomllib


def package_version(repo: Path) -> str:
    with (repo / "pyproject.toml").open("rb") as stream:
        return str(tomllib.load(stream)["project"]["version"])


def validate_release_tag(tag: str, repo: Path) -> str:
    expected = f"v{package_version(repo)}"
    if tag != expected:
        raise ValueError(f"release tag {tag!r} does not match package version {expected!r}")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag", help="Release tag in vX.Y.Z form")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        expected = validate_release_tag(args.tag, args.repo.resolve())
    except (OSError, KeyError, ValueError) as exc:
        parser.error(str(exc))
    print(f"release tag matches package version: {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
