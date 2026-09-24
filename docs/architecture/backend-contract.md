# Minimal Backend Contract v0

Phase 0 established one replaceable runtime boundary: an Agent's complete async run.
Phase 1A established the following five types in `agent_framework_core`; Phases 1B/1C
keep their source and public API unchanged:

| Type | Fields / method |
|---|---|
| `ToolDefinition[ArgsT, DepsT]` | name, description, parameters: type[ArgsT], invoke |
| `SessionState` | backend_id, format_version, backend_version, payload: bytes |
| `RunRequest[DepsT]` | prompt, context, state (optional) |
| `RunResult[OutputT]` | output, next_state |
| `AgentBackend[DepsT, OutputT]` | async run(request) -> RunResult |

ArgsT is a Pydantic BaseModel subclass. An owned async tool accepts DepsT and a
validated ArgsT, returning a JSON value. Records are frozen dataclasses; contained
context and outputs are not deeply frozen. Protocol compatibility is structural
and checked statically, not through runtime inheritance or isinstance checks.

No ModelBackend, ProviderBackend, ToolCall, Message, TraceEvent, universal context,
graph, MCP, memory hierarchy, or plugin abstraction is added. Configuration such as
instructions, model, tools, and provider settings belongs to the future composition
root/adapter, not each RunRequest. Core must not import PydanticAI or its adapter.

## Runtime adapter

`PydanticAgentBackend[DepsT, OutputT]` structurally implements AgentBackend. Construct
it with a public PydanticAI Model instance, explicit output_type, instructions, and
owned tools. request_limit and tool_calls_limit default to 50; both must be finite
non-negative integers. Zero denies requests/tool calls. Native UsageLimits enforce
these per run; the adapter does not implement separate token accounting.

The tool collection erases only the heterogeneous parameter-model type using one
local Any annotation. Each ToolDefinition still holds its own parameter model and
invoke together, and the bridge validates that exact model. DepsT and OutputT stay
typed, without casts, global ignores, or changes to Core variance.

## State ownership

Core does not decode SessionState.payload. Native histories preserve provider and
tool metadata that a role/content representation would lose. SessionState does not
promise lossless migration across backends. next_state replaces the complete prior
snapshot; never append it again to old history.

The adapter's guard currently accepts backend_id `pydantic-ai`, format_version `1`,
and backend_version `2.48.0` only. All three mismatches raise ValueError. No silent
reset or history drop is allowed. The exported validate_session_state helper still
checks only the envelope. Runtime restoration calls it first, then parses payload
with public ModelMessagesTypeAdapter. Malformed native JSON/schema raises a generic
ValueError without including payload contents or displaying the validation cause.
Successful runs use all_messages_json() once to return the full replacement snapshot.
No native message type is added to Core. Histories themselves retain upstream data,
including prompts/tool arguments; error redaction is not payload anonymization.

Commit replacement state only after success. Failed runs do not roll back tool
side effects; never blindly rerun a whole Agent as a retry. Durable checkpoints,
exactly-once execution, and cross-backend conversion are not implemented by these records.

## Resource ownership

The caller-supplied Model is **borrowed**. The backend does not close it after
success, failure, cancellation, or backend destruction, and provides no close/aclose
method. Provider/client lifecycle remains the composition root's responsibility.
The v0 backend creates no provider client, HTTP client, database client, or network
session; there are no backend-owned external provider/model resources to close.
Future backend-owned resources require an explicit ownership design before implementation.

The Agent object is adapter-created and adapter-owned. For the tested PydanticAI
2.48.0 public API path (a directly supplied Model and ordinary function tools), no
explicit adapter shutdown action is required. This does not claim Agent has no
lifecycle API: Agent and Model have public async context hooks. This adapter does
not enter an Agent context or manage those hooks for the borrowed model. Upstream
capability-owned models and resource-owning toolsets are outside this v0 contract.
Do not infer support for every provider's lifecycle from the offline tests.

The sentinel tests assert that close, aclose, __exit__, and __aexit__ are not called
on the borrowed model, including after dropping the backend. The close/aclose and
synchronous exit sentinels guard against future duck-typed cleanup by our backend;
they do not assert that those methods are part of PydanticAI's Model interface.

## Cancellation

The backend does not shield Agent.run, swallow asyncio cancellation, or translate
CancelledError into an ordinary exception or a tool retry. Cancellation during a
model request or an awaiting business tool propagates to the caller. Tool finally
blocks run as Python unwinds the cancellation; the adapter does not automatically
retry the complete Agent run.

An unsuccessful run returns no RunResult, so no replacement SessionState is
available to commit. The adapter itself has no state store or commit operation.
Cancellation with prior history leaves the caller-owned snapshot byte-for-byte
unchanged. Already completed external tool side effects cannot be rolled back;
callers must not blindly retry cancelled runs when tools may have side effects.
Offline tests use asyncio.Event handshakes and bounded waits, not timing sleeps.

## Same-session serialization

AgentBackend itself does not serialize concurrent runs belonging to one logical
session. Caller/Core runtime must eventually provide logical session identity and
serialization; the design is left to Phase 1D and remains open in Issue #6.
The current contract has no session_id, store, executor, or lock ownership. Do not
infer identity from id(SessionState), payload hashes, prompt text, or context
identity. No global/backend-wide lock is added to serialize unrelated sessions,
and this phase makes no broader concurrency guarantee.

## Validation and migration

Phase 1A tests cover typed tool definitions, context preservation, opaque state,
structural async protocol use, dependency direction, and version rejection.
Phase 1B covers structured output, validation retries before side effects, history
round-trips, finite limits and failure non-commit. Phase 1C adds offline model/tool
cancellation, prior-state preservation, and borrowed-resource lifecycle regressions
on Python 3.11/3.12, without changing Core public API or the pinned PydanticAI version.
Owned-external-resource closure is N/A in v0; it needs tests if ownership is introduced.
Same-session serialization remains open in Issue #6; the adapter does not persist
sessions. A second backend must pass the same applicable contract tests.
Existing native sessions stay with their original backend; prefer new sessions
when switching. Define tested conversion only when lossless migration is required.

See [tool rules](tool-contract.md), [workflow scope](workflow-scope.md),
[trace scope](tracing-scope.md), and [ADR-0001](../adr/0001-default-agent-backend.md).
