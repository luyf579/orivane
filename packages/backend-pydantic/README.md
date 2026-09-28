# orivane-backend-pydantic

The PydanticAI backend for Orivane, version 0.1.0, under the MIT license. This is
an early release awaiting final review; it is not yet published to PyPI.

PydanticAgentBackend accepts compatible public PydanticAI Model objects. Tested
offline using TestModel/FunctionModel, pinned to pydantic-ai-slim 2.48.0.
Real provider certification is not provided. Native session snapshots may contain
sensitive data and require application protection. Python 3.11/3.12 are tested;
py.typed is included. Core is required at exactly the same package version.

Once v0.1.0 is published to PyPI, install with `pip install orivane-backend-pydantic`.
During review, authorized collaborators use `uv sync --locked --all-packages` or
verified local wheels. The backend installs exactly matching `orivane-core==0.1.0`.

[Repository and documentation](https://github.com/luyf579/orivane) remain private
until the separately approved publication step.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
