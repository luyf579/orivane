# Workflow v0

## Purpose

`Workflow[T]` is a typed async orchestration primitive in Core: linear steps and
basic if/else. One caller-owned value type flows through the entire run. It can be
a dataclass, Pydantic model, or another domain object; there is no framework state type.

## Public API

`Workflow` is the only new public type, exported from `orivane_core`.

```python
Workflow[T]()
workflow.then(name: str, step: Callable[[T], Awaitable[T]]) -> Workflow[T]
workflow.branch(
    name: str,
    predicate: Callable[[T], bool],
    *,
    if_true: Callable[[T], Awaitable[T]],
    if_false: Callable[[T], Awaitable[T]],
) -> Workflow[T]
await workflow.run(value: T) -> T
```

The signatures above are schematic. Nodes require explicit non-empty string names;
empty or non-string names raise `ValueError`. Duplicate names also raise `ValueError`,
with steps and branches sharing one namespace. Names are stored exactly as supplied:
no stripping, case folding, or inference from `function.__name__`. Whitespace names
are allowed. Node records remain private; no additional workflow types are exported.

## Immutable composition

`then` and `branch` return new workflows. They never modify their source instance:

```python
base = Workflow[State]()
a = base.then("prepare", prepare)
b = base.branch("quality", needs_revision, if_true=revise, if_false=accept)
```

`base` remains empty; `a` and `b` are independent configurations. Internally, frozen
private nodes are held in a tuple. This is configuration immutability through the
public API, not deep immutability of caller-owned values or captured callable state.

## Step semantics

Steps run in insertion order and must return awaitables of the same value type.
Each completed step's returned object becomes the next node's input. An empty
workflow returns the original input object (`result is input`).

Workflow passes returned objects exactly as produced by steps. User steps may mutate
their input; Workflow does not clone values or promise immutable state. Passing a
sync function that returns a non-awaitable is a typing error and raises Python's
natural `TypeError` at execution. No executor conversion is performed.

## Branch semantics

Each branch evaluates its synchronous predicate exactly once per run. Its result
must be a real `bool`; `1`, `"yes"`, `[]`, and `None` raise `TypeError` before either
branch function runs. Async predicates are unsupported.

Only `if_true` runs for `True`; only `if_false` runs for `False`. Both are ordinary
async steps. The selected function's result feeds the following node. Branches
never execute in parallel, and there is no implicit retry.

## Error semantics

Step, predicate, and selected branch exceptions propagate as the original exception
object. No later node runs. Predicate failure calls neither branch. Workflow does
not wrap exceptions, skip failed nodes, retry steps, or retry a complete run.

Completed side effects are not rolled back. Workflow v0 is orchestration, not a
transaction. Callers must account for existing side effects before retrying a run.

## Cancellation

`asyncio.CancelledError` propagates unchanged from steps and branch functions.
Workflow does not shield work or catch `BaseException`. Cancellation of an awaiting
run reaches its active callable, whose `finally` cleanup runs normally; later nodes
do not execute. Already completed side effects remain.

## Concurrency

One Workflow instance can run concurrently on independent inputs. The current value
is a coroutine local variable; the instance keeps no mutable per-run state and uses
no execution lock. Extending a configuration cannot change suspended runs.

This guarantees only the absence of framework-owned shared per-run state. Callers
remain responsible for concurrency safety of their values, functions, and captured
resources. It does not serialize sessions or provide thread/process coordination.

## Agent integration

Workflow imports neither AgentBackend nor SessionState nor InMemorySessionRuntime.
Its constructor accepts no backend. Capture the owned AgentBackend contract in an
ordinary async closure, as in this complete offline example:

```python
import asyncio

from orivane_core import AgentBackend, RunRequest, Workflow
from orivane_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel


def answer_workflow(backend: AgentBackend[None, str]) -> Workflow[str]:
    async def ask(prompt: str) -> str:
        result = await backend.run(RunRequest(prompt, None))
        return result.output

    return Workflow[str]().then("ask", ask)


async def main() -> None:
    # Only the composition root selects the backend and model.
    backend: AgentBackend[None, str] = PydanticAgentBackend(
        TestModel(custom_output_text="done"), output_type=str
    )
    assert await answer_workflow(backend).run("hello") == "done"


asyncio.run(main())
```

A closure can similarly await `runtime.run(...)` when explicit session ordering is
needed. Runtime creation, session IDs and storage policy belong to the caller.
AgentBackend and InMemorySessionRuntime are unchanged. Another workflow can be
called with `await child.run(value)` inside an ordinary async step; there is no
special nested workflow node.

## Non-goals

No DAG, Graph, State Machine, parallel branches, durable execution, checkpointing,
automatic retry, multi-agent orchestration, backend selection, provider management,
session storage, or rollback. Workflow v0 added no dependency; Phase 1F adds the
OpenTelemetry API for private observability. The current development backend is
pinned to PydanticAI 2.54.0; Workflow contracts remain unchanged.
PydanticAI's internal graph is not this public workflow API.

## Future evolution

Phase 1F uses explicit names as structural attributes in private
[logging/tracing](observability.md), without changing Workflow's public API.
More complex scheduling requires a concrete
requirement and a separate design decision. See [ADR-0003](../adr/0003-workflow-v0.md).
