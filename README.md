# agent-framework

Private development repository for a backend-agnostic Python AI agent framework.

Working name. Repository and package names may change before public release.
Names are provisional until pre-public branding review.

This repository is in private development and is **not production ready**.
Agent is the core abstraction. PydanticAI is the first backend; business
code should depend on our contract rather than directly on PydanticAI.
Commerce extension is planned but not in current scope.

## Development status

- `agent-framework-core` / `agent_framework_core`: five public contract types plus
  `InMemorySessionRuntime` for explicit in-process session ordering and `Workflow`
  for typed linear async steps and basic if/else.
- `agent-framework-backend-pydantic` / `agent_framework_pydantic`: real PydanticAI
  backend available in development, with validated tools and native history snapshots.
- PydanticAI is pinned to `pydantic-ai-slim==2.48.0`, the Phase 0 tested baseline.
- No CLI, durable workflow engine, commerce, multi-backend implementation, or public release.

`PydanticAgentBackend` takes a public PydanticAI Model object, an explicit output_type,
optional instructions/tools, and finite request/tool-call budgets (50 each by default).
Only the composition root imports backend/model types; business callers use AgentBackend.
Offline example after development setup:

```python
import asyncio
from agent_framework_core import AgentBackend, RunRequest
from agent_framework_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel


async def main() -> None:
    backend: AgentBackend[None, str] = PydanticAgentBackend(
        TestModel(custom_output_text="done"), output_type=str
    )
    result = await backend.run(RunRequest("hello", None))
    print(result.output)


asyncio.run(main())
```

Only successful runs return a replacement SessionState. Failures propagate without
automatic whole-run retry; tool side effects cannot be rolled back. Cancellation and
borrowed-model ownership are covered by offline tests. Real-provider integration is
not certified. Native histories may contain sensitive inputs; callers must protect them.

For logical session ordering above an existing backend, inside an async caller:

```python
from agent_framework_core import InMemorySessionRuntime

runtime = InMemorySessionRuntime(backend, max_sessions=100)
runtime.create_session("example")
result = await runtime.run("example", "hello", deps)
runtime.delete_session("example")  # requires an idle session
```

Reuse one runtime on one event loop. Creation is explicit, capacity is required, and
unknown IDs fail. Same-session load/run/commit is serialized while different sessions
may overlap. State exists only in memory; no persistence or multi-process guarantee.
See [session runtime](docs/architecture/session-runtime.md) for cancellation, deletion
and capacity rules.

For linear async steps and basic if/else:

```python
import asyncio
from agent_framework_core import Workflow


async def prepare(value: str) -> str:
    return value.strip()


async def revise(value: str) -> str:
    return "ready"


async def accept(value: str) -> str:
    return value


workflow = (
    Workflow[str]()
    .then("prepare", prepare)
    .branch("quality", lambda value: not value, if_true=revise, if_false=accept)
)
assert asyncio.run(workflow.run("  ")) == "ready"
```

Composition returns new workflows; each run executes only the selected branch.
Errors and cancellation propagate without retry or rollback. This is linear only,
with no DAG, Graph or durable workflow. See [Workflow v0](docs/architecture/workflow.md)
for value ownership, concurrency and an example using the owned AgentBackend contract.

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
