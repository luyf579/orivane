# In-memory session runtime

## Purpose

`InMemorySessionRuntime[DepsT, OutputT]` is a concrete Core runtime above the existing
`AgentBackend[DepsT, OutputT]`. It owns logical-session existence, opaque latest snapshots
and per-session ordering. It does not change ToolDefinition, SessionState, RunRequest,
RunResult or AgentBackend. It adds no store/executor/lock protocol.

## API

```python
runtime = InMemorySessionRuntime(backend, max_sessions=100)
runtime.create_session("example")
result = await runtime.run("example", "hello", deps)
runtime.delete_session("example")  # only after all runs/waiters are finished
```

Import InMemorySessionRuntime from `agent_framework_core`. `backend` is borrowed;
the runtime neither creates providers nor closes the backend or its resources.
It returns the backend's RunResult after committing its next_state. There is no public
state/lock registry, entry count, state decoder, or lifecycle shutdown method.

## Session identity

The caller supplies an explicit non-empty str. The runtime does not allocate UUIDs,
normalize IDs or infer them from payloads, prompts, context, model, backend or object
identity. Whitespace/canonicalization, tenant namespaces, authorization and URL encoding
belong to the application boundary. A session ID is not an authorization token.

## Creation

Only synchronous `create_session(id)` creates a session, initially with committed
state None. Duplicate creation fails without changing the existing snapshot. `run`
and `delete_session` fail for missing IDs; they never silently recreate deleted,
misspelled or lost-after-restart history. Management must execute on the same thread
as the single event loop using this runtime.

## Run semantics

The runtime retains an entry synchronously, awaits its lock, loads the latest committed
snapshot, calls `backend.run(RunRequest(prompt, context, state))`, assigns result.next_state,
then returns the result and releases the lock/reference. Context is forwarded unchanged.
SessionState remains opaque; Core does not decode payloads or read native conversation IDs.
The in-memory commit is a synchronous dict assignment with no await after backend success
and before commit. The caller cannot observe a successful result before that assignment.

## Serialization

Retain -> acquire per-session lock -> load -> await backend -> commit -> unlock -> release
entry. A waiting run reads its predecessor's committed state after acquiring the lock,
not the state present when its coroutine was created. Different IDs use different locks
and may enter the backend concurrently. All participating callers must share the same
runtime instance and use its run method; calling the raw backend bypasses coordination.

The raw-backend fork characterization remains valid: the adapter itself does not know
logical session identity. Runtime integration tests demonstrate ordered native history
on top of that unchanged behavior.

## Cancellation

Cancellation propagates as CancelledError. An outer try/finally releases the entry
reference even if lock acquisition is cancelled; async-with releases an acquired lock.
A cancelled waiter does not release the holder's lock or remove a still-retained entry.
A cancelled holder commits nothing and permits an existing waiter to continue from the
previous committed state. Failed/cancelled runs are never automatically retried.

An in-memory assignment has no suspension point. Cancellation observed after a commit
does not roll it back, and loss of the caller's response does not prove no commit happened.
There is no shield, catch-and-convert BaseException, or detached save task. External tool
effects already completed by the backend cannot be rolled back.

## Deletion

`delete_session(id)` immediately rejects a busy session with any holder or waiter.
It does not wait, queue deletion or cancel work. Deleting an idle session removes its
existence/state and frees capacity. Later run(id, ...) fails until explicit creation
again, which starts empty. Merely creating a coroutine does not start/retain an operation;
once run begins executing, validation and retain happen before its first await.

## Capacity

`max_sessions` is required, with no default. It must be a positive int; zero, negatives,
bool and other types are rejected. Capacity counts logical sessions, including idle ones
with None state. At capacity, only new creation fails; existing sessions remain runnable.
No LRU, implicit expiry, reset or automatic eviction is performed. Explicit deletion is
the only way to free an occupied slot; no state survives process restart.

## Lock entry cleanup

Private entries contain one asyncio.Lock and a users counter. Lookup/create/increment
has no await; holders and queued waiters each keep a strong reference. Finally decrements
users after unlock or failed acquisition. Removal requires both users == 0 and the registry
still mapping the ID to that exact entry. This prevents an old release removing a newer
entry. The registry returns to empty when all operations are idle; state retention is
independent. Busy deletion uses registry presence, whose externally observable invariant
is that every registered entry has at least one retained operation.

## Failure semantics

| Condition | Exception / outcome |
|---|---|
| Empty or non-str ID | ValueError |
| Duplicate ID | ValueError; no reset |
| Missing ID for run/delete | KeyError; no implicit creation |
| Invalid max_sessions | ValueError |
| Creation at capacity | RuntimeError; existing sessions preserved |
| Deleting busy session | RuntimeError; holder/waiters preserved |
| Backend failure | Original exception propagates; prior committed state preserved |
| Cancellation before successful backend return | CancelledError; no replacement committed |

Runtime-generated errors use fixed messages, without payload, prompt or context data.
Backend exceptions propagate unchanged and are not globally sanitized by this layer.
No transaction spans tools and state; there is no exactly-once claim. Durable-save
failure/cancellation is outside this in-memory implementation and needs a separate design.

## Process limitations

One runtime instance, one Python process, one event loop, same-thread create/delete/run
management. No thread safety, cross-loop coordination, multiple-worker exclusion or
cross-machine guarantees. Multiple runtime instances have independent state and locks.
CLI process restarts lose sessions; multi-worker Web deployments need later persistence
and coordination work before they can claim shared-session safety.

## Non-goals

This is not a persistent store, multi-process coordinator, transaction manager, provider
resource owner, workflow engine or StorageAdapter. No custom SessionId/Revision classes,
distributed transactions, CAS, leases, backend-wide lock, or automatic whole-run retry.
See [ADR-0002](../adr/0002-session-serialization.md) for accepted scope and deferred work.
