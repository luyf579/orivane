# ADR-0003: Workflow v0

Package/import/command references reflect the approved Orivane rename. The original
architectural decision is unchanged; historical issues and Git history are preserved.

Status: Accepted

## Context

Issue #7 needs sequential async calls, basic if/else, and explicit failure behavior.
There is no current requirement for graph scheduling or durable execution.

## Decision

Add only `Workflow[T]` to Core. A single caller-owned value type flows through named
async steps and synchronous, strictly boolean predicates. `then` and `branch` return
new configurations; `run` keeps its current value local. Empty workflows are identity
operations. Only the selected branch executes. Errors and cancellation propagate
without retry or rollback of completed side effects.

Linear composition and if/else meet the requirement without a scheduler or extra
public node/state/builder types. Workflow has no AgentBackend or SessionRuntime
dependency: ordinary async closures integrate either, preserving the existing
contracts and allowing non-Agent steps to compose in the same way.

Do not expose pydantic-graph as our public API. Its graph model and dependency would
add concepts unnecessary for this scope and couple caller workflows to the backend.
The implementation uses only the standard library.

Require unique explicit names now so configuration identity does not depend on
Python function names. Store names privately; actual structured logging and tracing
remain in Issue #8 and are not implemented in this phase.

## Consequences

Configurations can be reused and run concurrently without framework-owned per-run
state. Callers still own input mutation, callable concurrency safety and side effects.
DAGs, graphs, state machines, parallel branches, persistence, checkpoints, automatic
retries and multi-agent orchestration remain outside v0. Further abstractions need
an explicit requirement. See [Workflow v0](../architecture/workflow.md) for the API,
failure contract and offline Agent integration example.
