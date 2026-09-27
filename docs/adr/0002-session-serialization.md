# ADR-0002: Same-session serialization

Package/import/command references reflect the approved Orivane rename. The original
architectural decision is unchanged; historical issues and Git history are preserved.

Status: Accepted

Implementation: `InMemorySessionRuntime` (Phase 1D-B).

## Implementation

Phase 1D-B implements the accepted in-process decision as one public concrete Core
type: `InMemorySessionRuntime[DepsT, OutputT]`, above the unchanged AgentBackend.
It uses explicit creation, an opaque non-empty string ID, a required positive
`max_sessions`, idle-only deletion, and reference-counted per-session entries.
Load/run/synchronous commit occur under the same lock. Holders and waiters retain
their entry before the first await; finally releases the reference on every exit.
Idle lock cleanup preserves committed state; only explicit deletion frees capacity.

The guarantee requires one shared runtime, one process/event loop, and same-thread
management. There is no persistence, thread/process coordination, transaction manager,
automatic retry, or exactly-once guarantee. No second runtime/store protocol is added.
See [the implemented API and error semantics](../architecture/session-runtime.md).
The option comparison and future-storage analysis below retain the Phase 1D-A design
rationale; deferred durable/multi-process capabilities are not implemented by acceptance.

## Context

Phase 1C fixed the cancellation and borrowed-resource contract without changing
AgentBackend. Issue #6 still requires same-session serialization. A SessionState is
an opaque replacement snapshot, not a logical session handle. RunRequest carries
prompt, context and optional state; it carries no durable identity or storage policy.
We need a design usable from both a local CLI and a Web service, while preserving
the five existing Core types. Phase 1D-A implemented no runtime; Phase 1D-B adds only
the concrete type identified above and leaves those five types unchanged.

## Empirical current behavior

OBSERVED on Python 3.11.16/3.12.7 and PydanticAI 2.48.0: after a successful seed run,
two runs given the same S0 both enter an offline FunctionModel before either is
released. With either completion order, SA contains seed+A only, SB seed+B only;
both decode successfully and S0 stays unchanged. They share a native conversation
identifier, but the backend does not use that field as a serialization key.
Independent sessions on the same backend also enter concurrently. These are
characterizations of today's missing coordination, not desired session behavior.
See [the experiment report](../research/phase1d-session-concurrency.md) for ordering,
scope and reproducible test names. No production implementation was changed.

## Requirements

- Explicit logical identity survives successive snapshots and serialization.
- One session's load/run/save is serialized; unrelated sessions can overlap.
- AgentBackend stays unaware of session_id, database, locks, retention and stores.
- Cancellation releases local coordination and never triggers whole-run retry.
- A result becomes caller-visible only after replacement state has been committed.
- Lock entries do not accumulate forever; state retention is a separate concern.
- CLI and Web share the same semantics. Future persistence remains possible.
- v0 guarantees only one Python process/event loop with one shared runtime owner.
- Do not claim exactly-once tools, transactions across external effects, or worker safety.

## Rejected identity heuristics

| Candidate | Why it cannot be the logical key |
|---|---|
| id(SessionState) | Deserialization creates another object; a process restart loses the identity; each successful replacement may create a new object in the same session. |
| hash(payload), including a stable digest | Each successful run changes content; copied identical histories can belong to independently forked sessions. A digest identifies bytes, not intent. Native backend/version encodings are unsuitable as a cross-backend identity contract. Python's hash adds process-specific behavior and collision concerns; replacing it with SHA-256 does not fix the semantic problem. |
| prompt | Identical prompts occur in unrelated sessions; prompts change each turn and can be sensitive. |
| context or its object identity | Dependencies may be shared, reconstructed or mutable; authentication context is not conversation identity. |
| model | One shared borrowed model may serve many sessions and may change during application composition. |
| backend instance | One adapter intentionally serves independent sessions; locking it serializes unrelated work. |
| native conversation_id | It belongs to opaque provider/backend history, may be absent or copied during a fork, and would require decoding the backend format in the session layer. Our fork probe retains the same value in both branches. |

PROPOSED identity: an explicit non-empty opaque **str**, normally a UUID-like string
allocated once by the application/runtime boundary. No custom SessionId class is
needed. Persist/reuse that string independently of SessionState. Both CLI and Web
can carry it unchanged as a future store key. Canonical form and authorized tenant
namespace are boundary responsibilities; an ID is not an authorization credential.
Backend/version envelope validation remains independent of ID validity.

