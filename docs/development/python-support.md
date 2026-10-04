# Python support

All workspace projects declare `requires-python = ">=3.11"`. The tested development
baseline is Python 3.11, 3.12 and 3.13. Python 3.13 was added after the Phase 3B
PydanticAI evaluation and full-suite verification; the minimum remains 3.11.

In the historical Phase 1A setup on Windows 11, uv 0.12.18 installed managed
CPython 3.11.16 at user scope without
changing the system default Python association. Existing CPython 3.12.7 remained
available. Both successfully created separate environments with uv and are used for
the local contract/tooling validation recorded in the Phase 1A PR and local evidence.
The current GitHub Actions configuration includes Linux Python 3.11, 3.12 and 3.13
for full checks and packaging. Focused OpenTelemetry jobs cover Python 3.12/3.13
with API/SDK 1.44.0/1.45.0. Local success and configured matrices do not by
themselves certify a remote CI run.

From the repository root in PowerShell, use a separate environment for each version:

```powershell
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) '.venv311'
uv sync --locked --all-packages --python 3.11
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv run --no-sync coverage run -m pytest
uv run --no-sync coverage report

$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) '.venv312'
uv sync --locked --all-packages --python 3.12
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv run --no-sync coverage run -m pytest
uv run --no-sync coverage report

$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) '.venv313'
uv sync --locked --all-packages --python 3.13
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv run --no-sync coverage run -m pytest
uv run --no-sync coverage report
Remove-Item Env:\UV_PROJECT_ENVIRONMENT
```

If uv is not on PATH, use `python -m uv`. A failed check on any tested version is a
blocker; do not silently raise the minimum or remove a matrix entry. Dependencies
and checks are frozen by uv.lock.
CI uses the official [uv Actions integration](https://docs.astral.sh/uv/guides/integration/github/)
and a shared [workspace lock](https://docs.astral.sh/uv/concepts/projects/workspaces/).
