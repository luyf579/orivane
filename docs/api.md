# Public API (development)

This describes the current __all__ exports. Package names are approved as Orivane; APIs are
pre-release. See the linked architecture documents for ownership and failure rules.

## Core: orivane_core

| Export | Contract |
| --- | --- |
| AgentBackend[DepsT, OutputT] | Protocol: async run(request: RunRequest[DepsT]) -> RunResult[OutputT] |
| ToolDefinition[ArgsT, DepsT] | Frozen record: name, description, Pydantic parameters type, async invoke(context, validated_args) returning JsonValue |
| RunRequest[DepsT] | Frozen prompt, context and optional state (default None) |
| RunResult[OutputT] | Frozen output and complete replacement next_state |
| SessionState | Frozen backend_id, format_version, backend_version, opaque payload bytes |
| InMemorySessionRuntime[DepsT, OutputT] | Construct with backend and required positive max_sessions; create_session(id), async run(id, prompt, context), delete_session(id) |
| Workflow[T] | then(name, async_step) and branch(name, sync_bool_predicate, if_true=..., if_false=...) return a new workflow; async run(value) -> T |

Reuse one session runtime on one event loop; unknown IDs fail and deletion requires
idle state. Same-session load/run/commit is serialized. State is memory-only.
Workflows pass values without copying, execute one branch and propagate errors and
cancellation without retry/rollback. See [sessions](architecture/session-runtime.md),
[workflow](architecture/workflow.md) and [tools](architecture/tool-contract.md).

## Backend: orivane_pydantic

| Export | Contract |
| --- | --- |
| PydanticAgentBackend[DepsT, OutputT] | Compatible public PydanticAI Model; explicit output_type; optional instructions/tools and finite request/tool-call limits; implements AgentBackend.run |
| BACKEND_ID | "pydantic-ai" |
| FORMAT_VERSION | 1 |
| BACKEND_VERSION | "2.48.0" |
| validate_session_state(state) | Validate envelope identity/versions without decoding payload; raises ValueError on mismatch |

Models are borrowed; their lifecycle belongs to the application. Native histories
may include sensitive content. Real provider operation is not certified by this
project; the examples use offline TestModel. Configure a desired TracerProvider
before backend construction for native spans. See [backend](architecture/backend-contract.md)
and [observability](architecture/observability.md).

## CLI command interface

`orivane init [PATH]`, `validate [PATH]`, `run [PATH]`, `trace [PATH]`;
PATH defaults to the current directory. Also --help and --version.
Module equivalent: `python -m orivane_cli`. No supported Python library
exports are introduced by the CLI package. See [CLI](cli.md) for strict TOML,
the synchronous zero-argument factory returning an async runner, stdin handling,
safe diagnostics and exit codes 0/1/2/130. No private module is a public API.
