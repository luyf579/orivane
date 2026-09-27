# Versioning

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Current development version is **0.1.0.dev0** for Core, backend and CLI. Keep it for
all Phase 1H local builds. No release candidate or final bump is authorized.

Naming is approved. After license approval, a separately approved release may use optional
`0.1.0rc1`, followed by final `0.1.0`. These are a future sequence, not existing releases.
The three distributions move together in v0; do not version them independently.
Backend/Core are tightly coupled, including a private observability helper within
the monorepo. Backend requires Core == the same version; CLI requires Core and
backend == that version. Published metadata must contain normal requirements,
never workspace=true or a checkout path. Current private Orivane wheels test this rule.

Version, dependency pins, lock, changelog, docs and CLI --version must agree. Do not
rewrite history. Tags/releases/uploads require separate approval after all gates.
PydanticAI and pydantic-graph remain 2.48.0; an upstream upgrade is deferred to a
post-v0.1.0 compatibility PR, independent of release metadata preparation.
