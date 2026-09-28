# Contributing

This is the public Orivane development repository. Contributions are welcome.
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

Check the working tree before creating a `feature/<description>`,
`fix/<description>` or approved `release/<version>` branch from main.
Do not commit product changes directly to main.
Link the relevant issue, explain public API changes, and attach actual test results.
Run Ruff, strict mypy, and tests for both supported Python versions. Request review
and wait for green CI; do not treat local passing tests as remote CI success.

Never commit secrets, `.env`, tokens, credential files, or local evidence artifacts.
Normal CI must not call real models or require model credentials. Use local fake
backends; future adapter tests should use TestModel/FunctionModel.
Do not publish releases or packages until explicitly approved and licensed.

Package/release changes require Maintainer approval. Naming and MIT are approved;
PyPI publication is currently deferred. Never reserve names by uploading placeholder packages.
Run the [local packaging checks](docs/release/packaging.md) for changes to manifests,
sdist/wheel inclusion or entry points. All distributions and internal exact requirements
now use 0.1.0; tag creation and publishing still require separate authorization.
See the [Trusted Publishing setup](docs/release/pypi-trusted-publishing.md).
The [offline examples](examples/README.md) are tested and included
in strict mypy; update them alongside documented API usage.
