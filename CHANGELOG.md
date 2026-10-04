# Changelog

## Unreleased

### Changed

- Prepare the synchronized 0.2.0 workspace and four distributions as unreleased
  development source. The latest published release remains v0.1.1.
- Upgrade the backend baseline from pydantic-ai-slim 2.48.0 to 2.54.0, with matching
  pydantic-graph 2.54.0 and the required genai-prices 0.1.9 lock update.
- Change the public BACKEND_VERSION value to 2.54.0 and accept only that exact
  native SessionState version before decoding. Old 2.48.0 snapshots are rejected
  without automatic migration, a compatibility window or a migration utility.
  Applications persisting state must start a new session or explicitly own its
  migration. Core contract shapes, exports and API signatures remain unchanged.
- Add Python 3.13 to the tested Python 3.11/3.12/3.13 baseline and the checks and
  packaging CI matrices; requires-python remains >=3.11. The focused OpenTelemetry
  CI matrix covers Python 3.12/3.13 with API/SDK 1.44.0/1.45.0.

## 0.1.1 - 2026-10-04

### Fixed

- Normalize allowlisted CLI trace attributes before JSON formatting, so UTF-8 bytes
  retained by OpenTelemetry 1.45 do not cause a TypeError. Recursively normalize
  lists and tuples; replace invalid UTF-8 bytes and unsupported values with fixed
  structural markers without printing their raw contents.
- Preserve the trace attribute allowlist and application failure behavior. Core,
  backend and Commerce runtime code and public APIs are unchanged.

## 0.1.0 - 2026-10-02

### Changed

- Approved Orivane repository, distribution, import and executable names; local config is orivane.toml.
- MIT adopted; all four distributions use 0.1.0 with included license files.
- Private package classifiers removed for final release review.
- Published the four 0.1.0 distributions through GitHub OIDC Trusted Publishing.
- Published the v0.1.0 GitHub Release.
- PyPI artifacts include publish attestations.
- Pre-public telemetry schema migrates to Orivane with no legacy aliases.
- Existing public exports, execution behavior and privacy guarantees are preserved.

### Added

- Experimental `orivane-commerce` source package with Product, Listing and MarketplaceAdapter.
- Package metadata/readmes, wheel/sdist and isolated installation checks.
- Offline executable examples, public API documentation, and naming/license/publication gates.
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
- Typed AgentBackend contract.
- Development tooling.
- PydanticAI 2.48.0 runtime adapter.
- Validated ToolDefinition bridge.
- Native SessionState round-trip with version guards and safe malformed-state errors.
- Offline backend contract tests migrated from Phase 0 probes.
- Cancellation lifecycle contract with unchanged prior state and no automatic whole-run retry.
- Borrowed Model ownership semantics; v0 owns no external provider/model resources.
- Offline lifecycle regression tests for cancellation, tool cleanup, and borrowed resources.