## Options

A: add session_id to RunRequest. B: a higher-level SessionRunner/SessionExecutor
around AgentBackend. C: each CLI/Web/application implements coordination itself.
D: introduce a SessionStore/runtime abstraction owning identity, state and serialization.

| Dimension | A: RunRequest ID | B: higher-level executor | C: every caller | D: store/runtime |
|---|---|---|---|---|
| Public API impact | Changes frozen Core request; still needs state/lock owner. | One future concrete entry point above frozen Core. | No framework API; divergent caller contracts. | New session/persistence-facing API, potentially several protocols. |
| Backend coupling | Encourages lock/store awareness; an ID field alone solves nothing. | Backend receives only current snapshot. | Backend stays pure if callers are disciplined. | Backend can stay pure, but store/execution boundary must be clear. |
| CLI suitability | CLI must still coordinate load/save around calls. | Natural run(session_id, prompt, context) entry. | Easy initial script, repeated policy in every entry point. | Natural once a session store exists; premature for a small local CLI. |
| FastAPI/Web suitability | Request ID useful, but route middleware still insufficient alone. | One app-scoped runtime per loop, shared by routes. | Easy to accidentally create locks per request or per router. | Natural persistence integration; still no automatic cross-worker safety. |
| Local-first suitability | Requires infrastructure beyond request field. | Can start with in-memory state in one process. | Low initial cost; semantics drift across commands. | Strong fit for durable local storage, higher initial cost. |
| Testing complexity | Core migration plus coordination integration. | One layer tested with a fake backend and scheduling barriers. | Repeat the same concurrency/failure matrix in every caller. | State, execution and persistence failure contracts tested together. |
| Cancellation semantics | ID alone supplies none. | One policy for wait/run/commit phases. | Each application must implement and maintain policy. | Must distinguish cancelled execution from uncertain durable commit. |
| Lock cleanup | Must still choose an owner; backend is wrong default. | Executor owns bounded-lifetime entries. | Often scattered module globals, difficult auditing. | Store/runtime owns entries; persistent and local coordination must differ. |
| Multiple backends | Pollutes all requests with coordination metadata. | Uses existing AgentBackend protocol; validates selected session backend. | Possible, with repeated integration code. | Possible if session payload stays opaque. |
| Future StorageAdapter | No help for storage boundaries. | Can move state operations behind a seam when needed. | N independent migrations. | Early generic storage design may constrain session semantics. |
| Multi-process limitation | Field alone provides no exclusion. | In-memory locks coordinate one loop only. | Per-worker locks remain independent. | Only safe if store's actual protocol supplies distributed coordination. |
| Migration cost | Changes all consumers/implementations of Core request. | Callers adopt one outer entry point; backend unchanged. | Cheapest now, most duplication to unwind later. | Higher up-front abstraction and retention/versioning commitments. |

## Decision

ACCEPTED: prefer **B**, one small concrete session execution runtime above
AgentBackend, initially owning identity lookup, in-memory latest state and per-session
coordination together. Do not introduce separate public Executor, Store and LockRegistry
protocols at once. B takes the minimal identity/state responsibilities needed for correct
execution; it does not become a generic persistence framework. D becomes justified when
a real durable store/second persistence implementation creates concrete pressure.

B versus D is therefore a responsibility boundary, not an argument for two immediate
abstractions. A store that owns only bytes cannot serialize a long backend run by itself;
an executor that accepts an already loaded snapshot cannot prevent stale reads. One
owner must cover the entire critical section. C is acceptable as a short-lived single
caller prototype but is not the shared framework recommendation. A changes Core without
solving commit ordering, so reject it now. No option requires changing the existing
AgentBackend contract to satisfy the in-process requirement.

## Why this is not part of AgentBackend

AgentBackend runs the supplied request; it has no reliable logical ID, latest-state
lookup or storage authority. Both probes demonstrate why a backend-wide asyncio.Lock
is inappropriate. Keep `AgentBackend.run(RunRequest(prompt, context, state))` unchanged.
The future runtime is shared at the application composition root, not newly created per
HTTP request. Applications supply identity and authorization; the runtime owns the
in-process per-session lock and latest-state access policy, not the backend or a generic KV store.

CLI sketch: `agent run --session <id>` resolves the explicit ID then calls the same
runtime entry point as `POST /sessions/{id}/runs`. The Web boundary authenticates and
authorizes access before dispatch. Different IDs can run concurrently. Two independent
CLI processes and two Web workers are deliberately outside v0's guarantee.

