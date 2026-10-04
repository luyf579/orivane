# Versioning

v0.1.0 was first published on 2026-10-02. Core, backend, CLI and Commerce are the
four distributions. The latest published release remains **v0.1.1**.
The current synchronized source/package version is **0.2.0, unreleased development
source**, including the virtual workspace and all four package versions.
The source repository is public, and releases use the tag-triggered Trusted Publishing workflow.
Future releases require separate Maintainer approval and follow the
[subsequent-release process](pypi-trusted-publishing.md#subsequent-releases).

The four current distributions move together in v0. Backend/Core are tightly coupled,
including a private observability helper. Backend requires Core == the same version;
CLI requires Core and backend == that version. Wheel requirements are ordinary exact
requirements, never workspace=true or checkout paths. CLI --version reads installed
distribution metadata, without a second runtime version constant.
Commerce requires only Pydantic, so it has no internal exact Orivane dependency.
All four current development package versions are 0.2.0.

The approved development dependency change upgrades PydanticAI and pydantic-graph
from 2.48.0 to 2.54.0, with genai-prices 0.1.8 to 0.1.9 as the required transitive
lock update. No other external or development-tool dependency changes are included.
PydanticAI and pydantic-graph are pinned to 2.54.0. The development lock resolves
OpenTelemetry API/SDK 1.44.0 and SDK-required semantic conventions 0.65b0 (TRANSITIVE).
Public installs may resolve newer OpenTelemetry versions within the declared >=1.44,<2
ranges; those dependencies are not exact pins. Release preparation removed
Private :: Do Not Upload from the original distributions; all four current
distributions omit it. MIT and naming approval alone do not authorize future
package uploads or release tags.

Public APIs follow semantic versioning from v0.1.0 onward, while 0.x minor releases
may intentionally evolve the API with release notes. v0.1.0 is an early release.
