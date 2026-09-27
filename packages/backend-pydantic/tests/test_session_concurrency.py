"""Characterize missing upper-layer serialization, not endorse history forks."""

import asyncio
import gc
import weakref

import pytest
from orivane_core import RunRequest, RunResult, SessionState
from orivane_pydantic import PydanticAgentBackend
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel


def prompts(messages: list[ModelMessage]) -> list[str]:
    return [
        part.content
        for message in messages
        for part in message.parts
        if isinstance(part, UserPromptPart) and isinstance(part.content, str)
    ]


def outputs(messages: list[ModelMessage]) -> list[str]:
    return [
        part.content for message in messages for part in message.parts if isinstance(part, TextPart)
    ]


async def complete_pair(
    backend: PydanticAgentBackend[None, str],
    state: SessionState | None,
    entered: dict[str, asyncio.Event],
    release: dict[str, asyncio.Event],
    events: list[str],
    order: str,
) -> dict[str, RunResult[str]]:
    tasks = {
        label: asyncio.create_task(backend.run(RunRequest(label, None, state))) for label in "AB"
    }
    results: dict[str, RunResult[str]] = {}
    try:
        await asyncio.wait_for(asyncio.gather(*(e.wait() for e in entered.values())), timeout=2)
        assert all(not task.done() for task in tasks.values())
        assert set(events) == {"A:enter", "B:enter"}
        events.append("both-entered")
        for label in order:
            release[label].set()
            results[label] = await asyncio.wait_for(tasks[label], timeout=2)
            events.append(f"{label}:done")
        assert events[2:] == [
            "both-entered",
            f"{order[0]}:return",
            f"{order[0]}:done",
            f"{order[1]}:return",
            f"{order[1]}:done",
        ]
        return results
    finally:
        for task in tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.wait_for(asyncio.gather(*tasks.values(), return_exceptions=True), timeout=2)


@pytest.mark.asyncio
@pytest.mark.parametrize("order", ["AB", "BA"])
async def test_concurrent_runs_from_same_snapshot_can_fork_history(order: str) -> None:
    entered = {label: asyncio.Event() for label in "AB"}
    release = {label: asyncio.Event() for label in "AB"}
    histories: dict[str, bytes] = {}
    events: list[str] = []

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        label = prompts(messages)[-1]
        if label in entered:
            histories[label] = ModelMessagesTypeAdapter.dump_json(messages)
            events.append(f"{label}:enter")
            entered[label].set()
            await release[label].wait()
            events.append(f"{label}:return")
        return ModelResponse(parts=[TextPart(f"{label}-result")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    first = await asyncio.wait_for(backend.run(RunRequest("seed", None)), timeout=2)
    state = first.next_state
    original = state.payload
    prior = ModelMessagesTypeAdapter.validate_json(original)
    results = await complete_pair(backend, state, entered, release, events, order)
    assert state.payload == original
    assert results["A"].next_state.payload != results["B"].next_state.payload
    for label in "AB":
        incoming = ModelMessagesTypeAdapter.validate_json(histories[label])
        final = ModelMessagesTypeAdapter.validate_json(results[label].next_state.payload)
        assert incoming[: len(prior)] == prior
        assert final[: len(prior)] == prior
        assert prompts(incoming) == ["seed", label]
        assert prompts(final) == ["seed", label]
        assert outputs(final) == ["seed-result", f"{label}-result"]
        assert results[label].output == f"{label}-result"
        assert final[-1].conversation_id == prior[-1].conversation_id
        assert events.count(f"{label}:enter") == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("order", ["AB", "BA"])
async def test_independent_sessions_can_enter_model_concurrently(order: str) -> None:
    entered = {label: asyncio.Event() for label in "AB"}
    release = {label: asyncio.Event() for label in "AB"}
    events: list[str] = []

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert len(messages) == 1  # Neither independent run received prior history.
        label = prompts(messages)[-1]
        events.append(f"{label}:enter")
        entered[label].set()
        await release[label].wait()
        events.append(f"{label}:return")
        return ModelResponse(parts=[TextPart(f"{label}-result")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    results = await complete_pair(backend, None, entered, release, events, order)
    histories = {
        label: ModelMessagesTypeAdapter.validate_json(results[label].next_state.payload)
        for label in "AB"
    }
    assert histories["A"][-1].conversation_id != histories["B"][-1].conversation_id
    for label in "AB":
        assert prompts(histories[label]) == [label]
        assert outputs(histories[label]) == [f"{label}-result"]
        assert results[label].output == f"{label}-result"
        assert events.count(f"{label}:enter") == 1


@pytest.mark.asyncio
async def test_weak_lock_entry_tracks_waiter_and_holder_references() -> None:
    # A standard-library reference-lifetime probe, not a session lock registry.
    locks: weakref.WeakValueDictionary[str, asyncio.Lock] = weakref.WeakValueDictionary()
    lock = asyncio.Lock()
    locks["example"] = lock
    reference = weakref.ref(lock)
    await asyncio.wait_for(lock.acquire(), timeout=2)
    started = asyncio.Event()
    acquired = asyncio.Event()
    release = asyncio.Event()

    async def waiter(retained: asyncio.Lock) -> None:
        started.set()
        async with retained:
            acquired.set()
            await release.wait()

    task = asyncio.create_task(waiter(lock))
    try:
        await asyncio.wait_for(started.wait(), timeout=2)
        del lock
        gc.collect()
        assert reference() is not None
        assert locks["example"] is reference()
        assert not acquired.is_set()
        locks["example"].release()
        await asyncio.wait_for(acquired.wait(), timeout=2)
        assert locks["example"] is reference()
        release.set()
        await asyncio.wait_for(task, timeout=2)
    finally:
        if not task.done():
            task.cancel()
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=2)
    del task
    gc.collect()
    assert reference() is None
    assert not locks

    # A locked flag itself does not keep the lock alive without a strong reference.
    unretained = asyncio.Lock()
    locks["example"] = unretained
    reference = weakref.ref(unretained)
    await asyncio.wait_for(unretained.acquire(), timeout=2)
    del unretained
    gc.collect()
    assert reference() is None
    assert not locks
