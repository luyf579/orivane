# agent-framework

Private development repository for a backend-agnostic Python AI agent framework.

Working name. Repository and package names may change before public release.
Names are provisional until pre-public branding review.

This repository is in private development and is **not production ready**.
Agent is the core abstraction. PydanticAI is the first planned backend; business
code should depend on our contract rather than directly on PydanticAI.
Commerce extension is planned but not in current scope.

## Phase 1A status

- `agent-framework-core` / `agent_framework_core`: five public contract types.
- `agent-framework-backend-pydantic` / `agent_framework_pydantic`: package boundary
  and session compatibility guards only; actual Agent execution is not implemented.
- PydanticAI is pinned to `pydantic-ai-slim==2.48.0`, the Phase 0 tested baseline.
- No CLI, workflow engine, commerce, multi-backend implementation, or public release.

## Development

Python 3.11+ and uv 0.12.18+. Run from the repository root in PowerShell:

```powershell
uv sync --locked --all-packages --python 3.11
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv run --no-sync coverage run -m pytest
uv run --no-sync coverage report
```

If uv is installed as a Python user package but its executable is not on PATH,
replace `uv` with `python -m uv`. Normal tests need no real model credentials.
Do not publish these provisional distribution names to PyPI.

See [contributing](CONTRIBUTING.md), [contract](docs/architecture/backend-contract.md),
[ADR-0001](docs/adr/0001-default-agent-backend.md), and
[Python support](docs/development/python-support.md).
