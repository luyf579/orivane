# orivane-backend-pydantic

The PydanticAI backend for Orivane, version 0.1.0, under the MIT license. The source
is public; this is an early release.

PydanticAgentBackend accepts compatible public PydanticAI Model objects. Tested
offline using TestModel/FunctionModel, pinned to pydantic-ai-slim 2.48.0.
Real provider certification is not provided. Native session snapshots may contain
sensitive data and require application protection. Python 3.11/3.12 are tested;
py.typed is included. Core is required at exactly the same package version.

Install with `pip install orivane-backend-pydantic`. The backend installs exactly
matching `orivane-core==0.1.0`. For local development, use
`uv sync --locked --all-packages` from the repository or locally built wheels.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
