# Local packaging verification

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Hatchling remains the build backend. All versions remain 0.1.0.dev0 and retain
Private :: Do Not Upload. Package readmes are self-contained; sdists include only
README, pyproject, source/type markers and build metadata. No project license is
invented: license fields/files wait for the license gate.

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

Then it creates a new unseeded venv outside the repository and installs only the
CLI wheel as the requested package with `uv pip install --offline --no-index
--find-links <wheelhouse>`. Core/backend are resolved from wheel requirements.
It verifies module paths are under that venv's site-packages, runs all examples,
checks help/version and performs init/validate/run/trace with the installed executable.
Core/backend py.typed and dependency direction are verified in actual wheels.
The CLI is a command interface and does not claim an intended typed library API.

CI runs this on both supported Python versions. Results, file lists, METADATA,
entry points, hashes and install transcripts are local artifacts, never uploads.
Supply an unused output directory; the tool refuses to overwrite an earlier run.
