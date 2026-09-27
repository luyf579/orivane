# Offline examples

From the repository root in PowerShell, after `uv sync --locked --all-packages`:

```powershell
uv run --no-sync python examples/01_offline_agent.py
uv run --no-sync python examples/02_session_runtime.py
uv run --no-sync python examples/03_workflow.py
```

Expected stdout respectively: `offline agent`, `offline session`, `offline workflow`.
No API key or network model request is required. These are executed by pytest and
again against installed wheels in a clean environment. They are Ruff/strict-mypy
checked. The first example is the README quickstart; sessions explicitly create and
delete an in-memory session, and the workflow example exercises both branch paths.
The separate local upstream startup banner may appear on stderr; it is not telemetry.
