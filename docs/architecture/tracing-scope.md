# Future tracing ownership

Core owns parent spans, run correlation, sampling/export policy, and sensitive-data
policy. The backend emits model/tool child spans. Both will share OpenTelemetry.
Phase 1A adds neither instrumentation nor a TraceEvent abstraction.

By default, full prompts, tool arguments, secrets, and private product data must not
be sent to remote exporters. Remote export is not required for local development or
CI. Future tests should use in-memory span capture and verify redaction and parentage.
