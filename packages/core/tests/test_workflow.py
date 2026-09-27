import asyncio
from collections.abc import Awaitable, Callable
from typing import cast

import pytest
from orivane_core import AgentBackend, RunRequest, RunResult, SessionState, Workflow


async def increment(value: int) -> int:
    return value + 1


@pytest.mark.asyncio
async def test_empty_workflow_returns_identical_input() -> None:
    value = object()
    assert await Workflow[object]().run(value) is value


@pytest.mark.asyncio
async def test_steps_run_in_order_and_pass_exact_returned_objects() -> None:
    initial: list[str] = []
    replacement: list[str] = []
    calls: list[str] = []

    async def first(value: list[str]) -> list[str]:
        calls.append("first")
        assert value is initial
        value.append("side effect")
        return replacement

    async def second(value: list[str]) -> list[str]:
        calls.append("second")
        assert value is replacement
        value.append("result")
        return value

    workflow = Workflow[list[str]]().then("first", first).then("second", second)
    assert await workflow.run(initial) is replacement
    assert initial == ["side effect"]
    assert replacement == ["result"]
    assert calls == ["first", "second"]


@pytest.mark.asyncio
async def test_then_and_branch_composition_leave_each_original_unchanged() -> None:
    base = Workflow[int]()
    a = base.then("same-name", increment)
    b = base.branch("same-name", lambda value: True, if_true=increment, if_false=increment)
    extended_a = a.branch("branch", lambda value: False, if_true=increment, if_false=increment)
    extended_b = b.then("last", increment)
    assert a is not base and b is not base and a is not b
    assert extended_a is not a and extended_b is not b
    assert await base.run(0) == 0
    assert await a.run(0) == await b.run(0) == 1
    assert await extended_a.run(0) == await extended_b.run(0) == 2


@pytest.mark.parametrize("first_branch", [False, True])
@pytest.mark.parametrize("second_branch", [False, True])
def test_duplicate_names_share_one_namespace(first_branch: bool, second_branch: bool) -> None:
    base = Workflow[int]()
    if first_branch:
        base = base.branch("node", lambda value: True, if_true=increment, if_false=increment)
    else:
        base = base.then("node", increment)
    with pytest.raises(ValueError, match="already exists"):
        if second_branch:
            base.branch("node", lambda value: True, if_true=increment, if_false=increment)
        else:
            base.then("node", increment)


@pytest.mark.parametrize("name", ["", None, 42, True])
@pytest.mark.parametrize("branch", [False, True])
def test_invalid_names_are_rejected(name: str, branch: bool) -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        if branch:
            Workflow[int]().branch(name, lambda value: True, if_true=increment, if_false=increment)
        else:
            Workflow[int]().then(name, increment)


@pytest.mark.asyncio
async def test_names_are_explicit_and_not_canonicalized() -> None:
    workflow = (
        Workflow[int]()
        .then(" ", increment)
        .then("A", increment)
        .branch("a", lambda value: True, if_true=increment, if_false=increment)
        .then(" A ", increment)
    )
    assert [node.name for node in workflow._nodes] == [" ", "A", "a", " A "]
    assert await workflow.run(0) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", [True, False])
async def test_only_selected_branch_runs_once_and_feeds_next_step(decision: bool) -> None:
    calls: list[tuple[str, int]] = []

    def predicate(value: int) -> bool:
        calls.append(("predicate", value))
        return decision

    async def if_true(value: int) -> int:
        calls.append(("true", value))
        return value + 10

    async def if_false(value: int) -> int:
        calls.append(("false", value))
        return value - 10

    async def later(value: int) -> int:
        calls.append(("later", value))
        return value * 2

    workflow = (
        Workflow[int]()
        .then("prepare", increment)
        .branch("choose", predicate, if_true=if_true, if_false=if_false)
        .then("later", later)
    )
    for initial in [1, 4]:
        calls.clear()
        branch_input = initial + 1
        branch_output = branch_input + (10 if decision else -10)
        assert await workflow.run(initial) == branch_output * 2
        assert calls == [
            ("predicate", branch_input),
            ("true" if decision else "false", branch_input),
            ("later", branch_output),
        ]


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", [1, "yes", [], None])
async def test_predicate_requires_real_bool_before_running_either_branch(decision: bool) -> None:
    calls: list[str] = []

    def predicate(value: int) -> bool:
        calls.append("predicate")
        return decision

    async def unexpected(value: int) -> int:
        calls.append("unexpected")
        return value

    workflow = (
        Workflow[int]()
        .branch("choose", predicate, if_true=unexpected, if_false=unexpected)
        .then("later", unexpected)
    )
    with pytest.raises(TypeError, match="predicate must return bool"):
        await workflow.run(0)
    assert calls == ["predicate"]


