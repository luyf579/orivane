# orivane-cli

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

Private development CLI, version 0.1.0rc1; not production ready and not published
by this project on PyPI. Distribution, imports and command names are approved as Orivane.
Publication approval is still required.

The `orivane` command provides deterministic offline init, static TOML
validate, stdin run and local structural trace. It uses a synchronous application
factory returning an async runner. No provider schema, persistent sessions, remote
exporter or automatic environment-file loading is included. Python 3.11/3.12 are
tested. This distribution has a command interface, not an intended typed library API;
it does not advertise PEP 561 support.

Develop from the authorized private repository with `uv sync --locked --all-packages`.
Local wheels are for packaging verification only. License metadata declares MIT.
Public author identities are not yet approved.

[Repository and documentation](https://github.com/luyf579/orivane)
require private repository access.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
