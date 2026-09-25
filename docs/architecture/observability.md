# Observability v0

## Purpose

Correlate Workflow, SessionRuntime and PydanticAgentBackend operations with structural
stdlib logs and OpenTelemetry spans. Observability is private infrastructure: both
packages keep their existing public exports and call signatures. No TraceEvent or
additional configuration/provider abstraction is introduced.

## Structured logging

Stable event names are LogRecord messages; structured values are LogRecord `extra`
fields. The framework installs no handler or formatter and never calls `basicConfig`
or changes logger levels. All lifecycle events use INFO, including error/cancel
events, so unconfigured logging does not trigger Python's WARNING-level lastResort
handler. Applications can filter on `af_outcome` instead of severity.

Each operation emits `.start` followed by one `.end`, `.error`, or `.cancel` event.
Ordinary handler/formatter exceptions are isolated and never replace a business
result or exception. Disabled loggers avoid constructing LogRecord fields. No input
serialization or repr is performed on either logging path.

## Logger names

| Logger | Event prefixes |
| --- | --- |
| `agent_framework.workflow` | `workflow.run`, `workflow.node` |
| `agent_framework.session` | `session.run` |
| `agent_framework.backend.pydantic` | `agent.run` |

## Stable structural fields

`af_event`, `af_component`, `af_operation`, `af_run_id`, and `af_duration_ms` identify
events. Terminal records add `af_outcome` (`success`, `error`, `cancelled`). Failure
and cancellation add only `af_error_type`, never the exception text or traceback.
Duration uses `perf_counter_ns`, converted to milliseconds; start records use zero.

Nodes add `af_node_name` and `af_node_kind` (`step` or `branch`). Backend operations
add `af_backend_id` (`pydantic-ai`). When the current span context is valid, records
include 32-digit hexadecimal `af_trace_id` and 16-digit `af_span_id`. No-op contexts
omit these fields; the framework does not invent trace IDs.

## Run correlation

A private ContextVar holds an opaque UUID string. The outermost instrumented
operation creates it, nested operations inherit it, and token reset restores the
previous context on every exit, including failure and cancellation. This run_id
is a framework correlation identifier, separate from the OTel trace_id.

Independent asyncio tasks started outside a framework operation receive different
run IDs. Tasks intentionally spawned inside a run inherit Python's context and
therefore its correlation, as ordinary child work should. There is no process-wide
mutable current ID. A host parent span can contain multiple independent framework
runs, each with its own run_id but sharing the host's trace_id.

## OpenTelemetry spans

Stable framework span names are:

```text
agent_framework.workflow.run
  agent_framework.workflow.node
    agent_framework.session.run
      agent_framework.agent.run
        PydanticAI agent/model/tool spans
```

This is an example call chain, not a required topology. A node may call the backend
directly or call no Agent at all. A branch uses one node span around both its
predicate and selected callable, with no additional decision span. User values,
session IDs and node names never become framework span names.

Framework attributes are `agent_framework.run_id`, `.component`, `.operation`,
`.node.name`, `.node.kind`, `.backend.id`, and `.outcome`, as applicable. Error spans
also contain `error.type` and ERROR status without a description. Framework spans
disable automatic exception events and automatic exception status descriptions.
Cancelled operations have outcome `cancelled` and leave status UNSET.

Session spans include lock waiting, execution and commit. Retain still happens
synchronously before awaiting the per-session lock, state is loaded after lock
acquisition and committed before unlock, and cancellation releases the entry.
Tracing introduces no await or execution lock and does not alter session ordering.

## Privacy defaults

Framework never logs raw prompts/contexts/results by default. It records no raw
session ID, SessionState payload, tool arguments/results, native message history,
provider request body, API key, exception message or stack trace. It does not hash
session IDs or collect additional state metadata.

Blocking offline tests serialize every captured LogRecord field and complete SDK
span JSON, including names, attributes, events and status descriptions. Sentinels
exercise prompts, context, outputs, tools, restored session history, session IDs,
instructions and model/tool exceptions. Exception objects still reach callers
unchanged. No remote service or credential is involved.

