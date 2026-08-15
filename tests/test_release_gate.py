from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_release_tag import package_version, validate_release_tag


def test_release_tag_must_exactly_match_package_version() -> None:
    repo = Path(__file__).resolve().parents[1]
    version = package_version(repo)
    assert validate_release_tag(f"v{version}", repo) == f"v{version}"
    with pytest.raises(ValueError, match="does not match"):
        validate_release_tag("v0.0.0", repo)