An in-memory v0 serves a long-lived/interactive CLI process or one Web process; it
does not preserve state across successive one-shot CLI invocations or process restarts.
An opaque stable ID is necessary but does not itself provide persistence. Durable
one-shot CLI continuation will require a concrete local persistence design later,
through the same outer entry point, rather than adding storage to AgentBackend.

## In-process semantics

One runtime instance and one event loop are prerequisites. Define the critical section
as load latest state, run, save full replacement, then return; never accept an unverified
caller-supplied snapshot as the latest state for an existing session. A session remains
bound to a compatible backend/history version; switching backend does not migrate history.

For a future entry map, prefer a **reference-counted entry**: synchronously look up/create
the entry and increment its user count before the first await. Count both holders and
waiters. Each caller retains a strong reference. After releasing or abandoning acquisition,
decrement in finally; remove only when count is zero and the map still refers to that entry.
Acquisition failure/cancellation must decrement too. No awaits between map lookup and retain,
or between decrement and removal, in the single-loop design. No public lock manager is needed.

| Cleanup alternative | Assessment |
|---|---|
| WeakValueDictionary | CPython 3.11/3.12 probes show Lock is weak-referenceable, and a waiting/holding coroutine's explicit local reference preserves it. After last strong reference it disappears. A locked flag alone does not preserve it. Viable only if every access retains a strong reference through waiting and holding, and lookup/create/retain cannot interleave. Hidden GC lifetime makes this less explicit than counts. |
| Reference-counted entry | Recommended for auditable ownership and deterministic removal after all users, including cancelled waiters, have left. More bookkeeping; test cancellation at every boundary. |
| Delete after last waiter | A naive deletion on unlock ignores queued/resuming waiters or the holder. A new entry can coexist with the old one. Safe only with explicit holder+waiter accounting, which reduces to the previous option. Do not inspect asyncio private waiter lists. |
| Bounded cache | Evicting a busy entry creates two locks for one ID. Only idle zero-user entries can be evicted; reject/backpressure new work if all are active. A size limit cannot replace ownership tracking. |

Lock-map cleanup does not delete session state. State retention needs an independent
policy: for initial in-memory v0, explicit session deletion/creation and a documented
capacity bound should reject excess creation rather than silently reset existing history.
Deleting a session while it is running must be coordinated, not implemented as raw dict pop.
An unbounded count of simultaneously active sessions also needs application admission
control; entry cleanup only prevents idle-lock accumulation.

## Cancellation semantics

