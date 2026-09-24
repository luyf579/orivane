# Contributing

This is a private development repository with provisional package names.
Public API changes should be discussed in an Issue before implementation.
Describe the use case, minimal contract change, compatibility impact, and tests.

## Setup and checks

Use Python 3.11+ and uv 0.12.18+. From the repository root in PowerShell:

```powershell
uv python install 3.11
uv sync --locked --all-packages --python 3.11
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv run --no-sync coverage run -m pytest
uv run --no-sync coverage report
```

Repeat with `--python 3.12` in a separate environment when checking both versions;
see [Python support](docs/development/python-support.md). `python -m uv` is an
equivalent command prefix when the uv executable is not on PATH.
Use `uv run --no-sync ruff format .` to format changes before reviewing the diff.
Commit `uv.lock`; use `--locked` to detect stale manifests. Avoid unrelated upgrades.

## Branch and PR workflow

Check the working tree before creating a `feature/<description>` or
`fix/<description>` branch from main. Do not commit product changes directly to main.
Link the relevant issue, explain public API changes, and attach actual test results.
Run Ruff, strict mypy, and tests for both supported Python versions. Request review
and wait for green CI; do not treat local passing tests as remote CI success.

Never commit secrets, `.env`, tokens, credential files, or local evidence artifacts.
Normal CI must not call real models or require model credentials. Use local fake
backends; future adapter tests should use TestModel/FunctionModel.
Do not publish releases or packages until explicitly approved and branding reviewed.
