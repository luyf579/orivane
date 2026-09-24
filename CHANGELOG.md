# Changelog

## Unreleased

### Added

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
