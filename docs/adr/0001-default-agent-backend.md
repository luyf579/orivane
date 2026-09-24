# ADR-0001: Default Agent backend

Status: accepted in Phase 0; Phase 1B implements the runtime without changing Core.

## Context

The framework centers on Agent, with Python 3.11+, uv, and a monorepo. Initial scope
is tool use, basic session state, and later linear workflows with conditions.
Business code must not bind directly to one upstream runtime.

## Decision

Use PydanticAI as the first backend, pinned to **pydantic-ai-slim==2.48.0**.
Own one AgentBackend Protocol and four records; keep upstream runtime types inside
the adapter. See [contract](../architecture/backend-contract.md). Harness is not a
required dependency and pydantic-graph is not our public workflow interface.

## Evidence and attempted refutation

Phase 0 inspected PydanticAI at commit
`06be8e7a0056d6c6c72d2868f6b26ee8e7364c77` and ran 10 focused upstream tests plus
five public-API probes. Tool context stayed outside model schema; tools received
owned dependencies; structured output and request limits worked; native message
JSON round-tripped without growing the original history list.

The hypothesis that Tool.from_schema enforces the supplied business schema was
false: the bridge must explicitly validate before side effects. A FunctionModel
probe verified invalid -> retry -> valid -> one side effect. See [tool rules](../architecture/tool-contract.md).
AbstractAgent.run already encapsulates graph iteration, so a thin adapter need not
depend on private graph or schema helpers. Phase 1B migrates all five probe behaviors
into self-contained product tests through PydanticAgentBackend: schema context
exclusion, dependency/history continuity, typed output, request limits, and validated
retry before side effects. Additional tests cover version/decode ordering, malformed
payload redaction, finite tool budgets, and failure without returned replacement state.

Sources: [Agent run](https://github.com/pydantic/pydantic-ai/blob/06be8e7a0056d6c6c72d2868f6b26ee8e7364c77/pydantic_ai_slim/pydantic_ai/agent/abstract.py),
[Tool](https://github.com/pydantic/pydantic-ai/blob/06be8e7a0056d6c6c72d2868f6b26ee8e7364c77/pydantic_ai_slim/pydantic_ai/tools.py),
[messages](https://github.com/pydantic/pydantic-ai/blob/06be8e7a0056d6c6c72d2868f6b26ee8e7364c77/pydantic_ai_slim/pydantic_ai/messages.py).

## Alternatives

OpenAI Agents SDK 0.22.3: 303 offline tests passed in Phase 0. Agent/Runner separation,
local context, and Session are useful patterns, but its Responses-oriented input
and model API increase coupling for this provider-neutral business boundary. It is
not OpenAI-only; retain it as a potential second backend rather than the default.

Microsoft Agent Framework Python 1.19.0: 134 focused core tests passed. Its core is
not inherently bloated; OpenAI integration is separately packaged. Adopt workspace
and dependency-direction lessons, not its full workflow/provider/release machinery.

LangGraph: official [overview](https://docs.langchain.com/oss/python/langgraph/overview)
and [persistence docs](https://docs.langchain.com/oss/python/langgraph/persistence)
describe stateful graph orchestration and persistence. Current linear + if scope
does not justify making graph the core runtime. Phase 0 did not clone or test it;
reconsider when durable DAG requirements exist.

Harness 0.34.0 is optional future capability work, not the default core dependency.
Its independently tested lock used PydanticAI 2.44.0, not our 2.48.0 baseline.

## Risks

Native message/schema semantics and tracing may change despite stable method names.
Tool.from_schema needs explicit validation. Tool side effects are not transactional;
basic snapshots are not crash recovery or exactly-once execution. Real providers,
streaming, cancellation and lifecycle semantics remain future validation work.
Phase 0 ran Python 3.12.7 only; the product validation matrix now covers Python 3.11
and 3.12 with offline models. This does not certify real providers or the deferred
cancellation, resource ownership, and same-session serialization requirements in #6.

## Version pinning strategy

Keep exact slim 2.48.0 and commit uv.lock, including the resolved graph dependency.
2.49.0 existed at research time; selected API signatures showed no obvious breaking
change, but schema/typing changes were not equivalently runtime-tested. Do not upgrade
merely because a release is newer. Review release notes and relevant diffs, then run
contract tests, native-state fixtures, and provider smoke tests before updating pins.
Do not claim all 2.x versions compatible without tests.

## Exit criteria

Revisit the default if required behavior depends on private graph/schema helpers,
business tools cannot be isolated, versioned state cannot reliably restore, needed
provider semantics are unavailable, or compatibility work outweighs thin adaptation.
Use evidence and shared contract tests rather than framework feature counts.

## Future multi-backend migration

Keep business code on owned types. Add a second adapter only for actual demand and
run the same applicable contract tests. Existing native sessions remain on their
original backend; new backends start new sessions. Lossless migration requires an
explicit tested converter. Do not pre-build universal Message/Model/Trace abstractions.
