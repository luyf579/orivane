# Minimal Backend Contract v0

Phase 0 established one replaceable runtime boundary: an Agent's complete async run.
Phase 1A established the following five types in `agent_framework_core`; Phase 1B
keeps their source and public API unchanged:

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

Core will own session identity, persistence policy, and same-session serialization.
Commit replacement state only after success. Failed runs do not roll back tool
side effects; never blindly rerun a whole Agent as a retry. Durable checkpoints,
exactly-once execution, cancellation/resource lifecycle, and cross-backend conversion
are not implemented by these records.

## Validation and migration

Phase 1A tests cover typed tool definitions, context preservation, opaque state,
structural async protocol use, dependency direction, and version rejection.
Future runtime tests must cover structured output, tool retry validation before
side effects, history round-trips, limits, failure persistence, cancellation, and
resource closure. Phase 1B now covers structured output, validation retries, history
round-trips, finite limits and failure non-commit. Cancellation, resource ownership,
and same-session serialization remain open in Issue #6; the adapter neither persists
sessions nor closes a caller-supplied Model. A second backend must pass the same applicable contract tests.
Existing native sessions stay with their original backend; prefer new sessions
when switching. Define tested conversion only when lossless migration is required.

See [tool rules](tool-contract.md), [workflow scope](workflow-scope.md),
[trace scope](tracing-scope.md), and [ADR-0001](../adr/0001-default-agent-backend.md).
