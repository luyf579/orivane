# orivane-core

The typed core of Orivane, version 0.2.0, under the MIT license. The source is public.
This is unreleased development source; the latest published release remains v0.1.1.

Provides typed AgentBackend, ToolDefinition, RunRequest, RunResult, SessionState,
InMemorySessionRuntime and Workflow contracts. Sessions are in memory; workflows
are linear async steps with basic branching, without durable execution.
Core imports no PydanticAI runtime. Python 3.11/3.12/3.13 are tested; py.typed is included.

Install with `pip install orivane-core`. For local development, use
`uv sync --locked --all-packages` from the repository.
Public APIs follow semantic versioning; 0.x minor releases
may intentionally evolve APIs with release notes. No production-readiness claim is made.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
