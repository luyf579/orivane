# Changelog

## Unreleased

### Added

- Separate developer CLI package with safe offline init, static TOML validate, stdin run and local trace.
- Structured lifecycle logging and OpenTelemetry parent spans for workflows, sessions and agents.
- Private run correlation with context restoration and concurrent task isolation.
- Privacy-safe telemetry defaults and PydanticAI native model/tool spans with content capture disabled.
- Typed linear Workflow with explicit named async steps.
- Basic conditional branching with synchronous, strictly boolean predicates.
- Workflow failure/cancellation propagation without implicit retry or rollback.
- InMemorySessionRuntime with explicit logical session identity.
- Per-session in-process serialization and cancellation-safe entry cleanup.
- Explicit session creation, capacity and idle-only deletion semantics.
- Initial workspace.
- Minimal backend contract.
- Development tooling.
- PydanticAI 2.48.0 runtime adapter.
- Validated ToolDefinition bridge.
- Native SessionState round-trip with version guards and safe malformed-state errors.
- Offline backend contract tests migrated from Phase 0 probes.
- Cancellation lifecycle contract with unchanged prior state and no automatic whole-run retry.
- Borrowed Model ownership semantics; v0 owns no external provider/model resources.
- Offline lifecycle regression tests for cancellation, tool cleanup, and borrowed resources.
