# Versioning

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

Final release preparation replaced 0.1.0rc1 with **0.1.0** consistently in Core,
backend, CLI and the virtual workspace. Commerce 0.1.0 is the fourth distribution,
added in source before the first publication. The source repository is public, but no
Git tag, GitHub Release or PyPI publication exists. PyPI publication is deferred;
tags, Releases and package uploads require separate Maintainer approval.

The four current distributions move together in v0. Backend/Core are tightly coupled,
including a private observability helper. Backend requires Core == the same version;
CLI requires Core and backend == that version. Wheel requirements are ordinary exact
requirements, never workspace=true or checkout paths. CLI --version reads installed
distribution metadata, without a second runtime version constant.
Commerce requires only Pydantic, so it has no internal exact Orivane dependency.
All four package versions remain 0.1.0.

The release preparation lock change was limited to internal Orivane versions;
external packages are frozen.
PydanticAI and pydantic-graph remain 2.48.0; OpenTelemetry API/SDK remain 1.44.0 and
SDK-required semantic conventions remain 0.65b0 (TRANSITIVE). Release preparation
removed Private :: Do Not Upload from the original distributions; all four current
distributions omit it. MIT and naming
approval alone do not authorize package uploads or release tags.

Public APIs follow semantic versioning from v0.1.0 onward, while 0.x minor releases
may intentionally evolve the API with release notes. v0.1.0 is an early release.
