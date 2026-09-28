# License review

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

LICENSE GATE: **APPROVED**

Decision: **MIT**, approved by the user for the Orivane RC phase on 2026-09-27.
The canonical root LICENSE uses the standard MIT terms without additional restrictions,
with Copyright (c) 2026 Orivane contributors. Each package build root contains an
exact copy; tests and wheel/sdist verification compare the bytes with the root file.
All three projects declare SPDX `license = "MIT"` and `license-files = ["LICENSE"]`.
Hatchling emits License-Expression: MIT and License-File: LICENSE; wheel licenses
reside under dist-info/licenses. No public author email is added.

Direct production dependency facts from the unchanged locked versions and official
metadata (checked 2026-09-27):

| Package | Role | Version | Declared license / source |
| --- | --- | --- | --- |
| pydantic | Core DIRECT | 2.13.5 | [MIT](https://pypi.org/pypi/pydantic/2.13.5/json) |
| opentelemetry-api | Core DIRECT | 1.44.0 | [Apache-2.0](https://pypi.org/pypi/opentelemetry-api/1.44.0/json) |
| pydantic-ai-slim | Backend DIRECT | 2.48.0 | [MIT](https://pypi.org/pypi/pydantic-ai-slim/2.48.0/json) |
| opentelemetry-sdk | CLI DIRECT; workspace DEV DIRECT | 1.44.0 | [Apache-2.0](https://pypi.org/pypi/opentelemetry-sdk/1.44.0/json) |
| Orivane Core / backend | Internal DIRECT | 0.1.0 | MIT |

No audited direct dependency requires Orivane itself to adopt Apache-2.0 merely
because it is a dependency. The Apache license definition excludes works that remain
separable or merely bind to its interfaces. Dependencies are not vendored into Orivane
source or wheels; they retain their own licenses and redistribution requirements.
The local verification wheelhouse is not an Orivane distribution. This records the
project decision and dependency facts, without changing third-party terms.

Sources: [standard MIT text](https://opensource.org/license/mit),
[Apache-2.0 terms](https://www.apache.org/licenses/LICENSE-2.0.txt),
[Hatchling metadata](https://hatch.pypa.io/latest/config/metadata/#license).
