# Versioning

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

The approved final release PR uses **0.1.0** consistently in Core, backend, CLI and
the virtual workspace, replacing 0.1.0rc1. This authorizes package preparation;
Maintainer approval is still required before merging, tagging or publishing.

The three distributions move together in v0. Backend/Core are tightly coupled,
including a private observability helper. Backend requires Core == the same version;
CLI requires Core and backend == that version. Wheel requirements are ordinary exact
requirements, never workspace=true or checkout paths. CLI --version reads installed
distribution metadata, without a second runtime version constant.

The lock change is limited to internal Orivane versions; external packages are frozen.
PydanticAI and pydantic-graph remain 2.48.0; OpenTelemetry API/SDK remain 1.44.0 and
SDK-required semantic conventions remain 0.65b0 (TRANSITIVE). The approved release
PR removes Private :: Do Not Upload from all three distributions. MIT and naming
approval do not authorize publication or another history rewrite.

Public APIs follow semantic versioning from v0.1.0 onward, while 0.x minor releases
may intentionally evolve the API with release notes. v0.1.0 is an early release.
