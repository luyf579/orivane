"""Build/audit release artifacts and smoke-test an offline wheelhouse install. No upload."""

import argparse
import email.parser
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKAGES = {
    "core": "orivane_core",
    "backend-pydantic": "orivane_pydantic",
    "cli": "orivane_cli",
    "commerce": "orivane_commerce",
}
UV = ["uv"] if shutil.which("uv") else [sys.executable, "-m", "uv"]
PATH_PATTERN = re.compile(
    rb"(?i)(?:(?<![a-z0-9])[a-z]:[\\/]|" + rb"github-agent-" + rb"framework-lab)"
)
SECRET_PATTERN = re.compile(
    rb"(?:(?<![A-Za-z0-9])sk" + rb"-[A-Za-z0-9_-]{12,}|github_pat" + rb"_[A-Za-z0-9_]+|"
    rb"(?:OPENAI|ANTHROPIC)_API_KEY\s*=|PYPI_API_" + rb"TOKEN|-----BE" + rb"GIN .*PRIVATE KEY)"
)


def check_content(name: str, content: bytes) -> None:
    assert not PATH_PATTERN.search(content), f"Local absolute path: {name} [REDACTED]"
    assert not SECRET_PATTERN.search(content), f"Potential credential: {name} [REDACTED]"


def requirement(value: str) -> tuple[str, tuple[str, ...]]:
    name, spec = re.split(r"(?=[<>=!~])", value.replace(" ", ""), maxsplit=1)
    return name, tuple(sorted(spec.split(",")))


