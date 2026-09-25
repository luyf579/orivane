# Tracing ownership

Phase 1F implements [observability v0](observability.md): Core owns parent spans,
private run correlation and sensitive-data defaults. The backend enables PydanticAI
model/tool child spans with content capture disabled. Both share OpenTelemetry.
Host applications own sampling, export configuration and telemetry resource lifecycle.
There is no TraceEvent abstraction or framework-installed exporter.

By default, full prompts, tool arguments, secrets, and private product data must not
be sent to remote exporters. Remote export is not required for local development or
CI. Offline tests use in-memory span capture and verify content exclusion and parentage.
