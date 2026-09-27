from pathlib import Path

import pytest


@pytest.mark.parametrize("package", ["core", "backend-pydantic", "cli"])
def test_package_license_matches_canonical_root_license(package: str) -> None:
    root = Path(__file__).resolve().parents[2]
    canonical = (root / "LICENSE").read_bytes()
    assert b"Copyright (c) 2026 Orivane contributors" in canonical
    assert (root / "packages" / package / "LICENSE").read_bytes() == canonical