@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["step", "predicate", "true", "false"])
@pytest.mark.parametrize("cancelled", [False, True])
async def test_failure_propagates_original_exception_without_retry_or_later_calls(
    location: str, cancelled: bool
) -> None:
    error = asyncio.CancelledError("cancelled") if cancelled else RuntimeError("failed")
    calls: list[str] = []
    effects: list[int] = []

    async def completed(value: int) -> int:
        calls.append("completed")
        effects.append(value)
        return value + 1

    async def failing_step(value: int) -> int:
        calls.append("step")
        raise error

    def predicate(value: int) -> bool:
        calls.append("predicate")
        if location == "predicate":
            raise error
        return location == "true"

    async def if_true(value: int) -> int:
        calls.append("true")
        raise error

    async def if_false(value: int) -> int:
        calls.append("false")
        raise error

    async def later(value: int) -> int:
        calls.append("later")
        return value

    workflow = Workflow[int]().then("completed", completed)
    if location == "step":
        workflow = workflow.then("failure", failing_step)
        expected = ["completed", "step"]
    else:
        workflow = workflow.branch("failure", predicate, if_true=if_true, if_false=if_false)
        expected = ["completed", "predicate"]
        if location != "predicate":
            expected.append(location)
    workflow = workflow.then("later", later)
    with pytest.raises(type(error)) as caught:
        await workflow.run(7)
    assert caught.value is error
    assert calls == expected
    assert effects == [7]  # Completed side effects are neither retried nor rolled back.


@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["step", "true", "false"])
async def test_task_cancellation_reaches_active_callable_and_stops_run(location: str) -> None:
    entered = asyncio.Event()
    blocker = asyncio.Event()
    calls: list[str] = []

    async def blocking(value: int) -> int:
        calls.append("blocking")
        entered.set()
        try:
            await blocker.wait()
        finally:
            calls.append("cleanup")
        return value

    async def unexpected(value: int) -> int:
        calls.append("unexpected")
        return value

    workflow = Workflow[int]()
    if location == "step":
        workflow = workflow.then("blocking", blocking)
    else:
        workflow = workflow.branch(
            "blocking", lambda value: location == "true", if_true=blocking, if_false=blocking
        )
    task = asyncio.create_task(workflow.then("later", unexpected).run(0))
    try:
        await asyncio.wait_for(entered.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
        assert calls == ["blocking", "cleanup"]
    finally:
        task.cancel()
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=2)


@pytest.mark.asyncio
async def test_shared_workflow_runs_overlap_without_sharing_current_values() -> None:
    entered = {1: asyncio.Event(), 10: asyncio.Event()}
    release = asyncio.Event()
    calls: list[tuple[str, int]] = []

    async def blocking(value: int) -> int:
        calls.append(("blocking", value))
        entered[value].set()
        await release.wait()
        return value + 1

    async def finish(value: int) -> int:
        calls.append(("finish", value))
        return value * 2

    workflow = Workflow[int]().then("blocking", blocking).then("finish", finish)
    tasks = [asyncio.create_task(workflow.run(value)) for value in [1, 10]]
    try:
        await asyncio.wait_for(
            asyncio.gather(*(event.wait() for event in entered.values())), timeout=2
        )
        assert all(not task.done() for task in tasks)
        assert sorted(calls) == [("blocking", 1), ("blocking", 10)]
        # Extending configuration while runs are suspended cannot affect those runs.
        extended = workflow.then("extra", increment)
        release.set()
        assert await asyncio.wait_for(asyncio.gather(*tasks), timeout=2) == [4, 22]
        assert sorted(calls) == [("blocking", 1), ("blocking", 10), ("finish", 2), ("finish", 11)]
        assert await extended.run(1) == 5
        assert await workflow.run(1) == 4
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2)


@pytest.mark.asyncio
async def test_non_awaitable_step_fails_without_running_later_steps() -> None:
    calls: list[str] = []

    def sync_step(value: int) -> int:
        calls.append("sync")
        return value

    async def later(value: int) -> int:
        calls.append("later")
        return value

    # Deliberately bypass static checking to exercise an invalid runtime caller.
    invalid = cast(Callable[[int], Awaitable[int]], sync_step)
    with pytest.raises(TypeError):
        await Workflow[int]().then("invalid", invalid).then("later", later).run(0)
    assert calls == ["sync"]


@pytest.mark.asyncio
async def test_child_workflow_is_an_ordinary_async_step() -> None:
    child = Workflow[int]().then("child", increment)

    async def invoke_child(value: int) -> int:
        return await child.run(value)

    assert await Workflow[int]().then("invoke", invoke_child).then("last", increment).run(0) == 2


@pytest.mark.asyncio
async def test_agent_contract_integration_uses_an_ordinary_closure() -> None:
    calls: list[RunRequest[None]] = []

    class FakeBackend:
        async def run(self, request: RunRequest[None]) -> RunResult[str]:
            calls.append(request)
            return RunResult("answer", SessionState("fake", 1, "v0", b"opaque"))

    backend: AgentBackend[None, str] = FakeBackend()

    async def ask(value: str) -> str:
        result = await backend.run(RunRequest(value, None))
        return result.output

    assert await Workflow[str]().then("ask", ask).run("question") == "answer"
    assert calls == [RunRequest("question", None)]
