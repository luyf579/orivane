# Python support

All workspace projects declare `requires-python = ">=3.11"`. Phase 1A checks Python
3.11 and 3.12; later versions are not yet certified by the CI matrix.

On Windows 11, uv 0.12.18 installed managed CPython 3.11.16 at user scope without
changing the system default Python association. Existing CPython 3.12.7 remained
available. Both successfully created separate environments with uv and are used for
the local contract/tooling validation recorded in the Phase 1A PR and local evidence.
GitHub Actions independently runs Linux Python 3.11 and 3.12; local success does not
by itself certify remote CI.

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
Remove-Item Env:\UV_PROJECT_ENVIRONMENT
```

If uv is not on PATH, use `python -m uv`. A failed 3.11 check is a blocker; do not
silently raise the minimum to 3.12. Dependencies and checks are frozen by uv.lock.
CI uses the official [uv Actions integration](https://docs.astral.sh/uv/guides/integration/github/)
and a shared [workspace lock](https://docs.astral.sh/uv/concepts/projects/workspaces/).
