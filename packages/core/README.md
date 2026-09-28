# orivane-core

The typed core of Orivane, version 0.1.0, under the MIT license. This is an early
release awaiting final review; it is not yet published to PyPI.

Provides typed AgentBackend, ToolDefinition, RunRequest, RunResult, SessionState,
InMemorySessionRuntime and Workflow contracts. Sessions are in memory; workflows
are linear async steps with basic branching, without durable execution.
Core imports no PydanticAI runtime. Python 3.11/3.12 are tested; py.typed is included.

Once v0.1.0 is published to PyPI, install with `pip install orivane-core`.
During review, authorized collaborators use `uv sync --locked --all-packages` or
verified local wheels. Public APIs follow semantic versioning; 0.x minor releases
may intentionally evolve APIs with release notes. No production-readiness claim is made.

[Repository and documentation](https://github.com/luyf579/orivane) remain private
until the separately approved publication step.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
