import asyncio

import pytest
from orivane_core import InMemorySessionRuntime, RunRequest, RunResult, SessionState


class FakeBackend:
    """Only the test fake understands how its deterministic opaque bytes are made."""

    def __init__(self) -> None:
        self.calls: list[RunRequest[object]] = []
        self.started: dict[str, asyncio.Event] = {}
        self.blockers: dict[str, asyncio.Event] = {}
        self.failures: set[str] = set()
        self.error = RuntimeError("offline backend failure")

    async def run(self, request: RunRequest[object]) -> RunResult[str]:
        self.calls.append(request)
        self.started.setdefault(request.prompt, asyncio.Event()).set()
        if request.prompt in self.blockers:
            await self.blockers[request.prompt].wait()
        if request.prompt in self.failures:
            raise self.error
        return RunResult(
            request.prompt, SessionState("fake", 1, "v0", b"\x00\xff" + request.prompt.encode())
        )

    async def wait_started(self, prompt: str) -> None:
        await asyncio.wait_for(self.started.setdefault(prompt, asyncio.Event()).wait(), timeout=2)


async def drain(*tasks: asyncio.Task[RunResult[str]]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2)


async def join_session(
    runtime: InMemorySessionRuntime[object, str], prompt: str, joining: asyncio.Event
) -> RunResult[str]:
    # No await between this signal and run's synchronous retain. When the driver
    # resumes, this caller has reached the held session lock and is counted.
    joining.set()
    return await runtime.run("s", prompt, None)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, None])
def test_capacity_requires_positive_integer(limit: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        InMemorySessionRuntime(FakeBackend(), max_sessions=limit)


@pytest.mark.asyncio
@pytest.mark.parametrize("session_id", ["", None, 42])
async def test_invalid_session_ids_rejected_at_every_entry_point(session_id: str) -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=2)
    with pytest.raises(ValueError, match="non-empty string"):
        runtime.create_session(session_id)
    with pytest.raises(ValueError, match="non-empty string"):
        await runtime.run(session_id, "private prompt", {"secret": "private context"})
    with pytest.raises(ValueError, match="non-empty string"):
        runtime.delete_session(session_id)
    assert not backend.calls
    assert not runtime._sessions and not runtime._entries


@pytest.mark.asyncio
async def test_duplicate_creation_never_resets_committed_state() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("s")
    with pytest.raises(ValueError, match="already exists"):
        runtime.create_session("s")
    context = object()
    result = await runtime.run("s", "first", context)
    assert backend.calls[0].state is None
    assert backend.calls[0].context is context
    assert runtime._sessions["s"] is result.next_state  # Commit is visible before success returns.
    with pytest.raises(ValueError, match="already exists"):
        runtime.create_session("s")
    await runtime.run("s", "second", context)
    assert backend.calls[-1].state is result.next_state


@pytest.mark.asyncio
async def test_missing_run_and_delete_fail_without_creating_session() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    with pytest.raises(KeyError, match="Unknown session") as exc:
        await runtime.run("unknown", "private prompt", {"secret": "private context"})
    assert "private" not in str(exc.value)
    with pytest.raises(KeyError, match="Unknown session"):
        runtime.delete_session("unknown")
    assert not runtime._sessions and not runtime._entries and not backend.calls


@pytest.mark.asyncio
async def test_capacity_counts_idle_sessions_and_delete_frees_only_its_slot() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=2)
    runtime.create_session("A")
    runtime.create_session("B")
    b = await runtime.run("B", "B-first", None)
    assert not runtime._entries
    with pytest.raises(RuntimeError, match="capacity"):
        runtime.create_session("C")
    await runtime.run("B", "B-second", None)  # Existing session still works at capacity.
    assert backend.calls[-1].state is b.next_state
    b_state = runtime._sessions["B"]
    runtime.delete_session("A")
    runtime.create_session("C")
    assert runtime._sessions["B"] is b_state
    assert runtime._sessions["C"] is None
    with pytest.raises(KeyError):
        await runtime.run("A", "deleted", None)
    runtime.delete_session("C")
    runtime.create_session("A")
    await runtime.run("A", "recreated", None)
    assert backend.calls[-1].state is None


@pytest.mark.asyncio
async def test_same_session_serializes_and_loads_after_first_commit() -> None:
    backend = FakeBackend()
    backend.blockers["A"] = asyncio.Event()
    backend.blockers["B"] = asyncio.Event()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("s")
    a = asyncio.create_task(runtime.run("s", "A", None))
    tasks = [a]
    try:
        await backend.wait_started("A")
        entry = runtime._entries["s"]
        joining = asyncio.Event()
        b = asyncio.create_task(join_session(runtime, "B", joining))
        tasks.append(b)
        await asyncio.wait_for(joining.wait(), timeout=2)
        assert runtime._entries["s"] is entry and entry.users == 2
        assert [call.prompt for call in backend.calls] == ["A"]
        assert not b.done()
        with pytest.raises(RuntimeError, match="busy"):
            runtime.delete_session("s")
        backend.blockers["A"].set()
        first = await asyncio.wait_for(a, timeout=2)
        await backend.wait_started("B")
        assert runtime._entries["s"] is entry and entry.users == 1
        assert backend.calls[-1].state is first.next_state
        assert runtime._sessions["s"] is first.next_state
        backend.blockers["B"].set()
        second = await asyncio.wait_for(b, timeout=2)
        assert runtime._sessions["s"] is second.next_state
        assert entry.users == 0 and not runtime._entries
    finally:
        await drain(*tasks)


