# Naming gate

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Status: **APPROVED**. On 2026-09-27 the user selected **Orivane**, then explicitly
accepted the discovered GitHub same-name situation and authorized the coordinated
rename. This closes the naming decision; it does not approve public visibility,
licensing, a version bump, tags, Releases, or uploads.

| Surface | Approved identity |
| --- | --- |
| GitHub repository | luyf579/orivane |
| Core distribution / import | orivane-core / orivane_core |
| Backend distribution / import | orivane-backend-pydantic / orivane_pydantic |
| CLI distribution / import | orivane-cli / orivane_cli |
| Executable | orivane |
| Local CLI config | orivane.toml |
| Future commerce distribution | orivane-commerce (name only; no package or reservation) |

Read-only PyPI JSON checks on 2026-09-27 returned HTTP 404 (NOT FOUND) for
[orivane](https://pypi.org/pypi/orivane/json),
[orivane-core](https://pypi.org/pypi/orivane-core/json),
[orivane-backend-pydantic](https://pypi.org/pypi/orivane-backend-pydantic/json),
[orivane-cli](https://pypi.org/pypi/orivane-cli/json) and
[orivane-commerce](https://pypi.org/pypi/orivane-commerce/json).
NOT FOUND does not guarantee registration availability, grant ownership or reserve
a name. Repeat checks before a separately authorized publication; never upload
placeholder packages. Private :: Do Not Upload remains on all three distributions.

## Accepted discoverability overlap

The GitHub root is not globally unique. Read-only search found
[wieslawsoltes/Orivane](https://github.com/wieslawsoltes/Orivane), a collaborative
whiteboard project, and [UrMacroGuy/Orivane](https://github.com/UrMacroGuy/Orivane).
The user accepted this overlap. No trademark or legal clearance is claimed.

## Historical decision and compatibility

The previous provisional `agent-framework` and `agent-framework-core` names conflict
with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) and
its [PyPI packages](https://pypi.org/project/agent-framework-core/). Those names are
not retained as distribution aliases or import shims; no public release preceded
the rename. Current imports, console script and config use Orivane. Historical
issue text and Git history remain unchanged.

Class/function exports, SessionState envelopes and runtime behavior are unchanged.
Existing structural telemetry names/keys (`agent_framework.*`, `af_*`) are retained
to avoid an unrelated observability schema change. They are telemetry labels, not
old Python import packages. Native PydanticAI identity remains pydantic-ai / 2.48.0.
See [rename impact](rename-impact.md), [license review](license-review.md) and
[publication gate](publication-gate.md).
