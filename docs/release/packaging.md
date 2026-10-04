# Local packaging verification

This document describes the packaging verification used for releases.
v0.1.0 was published on 2026-10-02. Publishing a future version requires separate
Maintainer approval.

Hatchling remains the build backend. The current package version is 0.1.1,
synchronized across the workspace and all four distributions. All four distributions
omit Private :: Do Not Upload. Package readmes are self-contained; sdists include only
README, pyproject, source/type markers, MIT LICENSE and build metadata. Root LICENSE
is canonical; each package has an exact copy checked by tests. SPDX license metadata
and wheel/sdist license bytes are verified against the root file.

From the repository root in PowerShell, after development setup:

```powershell
uv run --no-sync python scripts/packaging_check.py --output artifacts/packaging-311
```

Use the matching Python 3.11/3.12 environment and a new output directory per run.
When uv is only a Python module, run `python scripts/packaging_check.py --python
<path-to-target-python> --output artifacts/packaging-311`; the script locates uv
or uses the launching interpreter's uv module. No production dependency is added.

The script builds each package twice via uv build, audits content and metadata,
unpacks each sdist in a temporary directory and rebuilds it without the repository.
It compares uncompressed wheel content, not ZIP timestamps. It uses pinned pip 24.2
as an isolated download-only tool to populate a platform-specific wheelhouse,
constrained by uv.lock. This tooling is not a runtime or project dependency.
Downloads/build tooling may access public indexes; application smoke tests are offline.

Then it creates a new unseeded venv outside the repository and installs only
`orivane-cli==0.1.1` as the requested package with `uv pip install --offline --no-index
--find-links <wheelhouse>`. Core/backend are resolved from local wheel requirements.
It verifies module paths are under that venv's site-packages, runs all examples,
checks help/version and performs ten init/validate/run/trace rounds with the installed
executable. It rejects the old config filename and verifies that old modules,
distributions, executable and telemetry namespace are absent.
A separate isolated venv installs only the Commerce wheel from the same local
wheelhouse. It verifies imports, JSON round-trips, key validation and py.typed, and
confirms that no Core, backend, CLI or PydanticAI package is installed.
Core/backend/Commerce py.typed and dependency direction are verified in actual wheels.
The CLI is a command interface and does not claim an intended typed library API.

CI runs this on both supported Python versions. Results, file lists, wheel METADATA,
sdist PKG-INFO, entry points, hashes and install transcripts are local evidence.
The tag-only release workflow runs the same validator in a build job and transfers
only its first `dist/` set (four wheels and four sdists; eight validated distributions)
as four GitHub Actions artifacts. Each artifact contains one project's wheel and
sdist: release-orivane-core, release-orivane-backend-pydantic, release-orivane-cli
and release-orivane-commerce. Repeat builds and sdist rebuilds validate those
distributions; there is only one release build job.

Four privileged OIDC publish jobs each download only their own project artifact and
set `packages-dir: dist/`. They run in explicit dependency order: Core, backend, CLI,
then Commerce. They do not check out source, rebuild or run tests. All uploaded
files therefore originate from the same validated build. See [Trusted Publishing](pypi-trusted-publishing.md).
Supply an unused output directory; the tool refuses to overwrite an earlier run.