@pytest.mark.asyncio
async def test_different_sessions_overlap() -> None:
    backend = FakeBackend()
    backend.blockers = {label: asyncio.Event() for label in "AB"}
    runtime = InMemorySessionRuntime(backend, max_sessions=2)
    for label in "AB":
        runtime.create_session(label)
    tasks = [asyncio.create_task(runtime.run(label, label, None)) for label in "AB"]
    try:
        await asyncio.wait_for(
            asyncio.gather(*(backend.wait_started(label) for label in "AB")), timeout=2
        )
        assert len(backend.calls) == 2 and all(call.state is None for call in backend.calls)
        assert runtime._entries["A"] is not runtime._entries["B"]
        assert all(not task.done() for task in tasks)
        for label in "AB":
            backend.blockers[label].set()
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=2)
        assert [result.output for result in results] == ["A", "B"]
        assert not runtime._entries
    finally:
        await drain(*tasks)


@pytest.mark.asyncio
async def test_failure_keeps_old_state_and_does_not_retry() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("s")
    seed = await runtime.run("s", "seed", None)
    backend.failures.add("fail")
    with pytest.raises(RuntimeError, match="offline backend failure") as exc:
        await runtime.run("s", "fail", None)
    assert exc.value is backend.error
    assert [call.prompt for call in backend.calls] == ["seed", "fail"]
    assert runtime._sessions["s"] is seed.next_state
    assert not runtime._entries
    await runtime.run("s", "after", None)
    assert backend.calls[-1].state is seed.next_state


@pytest.mark.asyncio
async def test_holder_cancellation_preserves_state_and_allows_future_run() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("s")
    seed = await runtime.run("s", "seed", None)
    backend.blockers["A"] = asyncio.Event()
    task = asyncio.create_task(runtime.run("s", "A", None))
    try:
        await backend.wait_started("A")
        with pytest.raises(RuntimeError, match="busy"):
            runtime.delete_session("s")
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
        assert task.cancelled()
        assert runtime._sessions["s"] is seed.next_state
        assert not runtime._entries
        await asyncio.wait_for(runtime.run("s", "C", None), timeout=2)
        assert backend.calls[-1].state is seed.next_state
        assert [call.prompt for call in backend.calls] == ["seed", "A", "C"]
    finally:
        await drain(task)


@pytest.mark.asyncio
async def test_cancelled_waiter_keeps_holder_entry_and_later_waiter_serialized() -> None:
    backend = FakeBackend()
    backend.blockers["A"] = asyncio.Event()
    backend.blockers["C"] = asyncio.Event()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("s")
    a = asyncio.create_task(runtime.run("s", "A", None))
    tasks = [a]
    try:
        await backend.wait_started("A")
        entry = runtime._entries["s"]
        joining_b = asyncio.Event()
        b = asyncio.create_task(join_session(runtime, "B", joining_b))
        tasks.append(b)
        await asyncio.wait_for(joining_b.wait(), timeout=2)
        assert entry.users == 2
        b.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(b, timeout=2)
        assert runtime._entries["s"] is entry and entry.users == 1
        assert entry.lock.locked() and not a.done()
        joining_c = asyncio.Event()
        c = asyncio.create_task(join_session(runtime, "C", joining_c))
        tasks.append(c)
        await asyncio.wait_for(joining_c.wait(), timeout=2)
        assert runtime._entries["s"] is entry and entry.users == 2
        assert [call.prompt for call in backend.calls] == ["A"]
        backend.blockers["A"].set()
        first = await asyncio.wait_for(a, timeout=2)
        await backend.wait_started("C")
        assert runtime._entries["s"] is entry and entry.users == 1
        assert backend.calls[-1].state is first.next_state
        backend.blockers["C"].set()
        await asyncio.wait_for(c, timeout=2)
        assert [call.prompt for call in backend.calls] == ["A", "C"]
        assert not runtime._entries
    finally:
        await drain(*tasks)


@pytest.mark.asyncio
async def test_cancelled_holder_releases_same_entry_to_existing_waiter() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("s")
    seed = await runtime.run("s", "seed", None)
    backend.blockers = {label: asyncio.Event() for label in "AB"}
    a = asyncio.create_task(runtime.run("s", "A", None))
    tasks = [a]
    try:
        await backend.wait_started("A")
        entry = runtime._entries["s"]
        joining = asyncio.Event()
        b = asyncio.create_task(join_session(runtime, "B", joining))
        tasks.append(b)
        await asyncio.wait_for(joining.wait(), timeout=2)
        assert entry.users == 2
        a.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(a, timeout=2)
        await backend.wait_started("B")
        assert runtime._entries["s"] is entry and entry.users == 1
        assert runtime._sessions["s"] is seed.next_state
        assert backend.calls[-1].state is seed.next_state
        backend.blockers["B"].set()
        result = await asyncio.wait_for(b, timeout=2)
        assert runtime._sessions["s"] is result.next_state
        assert [call.prompt for call in backend.calls] == ["seed", "A", "B"]
        assert not runtime._entries
    finally:
        await drain(*tasks)


@pytest.mark.asyncio
async def test_idle_entry_cleanup_does_not_discard_state_or_capacity() -> None:
    backend = FakeBackend()
    runtime = InMemorySessionRuntime(backend, max_sessions=30)
    for index in range(30):
        session_id = str(index)
        runtime.create_session(session_id)
        first = await runtime.run(session_id, "first", None)
        assert not runtime._entries
        await runtime.run(session_id, "second", None)
        assert backend.calls[-1].state is first.next_state
        assert not runtime._entries
    assert len(runtime._sessions) == 30
    with pytest.raises(RuntimeError, match="capacity"):
        runtime.create_session("extra")
    for index in range(30):
        runtime.delete_session(str(index))
    assert not runtime._sessions and not runtime._entries
