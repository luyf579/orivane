# Workflow scope

Phase 1E implements [Workflow v0](workflow.md): typed linear async steps and basic
if/else in Core. `Workflow` is the only public workflow type. Composition returns
new configurations; errors and cancellation propagate without implicit retry.

PydanticAI internal graph != our public Workflow API.

Evaluate DAG, Graph, State Machine, Durable workflow, and Multi-Agent orchestration
only after a concrete requirement. Do not expose upstream private graph nodes or
implement a scheduler just to invoke sequential Agents.
