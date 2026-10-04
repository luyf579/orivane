# orivane-cli

The local Orivane CLI, version 0.1.1, under the MIT license. The source is public.
This is a local hotfix candidate, unpublished on PyPI and GitHub Releases. The
published release remains v0.1.0. No production-readiness claim is made.

The `orivane` command provides deterministic offline init, static TOML
validate, stdin run and local structural trace. It uses a synchronous application
factory returning an async runner. No provider schema, persistent sessions, remote
exporter or automatic environment-file loading is included. Python 3.11/3.12 are
tested. This distribution has a command interface, not an intended typed library API;
it does not advertise PEP 561 support.

Install the published v0.1.0 CLI and create an offline starter project in PowerShell:

```powershell
pipx install orivane-cli
orivane init demo
cd demo
orivane validate .
"hello" | orivane run .
"hello" | orivane trace .
```

The generated starter uses offline TestModel and needs no API key. The 0.1.1
candidate CLI resolves Core and the backend at exactly 0.1.1; install this candidate
from locally built wheels. `pip install orivane-cli` installs the published release
inside a Python environment. For local development, use
`uv sync --locked --all-packages` from the repository.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
