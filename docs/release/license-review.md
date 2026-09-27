# License review

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Status: **LICENSE_DECISION_REQUIRED**. No project LICENSE currently exists.
MIT and Apache-2.0 remain alternatives for the Maintainer/user to decide. No license
has been selected, no license classifier added, and no public identity invented.
Wheel License / License-Expression fields are intentionally absent until approval.

Direct production dependency facts from locked versions and official PyPI metadata,
checked 2026-09-27 (full license bodies are not reproduced):

| Package | Role | Locked version | Declared license / source |
| --- | --- | --- | --- |
| pydantic | Core direct | 2.13.5 | [MIT](https://pypi.org/pypi/pydantic/2.13.5/json) |
| opentelemetry-api | Core direct | 1.44.0 | [Apache-2.0](https://pypi.org/pypi/opentelemetry-api/1.44.0/json) |
| pydantic-ai-slim | Backend direct (PydanticAI) | 2.48.0 | [MIT](https://pypi.org/pypi/pydantic-ai-slim/2.48.0/json) |
| opentelemetry-sdk | CLI direct; workspace dev direct | 1.44.0 | [Apache-2.0](https://pypi.org/pypi/opentelemetry-sdk/1.44.0/json) |
| Core / backend workspace packages | Internal direct dependencies | 0.1.0.dev0 | Undecided; same project license gate |

These declarations are compatibility inputs, not an automatic license selection or
legal clearance. MIT and Apache dependencies retain their own terms; selecting a
project license does not relicense dependencies. Before distribution, approve the
project LICENSE, verify required notices and redistribution obligations (including
the full resolved dependency closure), then populate consistent metadata and rebuild.
Unknown future license facts must be recorded UNKNOWN, never inferred.
