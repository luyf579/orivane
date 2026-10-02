# Developer CLI v0

Project, distribution and command names are approved as Orivane. The CLI source is
public, and [`orivane-cli==0.1.0`](https://pypi.org/project/orivane-cli/0.1.0/)
was published on 2026-10-02. It is a separate package; Core and backend public APIs
remain unchanged.

## Install and development invocation

Install with `pipx install orivane-cli`, or `pip install orivane-cli` inside a
Python environment. For development, run from the repository root in PowerShell
using Python 3.11+ and the existing uv tool:

```powershell
uv sync --locked --all-packages --python 3.11
uv run --no-sync orivane --help
uv run --no-sync python -m orivane_cli --version
```

The installed console command `orivane` and `python -m orivane_cli`
use the same entry point. `--version` prints only the CLI distribution version.
Both top-level and per-command help work without importing an application.

## init

From the repository root in PowerShell:

```powershell
uv run --no-sync orivane init demo
```

`init [PATH]` defaults to the current directory. Only a nonexistent or empty directory
is accepted. Existing `app.py`, `orivane.toml`, unrelated files or a file
target cause rejection. There is no `--force`. Template files use exclusive creation;
ordinary write failures clean up only files created by that invocation. Concurrent
external modification of the target directory is not a supported initialization mode.

The fixed, deterministic starter contains `orivane.toml`, `app.py` and
`.gitignore` (ignoring `.env`, `.venv/`, `__pycache__/`, and `*.pyc`). No timestamps,
random identifiers, secret files or dependency installation are generated. Success
prints `INITIALIZED`.

The starter uses PydanticAgentBackend with PydanticAI TestModel. It runs entirely
offline without an API key and returns `offline starter`. Replace TestModel with a
real PydanticAI Model in your own application only when intentionally ready to make
provider calls. The CLI does not choose providers or pay for model calls automatically.

## Configuration

`PATH/orivane.toml` has exactly this v0 schema:

```toml
schema_version = 1

[app]
factory = "app:create_runner"
```

The only top-level fields are `schema_version` and `app`; the only app field is
`factory`. Version must be integer 1 (not a bool, float or string). Missing fields,
unknown fields, invalid TOML and unsupported versions fail with exit code 2.

Factory syntax is `module.path:callable_name`: exactly one colon, non-empty Python
identifiers, no keywords or empty dotted module segments. Nested attribute paths
are not supported. Config does not contain model/provider/API-key settings, tools,
workflow definitions, storage or plugins. No `.env` is loaded automatically.

## Factory convention

The factory is a synchronous zero-argument callable returning a runner callable.
Calling `runner(prompt: str)` must produce an awaitable with an arbitrary result.
Typically the factory closes over the resources and typed context its application
needs, and returns an `async def` function:

```python
from collections.abc import Awaitable, Callable


def create_runner() -> Callable[[str], Awaitable[object]]:
    async def run(prompt: str) -> object:
        return prompt.upper()

    return run
```

This convention is not a new Core interface. The CLI does not require an AgentBackend
return value: AgentBackend.run needs generic context, while real applications may
compose dependency injection, SessionRuntime or Workflow. The closure owns those
choices and any cleanup around its async execution. CLI does not infer or call
close/aclose methods on arbitrary application resources.

## validate

```powershell
uv run --no-sync orivane validate demo
```

`validate [PATH]` defaults to `.` and statically checks only TOML/schema/factory
syntax. It never imports `app.py`, resolves the factory or reads stdin. A valid
configuration prints exactly `VALID` and exits 0, even if its module is not installed.
It cannot certify importability or the runtime factory contract.

## stdin prompt and run

From the repository root in PowerShell:

```powershell
"hello" | uv run --no-sync orivane run demo
```

`run [PATH]` validates config, makes the resolved project root temporarily importable,
loads the module with importlib, resolves/calls its factory, then invokes and awaits
the runner. The whole text stream from stdin is passed unchanged: no strip, truncation
or implicit rejection of empty input. PowerShell's pipe supplies its normal newline.
There is no `--prompt`; the CLI does not require sensitive data in command arguments.
Choose a secure stdin source rather than typing confidential text into shell history.

Success prints `str(result)` to stdout. This is requested application output, not
telemetry, and may intentionally contain private data. CLI does not log it or add
it to spans. Config errors are detected before reading stdin. Import/factory failures
and runner/non-awaitable failures produce safe categories without exception text.

The project root stays importable through execution and sys.path is restored on
success or failure. Each CLI process is intended for one invocation; imported modules
remain in Python's module cache. There is no reload system or sys.modules cleanup.

## trace

```powershell
"hello" | uv run --no-sync orivane trace demo
```

`trace [PATH]` follows the same application convention and stdin contract, but first
creates and installs a local OTel TracerProvider with SimpleSpanProcessor and
InMemorySpanExporter, before even importing the user module or constructing the
factory. This timing makes PydanticAgentBackend's native instrumentation use the
correct provider. A preconfigured provider is rejected with `Trace provider already
configured`; no host provider is replaced and no private reset API is used.

The CLI owns its provider and force-flushes and shuts it down on success, load failure,
runtime failure or cancellation. The one-time global provider remains installed for
the remainder of that process; repeated in-process trace calls are not supported.
`init`, `validate` and ordinary `run` do not install a provider. CLI never imports
Core's private observability helpers; its capture uses the public OTel API/SDK.

On success, output is the application result, then `TRACE` on its own line, then
one JSON structural record per span. Records are sorted by start time with span
name as a deterministic tie-breaker. Equal timestamps need not place parents first;
use parent_span_id to establish the tree. With no captured spans, it prints
`TRACE` followed by `(no spans)` and still succeeds.

Displayed fields are only name, trace_id, span_id, parent_span_id, status code and
an attribute allowlist:

- `orivane.component`, `orivane.operation`
- `orivane.node.name`, `orivane.node.kind`
- `orivane.backend.id`, `orivane.outcome`
- `gen_ai.operation.name`

No events, status descriptions or other attributes are rendered. Trace/span IDs
are formatted as hexadecimal; missing optional IDs are null. JSON escaping keeps
control characters from becoming terminal formatting commands.

## Privacy

CLI diagnostics never print the config, environment, prompt, context, exception
message or traceback. Parse errors also avoid argparse's usual echo of rejected
argument values. The trace formatter uses an allowlist, not a denylist: prompt/output
attributes, tool arguments/results, tool schema defaults/examples, session IDs/payloads,
exception messages/stack traces and provider request bodies are not displayed, even
when present in the captured spans. Application output remains a separate section.

This is a local debugger, not a sandbox. `run` and `trace` intentionally execute trusted
application code, which can print, make network calls, install its own exporters or
perform side effects. The CLI cannot redact arbitrary prints or undo those actions.
Span names and allowlisted structural labels must themselves be non-sensitive.
Only our formatter's output is filtered; the local SDK can hold additional attributes
from arbitrary application spans in memory until process exit. Default framework
telemetry still follows [its content-exclusion policy](architecture/observability.md).

The CLI adds no logging handlers or remote exporter. PydanticAI's independent local
startup banner may appear on stderr in interactive environments; hosts can disable
it through the public opt-out documented in the observability guide. No telemetry
is uploaded by the CLI.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success (including help/version and trace with no spans) |
| 1 | Application load/runtime failure or preconfigured trace provider |
| 2 | Invalid CLI/config or unsafe/failed initialization |
| 130 | KeyboardInterrupt or cancellation reaching the CLI boundary |

Application-raised SystemExit is treated as an application failure (1), not as CLI
process control. argparse help/version and invalid usage retain their exit codes.

Errors are not retried. The runner's application-level side effects remain its owner's
responsibility. Errors default to category/type only; no custom error hierarchy is
added to Core.

## Limitations

One stdin stream maps to one invocation. No persistent sessions or `--session`, REPL,
multi-turn shell, interactive menus, provider schema, cloud exporter, plugin manager,
web UI, commerce or release publishing. TOML is the only v0 format; YAML/JSON support
may be considered later with a concrete requirement.

CLI directly depends on exact workspace Core/backend versions and OTel SDK >=1.44,<2.
Core keeps its direct OTel API dependency. The development lock resolves SDK 1.44.0
and semantic-conventions 0.65b0; public installs may resolve newer versions within
the declared ranges. Semantic conventions is an SDK transitive dependency, not a
direct declaration or project import.
PydanticAI and pydantic-graph stay at 2.48.0. No CLI framework/parser/template dependency
was added. See [ADR-0005](adr/0005-cli-v0.md).
