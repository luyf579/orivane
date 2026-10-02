# Orivane

A small, typed Python runtime for building backend-adaptable AI agents, sessions,
workflows, observability, and developer tooling.

Orivane v0.1.0 is an early release under the MIT license. The source repository is
**public**. The repository's tag-triggered GitHub Actions workflow uses Trusted
Publishing to release the four Python distributions.

Public APIs follow semantic versioning from v0.1.0 onward, while 0.x minor releases
may intentionally evolve the API with release notes. Orivane is not production ready.
Agent is the core abstraction. PydanticAI is the first backend; business
code should depend on our contract rather than directly on PydanticAI.
Orivane includes an experimental platform-neutral Commerce domain package.

## Current features

- `orivane-core` / `orivane_core`: five public contract types plus
  `InMemorySessionRuntime` for explicit in-process session ordering and `Workflow`
  for typed linear async steps and basic if/else.
- `orivane-backend-pydantic` / `orivane_pydantic`: real PydanticAI
  backend available in development, with validated tools and native history snapshots.
- PydanticAI is pinned to `pydantic-ai-slim==2.48.0`, the Phase 0 tested baseline.
- `orivane-cli` / `orivane_cli`: local init, validate, run and trace commands.
- No durable workflow engine or second backend.

## Experimental commerce domain

`orivane-commerce` is an experimental platform-neutral Commerce domain package.
It provides Product, Listing, and MarketplaceAdapter only.
Install with `pip install orivane-commerce`.
See the [commerce architecture](docs/architecture/commerce.md).
It provides no marketplace implementations, publishing, ingestion, or Listing Agent.

## Core concepts and backend

The [public API guide](docs/api.md) covers AgentBackend, typed requests/results,
validated tools, opaque SessionState, sessions and workflows. `PydanticAgentBackend`
takes a public PydanticAI Model object, an explicit output_type,
optional instructions/tools, and finite request/tool-call budgets (50 each by default).
Only the composition root imports backend/model types; business callers use AgentBackend.
Offline example after development setup:

```python
import asyncio

from orivane_core import AgentBackend, RunRequest
from orivane_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel


async def main() -> None:
    backend: AgentBackend[None, str] = PydanticAgentBackend(
        TestModel(custom_output_text="offline agent"), output_type=str
    )
    result = await backend.run(RunRequest("hello", None))
    assert result.output == "offline agent"
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

Only successful runs return a replacement SessionState. Failures propagate without
automatic whole-run retry; tool side effects cannot be rolled back. Cancellation and
borrowed-model ownership are covered by offline tests. Real-provider integration is
not certified. Native histories may contain sensitive inputs; callers must protect them.

## Session

For logical session ordering above an existing backend, inside an async caller:

```python
from orivane_core import InMemorySessionRuntime

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

## Workflow

For linear async steps and basic if/else:

```python
import asyncio
from orivane_core import Workflow


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

## CLI quickstart

Install the CLI and run in a directory where you want to create a new project.
These commands work in Windows PowerShell:

```powershell
pipx install orivane-cli
orivane init demo
cd demo
orivane validate .
echo "hello" | orivane run .
echo "hello" | orivane trace .
```

PowerShell can also use `"hello" | orivane run .`. During development,
developers can use the workspace setup below and prefix each `orivane` invocation
with `uv run --no-sync` from the repository root.

The generated starter uses offline `TestModel` and needs no API key. `validate` does not read
stdin or import the application. `run` and `trace` read the whole prompt from stdin;
trace displays a local structural span list after the application result. Names are
approved as Orivane. See [CLI documentation](docs/cli.md) for configuration, factory convention,
privacy and exit codes.

## Observability

The framework emits structural lifecycle logging and OpenTelemetry spans, with
private run correlation across Workflow, sessions and backend calls. Raw prompts,
contexts, outputs and tool content are excluded; PydanticAI native child spans use
content capture disabled. No telemetry is uploaded by default.

The host application controls logging handlers/levels, TracerProvider, sampler,
exporters and their lifecycle. See [observability](docs/architecture/observability.md)
for privacy boundaries and configuration responsibility.

## Installation and development

Install the distribution needed by your application:

```powershell
pip install orivane-core
pip install orivane-backend-pydantic
pipx install orivane-cli
pip install orivane-commerce
```

Alternatively, use `pip install orivane-cli` inside your Python environment.
The CLI installs matching Core and PydanticAI backend distributions automatically.
For local development, use the uv workspace below or locally built wheels.

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
Do not publish until the separate publication approval is complete.

See [contributing](CONTRIBUTING.md), [contract](docs/architecture/backend-contract.md),
[ADR-0001](docs/adr/0001-default-agent-backend.md), and
[Python support](docs/development/python-support.md).

Run the [three offline examples](examples/README.md) after setup; tests execute them
on both supported Python versions. The [documentation index](docs/README.md) links
all architecture, API, CLI and release preparation documents.

## Limitations

Only the PydanticAI backend is implemented and pinned to 2.48.0. Sessions are in
memory; same-session serialization covers one process and one event loop. Workflows
are linear with basic branching. There is no durable workflow, persistent memory,
multi-agent orchestration, commerce platform integration, plugin ecosystem or real-provider
certification matrix. Applications own model resources, side effects, native-history
protection and telemetry configuration.

## Contributing and release preparation

See [CONTRIBUTING](CONTRIBUTING.md) for setup, checks and review. Package/release
changes require Maintainer approval. The [public release checklist](docs/release/checklist.md)
and [packaging verification](docs/release/packaging.md) describe validation and remaining
publication steps. Read the [v0.1.0 release notes](docs/release/v0.1.0.md) and
[Trusted Publishing setup](docs/release/pypi-trusted-publishing.md). The source
repository is public; tags, GitHub Releases and package uploads require separate
Maintainer authorization.

## License

MIT. See [LICENSE](LICENSE) and the [dependency license review](docs/release/license-review.md).
Dependencies retain their own licenses. No public author or maintainer identity is
invented in package metadata.
