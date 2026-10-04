# orivane-core

The typed core of Orivane, version 0.1.1, under the MIT license. The source is public.
This is a local hotfix candidate, unpublished on PyPI and GitHub Releases. The
published release remains v0.1.0.

Provides typed AgentBackend, ToolDefinition, RunRequest, RunResult, SessionState,
InMemorySessionRuntime and Workflow contracts. Sessions are in memory; workflows
are linear async steps with basic branching, without durable execution.
Core imports no PydanticAI runtime. Python 3.11/3.12 are tested; py.typed is included.

Install the published v0.1.0 release with `pip install orivane-core`. Install this
0.1.1 candidate from locally built wheels. For local development, use
`uv sync --locked --all-packages` from the repository.
Public APIs follow semantic versioning; 0.x minor releases
may intentionally evolve APIs with release notes. No production-readiness claim is made.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