The [Python lock contract](https://docs.python.org/3.11/library/asyncio-sync.html#lock)
supports async-with cleanup, while [task cancellation](https://docs.python.org/3.11/library/asyncio-task.html#task-cancellation)
requires propagation after necessary finally cleanup. Proposed boundaries:

| Cancellation point | Required behavior |
|---|---|
| Waiting to acquire | No run and no commit. Release the entry reference/count; never release another task's lock. |
| Holding lock before/during load | async-with releases lock; outer finally drops entry count. Report cancellation, no fabricated result. |
| backend.run | Propagate CancelledError, no automatic rerun. Preserve prior committed snapshot. Completed tool effects are not undone. |
| In-memory replacement assignment | No await in commit step: one loop cannot inject cooperative cancellation halfway through the assignment. A cancellation observed after commit does not undo it. |
| Future awaited save | The remote write may fail, finish, or have an unknown outcome. Do not return success or blindly retry. Finish/resolve any still-running save before admitting another same-session write; otherwise quarantine that session and require reconciliation. Release the local lock in finally after this handoff, rather than leave it permanently held. |

Do not detach or blanket-shield save and release the lock while it can still write.
If save cannot acknowledge cancellation, a bounded cleanup/quarantine policy is required
before persistent v0 can be advertised; an in-process lock cannot cancel a remote commit.
Cancellation is a BaseException in these Python versions; use async-with/finally, not
catch-and-convert BaseException. Waiting requests must also consult unresolved-commit status
if a future persistent runtime uses quarantine. This is a future design gate, not code here.

## State commit ordering

Required sequence: **lock -> load -> backend.run -> save replacement -> unlock**.
The successful save is the session-state linearization point, not model completion.

Load outside lock: A and B both load S0; even if their runs are later serialized, B
still starts from stale S0 and forks. Unlock before save: A finishes from S0, unlocks;
B reads S0; B saves SB, then delayed A saves SA and loses B's turn. Locking just the
model call or just save does not repair either timeline. The backend correctly returns
full snapshots; the outer owner must order replacement and must never append one twice.

## Failure semantics

If backend execution fails/cancels, do not replace the committed state. If execution
succeeds and tools have effects but save fails, the caller receives failure rather than
a successful session result. A remote save failure can be ambiguous; retain enough
application-level correlation to reconcile without replaying side effects. Never promise
an atomic transaction between tool effects and state storage, rollback, or exactly-once.
Do not invent distributed transactions in v0. Keep errors free of raw history or credentials.

## Multi-process limitations

asyncio.Lock coordinates tasks in one event loop; it is not a thread/process/machine
coordination mechanism. Two runtime instances in the same process with separate maps
also do not coordinate. v0 requires one shared owner per session namespace and excludes
two CLI processes, multiple FastAPI workers and multiple machines.

NOW: in-process per-session ordering only; no Revision class, expected_version field,
CAS API or distributed lock implementation. LATER: before shared Postgres/Supabase or
multiple writers, evaluate store-level transactions, advisory locks, leases with fencing,
or compare-and-swap revisions. CAS detects conflicting saves but cannot undo duplicate
tool effects already executed by competing runs. A lease alone is insufficient after
expiry unless stale holders are fenced. Long DB transactions across model requests also
have costs. These are future decision points, not current guarantees.

## Future storage evolution

Choose **D: do not decide the generic StorageAdapter relationship yet**. The roadmap
name is not an implemented interface. Sessions need identity, opaque snapshot replacement,
commit outcomes and eventually concurrency control; generic get/set hides these semantics.
Do not make SessionStore an implementation of an undefined StorageAdapter (A). It might
later build on a concrete storage adapter (B), or remain a session-specific API (C), if
real consumers demonstrate which boundary preserves transactional/conditional semantics.
Keeping state access inside the proposed runtime permits later persistence without exposing
it through AgentBackend. Do not add a public storage protocol for an imagined second store.

## Public API pressure

No change to ToolDefinition, SessionState, RunRequest, RunResult or AgentBackend is required.
Phase 1D-B approval adds only the concrete InMemorySessionRuntime export and its private
implementation module. No custom ID class, store protocol or public locking API is added.
The five original types remain unchanged. There is no evidence requiring
PUBLIC_API_CHANGE_REQUIRED for the current backend contract. The implemented capacity
and idle deletion rules address in-memory retention; durable save outcomes remain a
future review gate.

## Implementation sketch

Non-executable pseudocode for **one object**, not three new protocols:

Assume the application has authorized the ID and explicitly selected an existing
session or creation of a new one. Missing/deleted existing sessions must fail, not
silently start over; `.get` below only uses None for an explicitly new empty session.

```text
run(session_id: str, prompt, context):
    entry = retain_entry_for(session_id)  # synchronous; includes waiting callers
    try:
        async with entry.lock:
            state = latest_states.get(session_id)  # load AFTER acquire
            result = await backend.run(RunRequest(prompt, context, state))
            latest_states[session_id] = result.next_state  # commit BEFORE unlock
            return result
    finally:
        drop_entry_reference(session_id, entry)  # after unlock/cancelled acquire
```

Map operations stand for internal implementation details of the proposed single runtime,
not public helpers implemented in this PR. Persistent load/save would replace the in-memory
steps inside the same critical section, only after their failure/cancellation contracts
are reviewed. No application should bypass this owner when accessing managed sessions.

## Exit criteria

Phase 1D-A completed: empirical same-state and independent-session probes, both completion orders,
weak-reference lifetime probe, Proposed ADR, Python 3.11/3.12 checks and review bundle;
Issue #6 stayed OPEN. Maintainer accepted this decision for Phase 1D-B implementation.

Phase 1D-B acceptance requires: same-ID requests load the previous committed result;
different IDs overlap; cancellation while waiting/holding/running releases ownership;
failure never produces a false successful commit; entry cleanup cannot create two active
locks per ID and does not grow with idle IDs; session deletion/capacity rules are explicit;
Core/backend contracts remain unchanged. Persistence or multi-process claims need separate
evidence. Today's fork characterization should remain explicitly about raw AgentBackend;
runtime correctness uses separate tests. The Phase 1D-B PR remains open for code review;
Issue #6 closes only when that PR is merged.
