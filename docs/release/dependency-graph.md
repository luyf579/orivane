# Direct dependency graph

The current synchronized source/package version is 0.2.0, unreleased development
source. Its internal exact requirements use 0.2.0. The latest published release
remains v0.1.1; the approved backend baseline now uses PydanticAI 2.54.0.

Derived from the four current distribution pyproject.toml files and uv.lock. Internal package
requirements in wheel METADATA must match these declarations after normalization.

| Distribution | Direct production requirements |
| --- | --- |
| orivane-core | pydantic>=2.12,<3; opentelemetry-api>=1.44,<2 |
| orivane-backend-pydantic | orivane-core==0.2.0; pydantic-ai-slim==2.54.0 |
| orivane-cli | orivane-core==0.2.0; orivane-backend-pydantic==0.2.0; opentelemetry-sdk>=1.44,<2 |
| orivane-commerce | pydantic>=2.12,<3 |

Core has no backend/PydanticAI dependency. Backend points to Core; CLI points to both.
Commerce depends on Pydantic only, with no Core, backend or CLI dependency.
Workspace source overrides are local development instructions, not wheel requirements.
The wheel installation check resolves CLI's dependencies from local wheel metadata.

Current development lock: Pydantic 2.13.5; PydanticAI and pydantic-graph 2.54.0;
OpenTelemetry API/SDK 1.44.0. Semantic conventions 0.65b0 remains SDK-required
TRANSITIVE, not directly declared or imported by project code. SDK is also DEV DIRECT
for tests. Public installs may resolve newer Pydantic/OpenTelemetry versions within
the declared ranges; the development lock does not pin downstream environments.
The required transitive genai-prices lock update is 0.1.8 to 0.1.9.
No exporter or unrelated runtime dependency is added for packaging.
