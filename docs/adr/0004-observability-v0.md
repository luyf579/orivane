# ADR-0004: Observability v0

Status: Accepted

## Decision

Use stdlib logging with stable LogRecord extra fields, and OpenTelemetry API spans
with private UUID correlation through a ContextVar. Do not add a logging abstraction,
TraceEvent model, observer bus or Core public type. Context inheritance naturally
connects Workflow nodes, SessionRuntime and AgentBackend calls while isolating
independent asyncio tasks. Reset the context on all exit paths.

The host controls handlers, levels, provider, sampling, export and shutdown. Framework
code installs no exporter, custom sampler or global logging/OTel configuration.
Unconfigured execution emits no framework telemetry; tests use the SDK's in-memory
exporter only. PydanticAI's independent local startup banner remains host-controlled.

Record structural identity, outcomes and monotonic duration. Exclude raw prompts,
contexts, outputs, tool arguments/results, session IDs/payloads, exception messages
and stack traces. Disable OTel's automatic exception capture for framework spans;
record ERROR status and error type manually. CancelledError propagates as cancellation.
Ordinary framework telemetry errors must not replace business results or exceptions.

Native PydanticAI spans are allowed only with content-safe public configuration.
The pinned 2.48.0 per-Agent Instrumentation capability supports content, binary
content and model-request-parameter capture switches. All are disabled; offline
sentinel tests verify native model/tool content and exception privacy. No private
upstream API, global `instrument_all`, version upgrade or exporter is used.

## Consequences

Add opentelemetry-api directly to Core, opentelemetry-sdk directly to dev dependencies,
and accept the SDK's required transitive semantic-conventions package. The Maintainer
confirmed this distinction on 2026-09-25; semantic-conventions is not directly declared
or imported. Existing contracts and public signatures stay unchanged.

The host must use non-sensitive structural labels/schemas and manage its own telemetry
resources. Framework safeguards do not scrub arbitrary host or provider instrumentation.
Sampling and failed telemetry hooks may omit observations. No CLI, hosted observability
service, JSON formatter or automatic remote export is part of this decision.