def wheel_files(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as wheel:
        assert wheel.testzip() is None
        return {name: wheel.read(name) for name in wheel.namelist()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    metadata_dir = output / "build-metadata"
    metadata_dir.mkdir()

    def run(
        log: str, command: list[str], cwd: Path = REPO, prompt: str = "", expected_code: int = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            command,
            cwd=cwd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        with (output / log).open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(command)
                + "\n"
                + result.stdout
                + result.stderr
                + f"\nExit code: {result.returncode}\n"
            )
        assert result.returncode == expected_code, f"Unexpected exit code; see {output / log}"
        return result

    first, second = output / "dist", output / "repeat-dist"
    for destination in [first, second]:
        for package in PACKAGES:
            run(
                "build-results.txt",
                [
                    *UV,
                    "build",
                    str(REPO / "packages" / package),
                    "--python",
                    args.python,
                    "--out-dir",
                    str(destination),
                ],
            )
        distributions = [*destination.glob("*.whl"), *destination.glob("*.tar.gz")]
        assert len(list(destination.glob("*.whl"))) == len(PACKAGES)
        assert len(list(destination.glob("*.tar.gz"))) == len(PACKAGES)
        assert set(destination.iterdir()) - set(distributions) <= {destination / ".gitignore"}
    records = []
    for package, module in PACKAGES.items():
        project = tomllib.loads((REPO / "packages" / package / "pyproject.toml").read_text())[
            "project"
        ]
        wheel = next(first.glob(project["name"].replace("-", "_") + "-*.whl"))
        files = wheel_files(wheel)
        assert files == wheel_files(second / wheel.name), "Repeated wheel content changed"
        prefix = project["name"].replace("-", "_") + "-0.2.0.dist-info/"
        expected = {
            str(p.relative_to(REPO / "packages" / package / "src")).replace("\\", "/")
            for p in (REPO / "packages" / package / "src" / module).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        expected |= {prefix + name for name in ["METADATA", "WHEEL", "RECORD", "licenses/LICENSE"]}
        if package == "cli":
            expected.add(prefix + "entry_points.txt")
        assert set(files) == expected, (package, set(files) ^ expected)
        for name, data in files.items():
            check_content(name, data)
        metadata = email.parser.BytesParser().parsebytes(files[prefix + "METADATA"])
        assert metadata["Name"] == project["name"] and metadata["Version"] == "0.2.0"
        assert metadata["Requires-Python"] == ">=3.11"
        assert {requirement(r) for r in metadata.get_all("Requires-Dist", [])} == {
            requirement(r) for r in project["dependencies"]
        }
        assert "Private :: Do Not Upload" not in metadata.get_all("Classifier", [])
        assert set(metadata.get_all("Project-URL", [])) == {
            f"{label}, {url}" for label, url in project["urls"].items()
        }
        assert metadata["Description-Content-Type"] == "text/markdown"
        assert metadata["License-Expression"] == "MIT"
        assert metadata.get_all("License-File") == ["LICENSE"]
        assert files[prefix + "licenses/LICENSE"] == (REPO / "LICENSE").read_bytes()
        assert metadata["Author"] is None and metadata["Maintainer"] is None
        if package != "cli":
            assert module + "/py.typed" in files
        else:
            assert b"orivane = orivane_cli._main:main" in files[prefix + "entry_points.txt"]
        for suffix in ["METADATA", "WHEEL", "entry_points.txt"]:
            if prefix + suffix in files:
                (metadata_dir / (package + "-" + suffix + ".txt")).write_bytes(
                    files[prefix + suffix]
                )
        (metadata_dir / (package + "-wheel-files.json")).write_text(
            json.dumps(sorted(files), indent=2), encoding="utf-8"
        )
        sdist = next(first.glob(project["name"].replace("-", "_") + "-*.tar.gz"))
        with tempfile.TemporaryDirectory(prefix="framework-sdist-") as temp:
            unpacked = Path(temp)
            with tarfile.open(sdist) as archive:
                members = archive.getmembers()
                names = []
                for member in members:
                    assert member.isfile() or member.isdir()
                    relative = Path(member.name).parts[1:]
                    if member.isfile():
                        name = "/".join(relative)
                        names.append(name)
                        assert name in {
                            "README.md",
                            "LICENSE",
                            "pyproject.toml",
                            "PKG-INFO",
                            ".gitignore",
                        } or name.startswith("src/" + module + "/")
                        extracted = archive.extractfile(member)
                        assert extracted is not None
                        content = extracted.read()
                        check_content(name, content)
                        if name == "LICENSE":
                            assert content == (REPO / "LICENSE").read_bytes()
                        if name == "PKG-INFO":
                            sdist_metadata = email.parser.BytesParser().parsebytes(content)
                            for field in [
                                "Name",
                                "Version",
                                "License-Expression",
                                "License-File",
                                "Requires-Python",
                                "Requires-Dist",
                                "Project-URL",
                                "Classifier",
                            ]:
                                assert sorted(sdist_metadata.get_all(field, [])) == sorted(
                                    metadata.get_all(field, [])
                                ), (package, field)
                            (metadata_dir / (package + "-PKG-INFO.txt")).write_bytes(content)
                assert {"README.md", "LICENSE", "pyproject.toml", "PKG-INFO"} <= set(names)
                archive.extractall(unpacked, filter="data")
            run(
                "sdist-rebuild.txt",
                [
                    *UV,
                    "build",
                    str(next(unpacked.iterdir())),
                    "--no-sources",
                    "--wheel",
                    "--python",
                    args.python,
                    "--out-dir",
                    str(unpacked / "rebuilt"),
                ],
                cwd=unpacked,
            )
            assert files == wheel_files(next((unpacked / "rebuilt").glob("*.whl"))), (
                "sdist rebuild content changed"
            )
        (metadata_dir / (package + "-sdist-files.json")).write_text(
            json.dumps(sorted(names), indent=2), encoding="utf-8"
        )
        records.append(
            {
                "package": package,
                "wheel": wheel.name,
                "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "sdist": sdist.name,
                "sdist_sha256": hashlib.sha256(sdist.read_bytes()).hexdigest(),
                "files": len(files),
                "requires_dist": metadata.get_all("Requires-Dist", []),
                "version": metadata["Version"],
                "license": metadata["License-Expression"],
                "requires_python": metadata["Requires-Python"],
                "project_urls": metadata.get_all("Project-URL", []),
                "classifiers": metadata.get_all("Classifier", []),
                "repeat_content": "PASS",
                "sdist_rebuild": "PASS",
            }
        )

    wheelhouse = output / "wheelhouse"
    wheelhouse.mkdir()
    for wheel in first.glob("*.whl"):
        shutil.copy2(wheel, wheelhouse / wheel.name)
    lock = tomllib.loads((REPO / "uv.lock").read_text())
    constraints = output / "constraints.txt"
    constraints.write_text(
        "\n".join(
            f"{p['name']}=={p['version']}" for p in lock["package"] if "registry" in p["source"]
        )
        + "\n",
        encoding="utf-8",
    )
    cli_wheel = next(wheelhouse.glob("orivane_cli-*.whl"))
    commerce_wheel = next(wheelhouse.glob("orivane_commerce-*.whl"))
    run(
        "wheel-install.txt",
        [
            *UV,
            "tool",
            "run",
            "--python",
            args.python,
            "--from",
            "pip==24.2",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--only-binary=:all:",
            "--index-url",
            "https://pypi.org/simple",
            "--dest",
            str(wheelhouse),
            "--find-links",
            str(wheelhouse),
            "--constraint",
            str(constraints),
            str(cli_wheel),
            str(commerce_wheel),
        ],
    )
    with tempfile.TemporaryDirectory(prefix="framework-installed-") as temp:
        root = Path(temp)
        env = root / "venv"
        run("wheel-install.txt", [*UV, "venv", "--python", args.python, str(env)], cwd=root)
        python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        command = env / ("Scripts/orivane.exe" if os.name == "nt" else "bin/orivane")
        run(
            "wheel-install.txt",
            [
                *UV,
                "pip",
                "install",
                "--python",
                str(python),
                "--offline",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                "orivane-cli==0.2.0",
            ],
            cwd=root,
        )
        smoke = """import importlib, importlib.util, json, pathlib, sys
import importlib.metadata as metadata
from orivane_core import (
    AgentBackend, ToolDefinition, RunRequest, RunResult, SessionState,
    InMemorySessionRuntime, Workflow,
)
from orivane_pydantic import (
    PydanticAgentBackend, BACKEND_ID, BACKEND_VERSION, FORMAT_VERSION, validate_session_state,
)
assert importlib.util.find_spec('orivane_commerce') is None
paths = {}
for name in ['orivane_core', 'orivane_pydantic', 'orivane_cli']:
    path = pathlib.Path(importlib.import_module(name).__file__).resolve()
    assert path.is_relative_to(pathlib.Path(sys.prefix).resolve()) and 'site-packages' in path.parts
    paths[name] = str(path)
assert metadata.version('pydantic-ai-slim') == metadata.version('pydantic-graph') == '2.54.0'
assert BACKEND_ID == 'pydantic-ai' and BACKEND_VERSION == '2.54.0' and FORMAT_VERSION == 1
print(json.dumps(paths))
for old in ['agent_framework_core', 'agent_framework_pydantic', 'agent_framework_cli']:
    assert importlib.util.find_spec(old) is None, 'Legacy import must not be installed'
    try:
        importlib.import_module(old)
    except ModuleNotFoundError as error:
        assert error.name == old
    else:
        raise AssertionError('Legacy import must fail')
for old in ['agent-framework-core', 'agent-framework-backend-pydantic', 'agent-framework-cli']:
    try:
        metadata.distribution(old)
    except metadata.PackageNotFoundError:
        pass
    else:
        raise AssertionError('Legacy distribution must not be installed')
for name in ['orivane-core', 'orivane-backend-pydantic', 'orivane-cli']:
    assert metadata.version(name) == '0.2.0'
"""
        run("wheel-install.txt", [str(python), "-I", "-c", smoke], cwd=root)
        result = run("wheel-install.txt", [str(command), "--version"], cwd=root)
        assert result.stdout == "0.2.0\n"
        run("wheel-install.txt", [str(command), "--help"], cwd=root)
        assert not command.with_name(
            "agent-framework.exe" if os.name == "nt" else "agent-framework"
        ).exists()
        for round_number in range(10):
            project_name = f"demo-{round_number}"
            for action in ["init", "validate", "run", "trace"]:
                result = run(
                    "wheel-install.txt",
                    [str(command), action, project_name],
                    cwd=root,
                    prompt="SECRET_PROMPT_PACKAGING",
                )
                assert "SECRET_" not in result.stdout + result.stderr
                if action == "init":
                    assert (root / project_name / "orivane.toml").is_file()
                    assert not (root / project_name / "agent-framework.toml").exists()
                if action == "trace":
                    assert result.stdout.startswith("offline starter\nTRACE\n")
                    structural = result.stdout.split("\nTRACE\n", 1)[1]
                    assert "agent" + "_framework." not in structural
                    rows = [json.loads(line) for line in structural.splitlines()]
                    assert any(row["name"] == "orivane.agent.run" for row in rows)
                    assert any(
                        row["attributes"].get("gen_ai.operation.name") == "chat" for row in rows
                    )
        (root / "demo-0" / "orivane.toml").rename(root / "demo-0" / "agent-framework.toml")
        run("wheel-install.txt", [str(command), "validate", "demo-0"], cwd=root, expected_code=2)
        for source, expected in zip(
            sorted((REPO / "examples").glob("*.py")),
            ["offline agent\n", "offline session\n", "offline workflow\n"],
            strict=True,
        ):
            target = root / source.name
            shutil.copy2(source, target)
            result = run("wheel-install.txt", [str(python), "-I", str(target)], cwd=root)
            assert result.stdout == expected

    with tempfile.TemporaryDirectory(prefix="commerce-installed-") as temp:
        root = Path(temp)
        env = root / "venv"
        log = "commerce-wheel-install.txt"
        run(log, [*UV, "venv", "--python", args.python, str(env)], cwd=root)
        python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run(
            log,
            [
                *UV,
                "pip",
                "install",
                "--python",
                str(python),
                "--offline",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                str(commerce_wheel),
            ],
            cwd=root,
        )
        run(log, [*UV, "pip", "check", "--python", str(python)], cwd=root)
        smoke = """import importlib.util, json, pathlib, sys
import importlib.metadata as metadata
import orivane_commerce
from orivane_commerce import Product, Listing, MarketplaceAdapter
from pydantic import ValidationError

path = pathlib.Path(orivane_commerce.__file__).resolve()
assert path.is_relative_to(pathlib.Path(sys.prefix).resolve()) and 'site-packages' in path.parts
assert path.with_name('py.typed').is_file()
assert orivane_commerce.__all__ == ['Product', 'Listing', 'MarketplaceAdapter']
for name in ['orivane_core', 'orivane_pydantic', 'orivane_cli', 'pydantic_ai']:
    assert importlib.util.find_spec(name) is None, name
installed = {d.metadata['Name'].replace('_', '-').lower() for d in metadata.distributions()}
assert installed == {
    'orivane-commerce', 'pydantic', 'pydantic-core', 'annotated-types',
    'typing-extensions', 'typing-inspection',
}, installed
assert metadata.version('orivane-commerce') == '0.2.0'
product = Product(name='Trowel', attributes={'Product Type': 'tool', 'Color': 'red'})
listing = Listing(title='Trowel', description='Garden tool', language='en', keywords=('garden',))
assert Product.model_validate_json(product.model_dump_json()) == product
assert Listing.model_validate_json(listing.model_dump_json()) == listing
for key in [' Color', 'Color ', '   ']:
    try:
        Product(name='Trowel', attributes={key: 'red'})
    except ValidationError:
        pass
    else:
        raise AssertionError('Surrounding whitespace accepted')
print(json.dumps({'module': str(path), 'installed': sorted(installed), 'roundtrips': 'PASS',
                  'attribute_keys': 'PASS', 'py_typed': True, 'core_backend_cli_absent': True}))
"""
        run(log, [str(python), "-I", "-c", smoke], cwd=root)
    (output / "result.json").write_text(
        json.dumps(
            {
                "packages": records,
                "clean_install": "PASS",
                "commerce_clean_install": "PASS",
                "expected_artifact_count": 2 * len(PACKAGES),
                "cli_roundtrip": "PASS",
                "cli_roundtrip_rounds": 10,
                "legacy_config": "NOT ACCEPTED",
                "legacy_imports_distributions_cli": "NOT INSTALLED",
                "license": "MIT; root, package, wheel and sdist copies match",
                "examples": "PASS",
                "path_scan": "PASS",
                "secret_scan": "PASS",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("PASS: builds, repeat content, sdist rebuild, offline wheel install, CLI and examples")


if __name__ == "__main__":
    main()
