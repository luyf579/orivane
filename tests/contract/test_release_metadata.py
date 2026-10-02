import ast
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _release_packages() -> dict[str, str]:
    tree = ast.parse((ROOT / "scripts/packaging_check.py").read_text(encoding="utf-8"))
    value = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "PACKAGES" for target in node.targets)
    )
    packages: dict[str, str] = ast.literal_eval(value)
    return packages


@pytest.mark.parametrize("package", ["core", "backend-pydantic", "cli", "commerce"])
def test_package_license_matches_canonical_root_license(package: str) -> None:
    root = Path(__file__).resolve().parents[2]
    canonical = (root / "LICENSE").read_bytes()
    assert b"Copyright (c) 2026 Orivane contributors" in canonical
    assert (root / "packages" / package / "LICENSE").read_bytes() == canonical


def test_release_packages_and_trusted_publishers_match_workspace() -> None:
    packages = _release_packages()
    workspace = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert len(packages) == 4
    assert {f"packages/{name}" for name in packages} == set(
        workspace["tool"]["uv"]["workspace"]["members"]
    )
    projects = [
        tomllib.loads((ROOT / "packages" / name / "pyproject.toml").read_text())["project"]
        for name in packages
    ]
    assert {project["version"] for project in projects} == {workspace["project"]["version"]}
    publishers = re.findall(
        r"^\| (orivane-[^ ]+) \| luyf579 \| orivane \| release\.yml \| pypi \|$",
        (ROOT / "docs/release/pypi-trusted-publishing.md").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert len(publishers) == len(packages)
    assert set(publishers) == {project["name"] for project in projects}
    graph = (ROOT / "docs/release/dependency-graph.md").read_text(encoding="utf-8")
    assert set(re.findall(r"^\| (orivane-[^ ]+) \|", graph, re.MULTILINE)) == set(publishers)


def test_release_workflow_artifact_count_and_labels_match_packages() -> None:
    package_count = len(_release_packages())
    artifact_count = package_count * 2  # One wheel and one sdist per package.
    assert package_count == 4 and artifact_count == 8
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "- name: Build and validate all four distributions" in workflow
    assert "- name: Store the eight validated distributions" in workflow
    assert re.findall(r"^\s+(artifacts/release/dist/\S+)$", workflow, re.MULTILINE) == [
        "artifacts/release/dist/*.whl",
        "artifacts/release/dist/*.tar.gz",
    ]
