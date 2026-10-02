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
        r"^\| (orivane-[^ ]+) \| luyf579 \| orivane \| release\.yml \| (pypi[^ ]*) \|$",
        (ROOT / "docs/release/pypi-trusted-publishing.md").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert len(publishers) == len(packages)
    assert dict(publishers) == {
        "orivane-core": "pypi",
        "orivane-backend-pydantic": "pypi-backend-pydantic",
        "orivane-cli": "pypi-cli",
        "orivane-commerce": "pypi-commerce",
    }
    assert {project for project, _ in publishers} == {project["name"] for project in projects}
    graph = (ROOT / "docs/release/dependency-graph.md").read_text(encoding="utf-8")
    assert set(re.findall(r"^\| (orivane-[^ ]+) \|", graph, re.MULTILINE)) == {
        project for project, _ in publishers
    }


def _release_jobs() -> dict[str, str]:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    blocks = re.split(
        r"^  ([a-z][a-z0-9-]+):\n", workflow.split("jobs:\n", 1)[1], flags=re.MULTILINE
    )
    jobs = dict(zip(blocks[1::2], blocks[2::2], strict=True))
    assert len(jobs) == len(blocks[1::2])
    return jobs


def _job_steps(job: str) -> list[str]:
    return re.split(r"^      - ", job, flags=re.MULTILINE)[1:]


def test_release_workflow_artifact_count_and_labels_match_packages(tmp_path: Path) -> None:
    packages = _release_packages()
    assert len(packages) == 4
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    dist = tmp_path / "artifacts/release/dist"
    dist.mkdir(parents=True)
    expected_files: dict[str, set[str]] = {}
    for package in packages:
        project = tomllib.loads((ROOT / "packages" / package / "pyproject.toml").read_text())[
            "project"
        ]["name"]
        prefix = project.replace("-", "_")
        files = {f"{prefix}-{version}-py3-none-any.whl", f"{prefix}-{version}.tar.gz"}
        expected_files[project] = files
        for name in files:
            (dist / name).touch()
    assert len(list(dist.iterdir())) == 8
    build = _release_jobs()["build"]
    assert build.count("scripts/packaging_check.py") == 1
    uploads = [step for step in _job_steps(build) if "uses: actions/upload-artifact@" in step]
    assert len(uploads) == 4
    seen: set[str] = set()
    for step in uploads:
        assert "uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in step
        project = re.findall(r"^          name: release-(orivane-\S+)$", step, re.MULTILINE)[0]
        patterns = re.findall(r"^            (artifacts/release/dist/\S+)$", step, re.MULTILINE)
        assert len(patterns) == 2
        matched = {path.name for pattern in patterns for path in tmp_path.glob(pattern)}
        assert matched == expected_files[project]
        assert "if-no-files-found: error" in step
        seen.add(project)
    assert seen == set(expected_files)


@pytest.mark.parametrize("package", ["core", "backend-pydantic", "cli", "commerce"])
def test_publish_job_downloads_only_its_project_artifact(package: str) -> None:
    project = tomllib.loads((ROOT / "packages" / package / "pyproject.toml").read_text())[
        "project"
    ]["name"]
    job = _release_jobs()[f"publish-{package}"]
    steps = _job_steps(job)
    assert len(steps) == 2
    assert "uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in steps[0]
    assert re.findall(r"^          name: (\S+)$", steps[0], re.MULTILINE) == [f"release-{project}"]
    assert "          path: dist/" in steps[0]
    assert "uses: pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33" in steps[1]
    assert "          packages-dir: dist/" in steps[1]
    assert "skip-existing" not in job
    assert "checkout" not in job and "run:" not in job
    assert "secrets." not in job


def test_release_publish_order_and_environment_mapping() -> None:
    jobs = _release_jobs()
    expected = {
        "publish-core": ("build", "pypi"),
        "publish-backend-pydantic": ("publish-core", "pypi-backend-pydantic"),
        "publish-cli": ("publish-backend-pydantic", "pypi-cli"),
        "publish-commerce": ("publish-cli", "pypi-commerce"),
    }
    assert list(jobs) == ["build", *expected]
    for name, (needs, environment) in expected.items():
        assert re.findall(r"^    needs: (\S+)$", jobs[name], re.MULTILINE) == [needs]
        assert f"    environment:\n      name: {environment}\n" in jobs[name]


def test_release_trigger_and_oidc_permissions_remain_restricted() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert workflow.split("jobs:\n", 1)[0] == (
        'name: Release\non:\n  push:\n    tags:\n      - "v*"\n\npermissions:\n  contents: read\n\n'
    )
    jobs = _release_jobs()
    assert "id-token:" not in jobs["build"]
    for name, job in jobs.items():
        if name != "build":
            assert re.findall(r"^      (contents|id-token): (\S+)$", job, re.MULTILINE) == [
                ("contents", "read"),
                ("id-token", "write"),
            ]
    assert "contents: write" not in workflow and "packages: write" not in workflow
    assert "secrets." not in workflow
