# Versioning

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

The approved RC version is **0.1.0rc1**, consistently used by Core, backend, CLI and
the virtual workspace. It replaces private development 0.1.0.dev0. A separately
approved final release may become 0.1.0; no final bump, tag or upload is authorized here.

The three distributions move together in v0. Backend/Core are tightly coupled,
including a private observability helper. Backend requires Core == the same version;
CLI requires Core and backend == that version. Wheel requirements are ordinary exact
requirements, never workspace=true or checkout paths. CLI --version reads installed
distribution metadata, without a second runtime version constant.

The lock change is limited to workspace RC versions; external packages are frozen.
PydanticAI and pydantic-graph remain 2.48.0; OpenTelemetry API/SDK remain 1.44.0 and
SDK-required semantic conventions remain 0.65b0 (TRANSITIVE). Keep Private :: Do Not
Upload until the separately approved final release. MIT and naming approval do not
authorize publication or a history rewrite.
