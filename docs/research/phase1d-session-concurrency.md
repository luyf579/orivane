# Phase 1D-A: session concurrency characterization

This report separates **OBSERVED** measurements, **INFERRED** consequences and
**PROPOSED** future behavior. NO SESSION RUNTIME IMPLEMENTED. A fork is evidence of
missing outer serialization, not an endorsed product contract.

## Environment and provenance

- Local Windows, Python **3.11.16** and **3.12.7**.
- `pydantic-ai-slim==2.48.0`, `pydantic-graph==2.48.0`; existing locked environments.
- Production baseline: `5b00fdb32990708c9bfbde287f47c26b061de838`, the squash merge of PR #13.
- Exploratory probe ran before the characterization assertions were written, using
  the real PydanticAgentBackend and offline FunctionModel, with model requests disabled
  by override_allow_model_requests(False). It recorded results instead of assuming a fork.
- Review evidence includes initial-probe-3.11.16.json, initial-probe-3.12.7.json and
  the exploratory script. The committed reproduction is
  `packages/backend-pydantic/tests/test_session_concurrency.py`; the existing autouse
  offline fixture applies. No API key, network provider or time-based sleep is used.

## Probe design

First complete `run("seed")` and retain real snapshot S0. On the **same backend instance**,
start A and B with the exact same S0. Each model callback records its incoming messages,
sets a started Event, then waits on its own release Event. The driver waits for both
started Events before releasing either. It releases A and awaits completion before B,
then repeats in a fresh setup with reverse completion order. All waits have 2-second
guards and cleanup cancels/drains unfinished tasks.

The independent-session variant uses that same backend instance but starts both requests
without prior history. A/B are labels for independent logical conversations in the probe,
not newly implemented session IDs. This isolates backend-wide serialization from any
history-dependent behavior. Native messages are decoded with the public
ModelMessagesTypeAdapter; no raw private SDK fields are accessed.

## Observed event ordering

OBSERVED in both Python versions, for shared and independent initial state:

| Controlled completion order | Recorded events |
|---|---|
| A then B | A:enter, B:enter, both-entered, A:return, A:done, B:return, B:done |
| B then A | A:enter, B:enter, both-entered, B:return, B:done, A:return, A:done |

The observed start order follows this probe's task creation. Tests deliberately permit
either order of the first two entries; they require both entries before either return
and enforce only the release/completion order. No scheduling fairness or latency guarantee
is inferred. A backend-wide lock would prevent the second callback from reaching the
barrier until the first was released, so these tests would time out rather than pass.

## Observed snapshot behavior

OBSERVED for both completion orders and both Python versions:

| Question | Observation |
|---|---|
| Do A/B read the same S0? | Yes. Each callback's history prefix equals decoded S0; current prompts differ. |
| Can both callbacks enter concurrently? | Yes, neither release Event is set until both have entered. |
| Does SA contain B's result? | No. Prompts: [seed, A]; text outputs: [seed-result, A-result]. |
| Does SB contain A's result? | No. Prompts: [seed, B]; text outputs: [seed-result, B-result]. |
| Are both legitimate replacement snapshots? | Both decode using the native adapter and preserve the original prefix; their payload bytes differ. They are two valid continuations, not one serialized conversation. |
| Is S0 mutated? | No, the input payload remains byte-for-byte unchanged. |
| Does native conversation identity resolve this? | SA/SB retain the same native conversation_id from S0, but are still divergent histories. |

`test_concurrent_runs_from_same_snapshot_can_fork_history` preserves these facts as a
characterization in AB and BA cases. It checks actual message contents, not just that
two tasks complete. It does not assert that the framework should commit both snapshots.
There is no state store in this probe, so no actual database lost update is claimed.

## Different-session concurrency

OBSERVED: independent runs both enter before release, return only their own prompt and
result, and have distinct native conversation IDs. The committed test
`test_independent_sessions_can_enter_model_concurrently` covers AB and BA completion.

INFERRED: a single backend-wide lock would unnecessarily serialize these unrelated runs.
One Model or Backend instance cannot be the logical session key. This experiment is not
a claim that every Model, tool, streaming path or shared dependency is concurrency-safe.

## Weak lock references

OBSERVED in both versions: asyncio.Lock supports weak references. A weak-value map keeps
the same lock while a waiting coroutine explicitly retains it as an argument and while
that coroutine holds it. After completion and dropping the last strong reference, GC
removes the entry. The committed standard-library probe also confirms that the locked
flag itself does not keep an otherwise unreferenced Lock alive.

The test uses public acquire/release/async-with and weakref APIs, not `_waiters` or private
event-loop attributes. It is a local reference-lifetime experiment, not a production
registry. These observations accord with the [weakref documentation](https://docs.python.org/3.12/library/weakref.html#weakref.WeakValueDictionary).

INFERRED: a weak map is viable only when lookup/create/retention happens without an await,
and every waiter/holder maintains a strong reference through its entire operation. GC
cleanup is not a substitute for that invariant. Deleting an entry at unlock while a waiter
still has the old lock can create a second lock for the same session. PROPOSED: explicit
reference-counted entries are easier to audit; compare alternatives in ADR-0002.

## Cancellation notes

OBSERVED from the Phase 1C regression suite retained on main: model/tool cancellation
propagates, tool finally runs, no whole-run retry occurs, a prior snapshot stays unchanged,
and borrowed lifecycle hooks are not called. This phase's normal concurrency probes add
task cleanup on failure; they do **not** certify a future lock-owning runtime's cancellation.
The standard-library lock probe measures reference lifetimes on normal completion, not
all cancelled-waiter interleavings. Those require Phase 1D-B tests if implementation is approved.

INFERRED: a future outer layer must release lock/entry ownership when acquisition or
execution is cancelled. Awaited durable save has an additional ambiguous-commit problem
that in-memory cancellation tests cannot settle. Python wait_for is a cooperative timeout,
not a hard kill of code that suppresses cancellation; external CI job limits are separate.

## Design consequences

INFERRED from inspected Core/backend source: the adapter receives no explicit logical
session ID, owns no store/commit function and does not serialize by native history ID.
It cannot distinguish an intentional history fork from two conflicting writes to one
logical session. Object identity, payload hashes, prompts, context, model and backend
identity cannot supply that missing intent.

PROPOSED in [ADR-0002](../adr/0002-session-serialization.md): one future concrete runtime
above the unchanged AgentBackend takes a stable opaque string ID, owns latest-state
lookup and per-session serialization, and performs load/run/save inside one critical
section. Keep unrelated sessions concurrent. Defer separate store/protocol abstractions
until a concrete persistence requirement justifies them. No in-process lock provides
multi-worker safety, no tool effect rollback is promised, and CAS alone cannot provide
exactly-once effects. This is an ADR recommendation awaiting review, not shipped behavior.

## Reproduction and scope

From the repository root in PowerShell, using an existing development environment:

```powershell
python -m pytest packages/backend-pydantic/tests/test_session_concurrency.py -q
```

Use Python 3.11 and 3.12 with the locked workspace dependencies. The suite adds five
cases (two shared-state orders, two independent-session orders, one weak-lock probe).
Full checks remain Ruff, format check, strict mypy, pytest and 100% production coverage.
Evidence records the exact interpreters, commands and results; no thresholds are lowered.
Core and adapter production source, exports, dependency manifests and uv.lock stay unchanged.