Structural labels are developer-supplied metadata: choose non-sensitive node/tool
names, tool descriptions, model names and schemas. PydanticAI still emits model/tool
identity, usage and tool schema definitions even with content capture disabled.
Do not embed secrets or private product data in those definitions (including schema
defaults/examples). The framework does not scrub arbitrary host instrumentation,
third-party provider instrumentation, baggage, or host parent spans that separately
record exceptions. Native history retained for session functionality is still
sensitive application data; these telemetry rules do not anonymize stored state.

## PydanticAI integration

Pinned PydanticAI 2.48.0 supports public per-Agent
`capabilities=[Instrumentation(settings=InstrumentationSettings(...))]`. Each
adapter-created Agent receives `include_content=False`, `include_binary_content=False`
and `include_model_request_parameters=False`. It uses the host TracerProvider and
does not call `Agent.instrument_all` or change another Agent's configuration.

The installed 2.48.0 source and offline tests verify that content-disabled native
model/tool/agent spans withhold exception messages and stack traces as well as
prompt/tool/result content. Tests identify native spans by their `pydantic-ai`
instrumentation scope and `gen_ai.operation.name` (`chat`, `execute_tool`), rather
than relying on every upstream span name. Both PydanticAI and pydantic-graph remain
2.48.0. Native child tracing is enabled; the privacy deferral gate was not needed.

The native instrumentation can also emit usage metrics through the host's OTel
MeterProvider; the framework installs no meter provider, reader or exporter.

## Cancellation/errors

Failures propagate with original identity and without retries or rollback. A
cancelled call emits cancel lifecycle events and re-raises CancelledError. Ordinary
framework logging/span setup, attribute and finalization failures are best effort
and isolated from business work; context cleanup still runs. No telemetry errors
are logged recursively. This does not promise recovery from a broken third-party
native instrumentation implementation, fatal BaseException raised by host hooks,
or a blocking handler/exporter. Host hooks should be non-blocking and reliable.

## Host configuration responsibility

The application owns logging handlers, levels and formatting, OTel SDK providers,
sampling, processors, exporters and resource lifecycle. Configure these before
constructing backends. For local development a host can opt into stdlib logging:

```python
import logging

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s run=%(af_run_id)s"))
logger = logging.getLogger("agent_framework")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
# At application shutdown: logger.removeHandler(handler); handler.close()
```

This example is application configuration; no such setup runs during framework
import or construction. A host choosing OTel SDK tracing must install its provider,
select its standard sampler, and own processor/exporter flush and shutdown. The
framework neither flushes nor shuts down borrowed providers, log handlers, models
or clients. Tests use isolated providers and shut them down after each capture.

## No exporter by default

With no SDK provider or logging configuration, execution produces no framework
telemetry output and uses OTel API no-op behavior. Framework source imports no SDK/exporter/processor;
it neither installs a global TracerProvider nor adds custom sampling. A host sampler
can drop all spans without changing execution. Nothing uploads telemetry by default.
Ordinary CI uses only an InMemorySpanExporter in tests, never remote credentials.

PydanticAI 2.48.0 separately prints a once-per-process local startup banner in
interactive/coding-agent environments. This preexisting upstream UI is not telemetry
export and does not include run content. Hosts requiring completely silent stderr
can set the public `pydantic_ai.BANNER_ENABLED = False` before running, or set
`PYDANTIC_AI_NO_BANNER=1` in their process environment. The framework does neither:
it does not override the application's global banner policy. A fresh-process test
removes pytest/CI suppression and verifies both this boundary and the public opt-out.

## Limitations

DIRECT production dependency: `opentelemetry-api>=1.44,<2` in Core.
DEV DIRECT dependency: `opentelemetry-sdk>=1.44,<2` at the workspace root.
EXPECTED TRANSITIVE dependency: `opentelemetry-semantic-conventions==0.65b0`, required
by SDK 1.44.0. It is neither a direct dependency nor imported by project code/tests.
The API and SDK currently resolve to 1.44.0; no unrelated direct dependency is added.

No OTLP, Jaeger, Zipkin, Logfire, Langfuse, hosted integration, exporter, custom sampler,
JSON formatter, trace-event bus, session pseudonymization, durable tracing or CLI is
provided. Emission is best effort; there is no completeness/delivery guarantee.
See [ADR-0004](../adr/0004-observability-v0.md).
