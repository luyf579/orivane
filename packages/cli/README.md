# orivane-cli

The local Orivane CLI, version 0.1.0, under the MIT license. This is an early release
awaiting final review; it is not yet published to PyPI.

The `orivane` command provides deterministic offline init, static TOML
validate, stdin run and local structural trace. It uses a synchronous application
factory returning an async runner. No provider schema, persistent sessions, remote
exporter or automatic environment-file loading is included. Python 3.11/3.12 are
tested. This distribution has a command interface, not an intended typed library API;
it does not advertise PEP 561 support.

Once v0.1.0 is published to PyPI, run these commands in PowerShell:

```powershell
pipx install orivane-cli
orivane init demo
cd demo
orivane validate .
"hello" | orivane run .
"hello" | orivane trace .
```

The generated starter uses offline TestModel and needs no API key. Installing the
CLI resolves Core and the backend at exactly 0.1.0. During review, collaborators
use `uv sync --locked --all-packages` or verified local wheels.

[Repository and documentation](https://github.com/luyf579/orivane) remain private
until the separately approved publication step.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
