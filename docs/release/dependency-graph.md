# Direct dependency graph

The current synchronized source/package version is 0.1.1. Its internal exact
requirements use 0.1.1; external dependency declarations are unchanged.

Derived from the four current distribution pyproject.toml files and uv.lock. Internal package
requirements in wheel METADATA must match these declarations after normalization.

| Distribution | Direct production requirements |
| --- | --- |
| orivane-core | pydantic>=2.12,<3; opentelemetry-api>=1.44,<2 |
| orivane-backend-pydantic | orivane-core==0.1.1; pydantic-ai-slim==2.48.0 |
| orivane-cli | orivane-core==0.1.1; orivane-backend-pydantic==0.1.1; opentelemetry-sdk>=1.44,<2 |
| orivane-commerce | pydantic>=2.12,<3 |

Core has no backend/PydanticAI dependency. Backend points to Core; CLI points to both.
Commerce depends on Pydantic only, with no Core, backend or CLI dependency.
Workspace source overrides are local development instructions, not wheel requirements.
The wheel installation check resolves CLI's dependencies from local wheel metadata.

Current development lock: Pydantic 2.13.5; PydanticAI and pydantic-graph 2.48.0;
OpenTelemetry API/SDK 1.44.0. Semantic conventions 0.65b0 remains SDK-required
TRANSITIVE, not directly declared or imported by project code. SDK is also DEV DIRECT
for tests. Public installs may resolve newer Pydantic/OpenTelemetry versions within
the declared ranges; the development lock does not pin downstream environments.
No exporter or unrelated runtime dependency is added for packaging.
