# orivane-cli

The local Orivane CLI, version 0.2.0, under the MIT license. The source is public.
This is unreleased development source; the latest published release remains v0.1.1.
No production-readiness claim is made.

The `orivane` command provides deterministic offline init, static TOML
validate, stdin run and local structural trace. It uses a synchronous application
factory returning an async runner. No provider schema, persistent sessions, remote
exporter or automatic environment-file loading is included. Python 3.11/3.12/3.13 are
tested. This distribution has a command interface, not an intended typed library API;
it does not advertise PEP 561 support.

Install the CLI and create an offline starter project in PowerShell:

```powershell
pipx install orivane-cli
orivane init demo
cd demo
orivane validate .
"hello" | orivane run .
"hello" | orivane trace .
```

The generated starter uses offline TestModel and needs no API key.
`pip install orivane-cli` installs the published CLI inside a Python environment.
For the 0.2.0 development source, use `uv sync --locked --all-packages` from the
repository; its exact internal requirements are `orivane-core==0.2.0` and
`orivane-backend-pydantic==0.2.0`.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
