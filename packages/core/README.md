# orivane-core

The typed core of Orivane, version 0.1.0, under the MIT license. The source is public;
this early release is not yet published to PyPI. PyPI publication is deferred.

Provides typed AgentBackend, ToolDefinition, RunRequest, RunResult, SessionState,
InMemorySessionRuntime and Workflow contracts. Sessions are in memory; workflows
are linear async steps with basic branching, without durable execution.
Core imports no PydanticAI runtime. Python 3.11/3.12 are tested; py.typed is included.

Once v0.1.0 is published to PyPI, install with `pip install orivane-core`.
Until PyPI publication, use `uv sync --locked --all-packages` from the repository
or locally built wheels. Public APIs follow semantic versioning; 0.x minor releases
may intentionally evolve APIs with release notes. No production-readiness claim is made.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
