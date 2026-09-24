# Workflow scope

v0 workflows will use linear async steps and basic if/else in Core. Phase 1A adds
no workflow engine or workflow public API.

PydanticAI internal graph != our public Workflow API.

Evaluate DAG, Graph, State Machine, Durable workflow, and Multi-Agent orchestration
only after a concrete requirement. Do not expose upstream private graph nodes or
implement a scheduler just to invoke sequential Agents.
