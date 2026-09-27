# Rename impact

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

Before the first public v0.1.0 release, rename cost remains bounded: this is private
development, there is no published compatibility promise, and there are three small
workspace packages. The user approved Orivane and accepted GitHub same-name risk.
The coordinated rename changes repository/distribution/import/executable identities,
current documentation and tooling. No git history or historical issue text is rewritten.

| Area | Coordinated rename scope |
| --- | --- |
| Repository | Update repository name/URLs with explicit approval |
| Distributions / imports | Update directories, imports, requirements and metadata together |
| CLI | Rename console script and module invocation documentation/tests |
| README / docs / examples | Update current instructions, links and terminology |
| pyproject / uv.lock | Change package identities, resolve without unrelated upgrades |
| GitHub Actions / tests | Update selectors and verify installed-wheel behavior |
| ADRs | Annotate historical provisional decisions and update current references |
| Issues | Preserve historical issue text; link the new decision when appropriate |
| Git history | Preserve it; no rewrite |

Full tests, type checks, wheel/sdist builds and clean installs verify the renamed packages. Inspect
dependency direction and console/import names in artifacts, not just source search.

## Pre-public RC telemetry migration

0.1.0rc1 makes a clean break from the private telemetry schema: logger/tracer/span
and attribute prefix `agent_framework` becomes `orivane`; structured log prefix
`af_` becomes `orivane_`. No old/new aliases are emitted. The logger names are
orivane.workflow, orivane.session and orivane.backend.pydantic. Span names remain
low-cardinality: orivane.workflow.run, orivane.workflow.node, orivane.session.run and
orivane.agent.run. The actual log fields are event, component, operation, run_id,
outcome, duration_ms, node_name, node_kind, backend_id, trace_id, span_id and error_type,
each with the new prefix. Standard gen_ai.operation.name and error.type are unchanged.

Privacy sentinels, parentage, cancellation, failure handling and CLI's structural
allowlist remain enforced. The change introduces no public API symbol or additional
content capture. Runtime, tests and current instructions use the new names; this
section records the old namespace solely for migration review.
