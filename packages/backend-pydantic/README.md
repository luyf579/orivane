# orivane-backend-pydantic

The PydanticAI backend for Orivane, version 0.1.1, under the MIT license. The source
is public.

This evaluation branch prepares the PydanticAI 2.54.0 foundation for a future
v0.2.0 release. Distribution versions remain 0.1.1 for local evaluation only;
these candidate wheels must not be published. Released v0.1.1 still uses 2.48.0.

PydanticAgentBackend accepts compatible public PydanticAI Model objects. Tested
offline using TestModel/FunctionModel, with this candidate pinned to
`pydantic-ai-slim==2.54.0`.
Real provider certification is not provided. Native session snapshots may contain
sensitive data and require application protection. Python 3.11/3.12 are tested;
py.typed is included. Core is required at exactly the same package version.

`pip install orivane-backend-pydantic` installs the published package. For this
local candidate, use `uv sync --locked --all-packages` from the repository; it
requires `orivane-core==0.1.1` and `pydantic-ai-slim==2.54.0`.

## Native session version policy

The candidate accepts only `backend_id="pydantic-ai"`, `format_version=1` and
`backend_version="2.54.0"`. Other versions are rejected before history decoding
or model/tool execution. Successful runs produce complete replacement history
labeled 2.54.0. The public `BACKEND_VERSION` export changes from 2.48.0 to 2.54.0;
export names and signatures remain unchanged.

When a future Orivane release switches to PydanticAI 2.54.0,
SessionState snapshots labeled backend_version 2.48.0 are rejected.

Applications persisting SessionState must start a new session
or perform an explicitly application-owned migration.

Orivane provides no automatic migration in this phase. There is no compatibility
window or migration utility; caller-owned snapshots are not reset or relabeled.

[Repository and documentation](https://github.com/luyf579/orivane) are public.

## License

MIT. The included LICENSE is an exact copy of the repository root license.
