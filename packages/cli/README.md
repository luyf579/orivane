# orivane-cli

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Private development CLI, version 0.1.0.dev0; not production ready and not published
by this project on PyPI. Distribution, imports and command names are approved as Orivane.
License and publication decisions are still required.

The `orivane` command provides deterministic offline init, static TOML
validate, stdin run and local structural trace. It uses a synchronous application
factory returning an async runner. No provider schema, persistent sessions, remote
exporter or automatic environment-file loading is included. Python 3.11/3.12 are
tested. This distribution has a command interface, not an intended typed library API;
it does not advertise PEP 561 support.

Develop from the authorized private repository with `uv sync --locked --all-packages`.
Local wheels are for packaging verification only. License metadata is intentionally
absent until MIT or Apache-2.0 is approved. Public identities are not yet approved.

[Repository and documentation](https://github.com/luyf579/orivane)
require private repository access.
