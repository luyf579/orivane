import asyncio
import gc
from dataclasses import replace
from types import TracebackType
from typing import Self

import pytest
from agent_framework_core import RunRequest, RunResult, ToolDefinition
from agent_framework_pydantic import PydanticAgentBackend
from pydantic import BaseModel, JsonValue
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionDef, FunctionModel


class BorrowedModel(FunctionModel):
    """Sentinels for accidental lifecycle management by our adapter.

    Model publicly defines async context hooks. close/aclose and synchronous exit
    are duck-typing traps, not claims about PydanticAI's Model interface.
    """

    def __init__(self, function: FunctionDef) -> None:
        super().__init__(function)
        self.close_called = 0
        self.aclose_called = 0
        self.exit_called = 0
        self.aexit_called = 0
        self.aenter_called = 0

    def close(self) -> None:
        self.close_called += 1

    async def aclose(self) -> None:
        self.aclose_called += 1

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exit_called += 1

    async def __aenter__(self) -> Self:
        self.aenter_called += 1
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self.aexit_called += 1
        return await super().__aexit__(exc_type, exc_val, exc_tb)


def assert_borrowed(model: BorrowedModel) -> None:
    assert model.close_called == 0
    assert model.aclose_called == 0
    assert model.exit_called == 0
    assert model.aexit_called == 0
    assert model.aenter_called == 0


async def cancel_when_started(task: asyncio.Task[RunResult[str]], started: asyncio.Event) -> None:
    """Bound both the handshake and cancellation; drain the task on assertion failure."""
    try:
        await asyncio.wait_for(started.wait(), timeout=2)
        assert task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
        assert task.cancelled()
        # A cancelled task has no RunResult or next_state available to its caller.
        with pytest.raises(asyncio.CancelledError):
            task.result()
    finally:
        if not task.done():
            task.cancel()
            await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=2)


@pytest.mark.asyncio
async def test_model_request_cancellation_propagates() -> None:
    started = asyncio.Event()
    blocker = asyncio.Event()
    calls = 0
    cleaned = False

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls, cleaned
        calls += 1
        started.set()
        try:
            await blocker.wait()
        finally:
            cleaned = True
        return ModelResponse(parts=[TextPart("unexpected")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    task = asyncio.create_task(backend.run(RunRequest("cancel model", None)))
    await cancel_when_started(task, started)
    assert calls == 1
    assert cleaned
    assert not blocker.is_set()


@pytest.mark.asyncio
async def test_tool_cancellation_propagates_and_runs_finally() -> None:
    class Parameters(BaseModel):
        value: int

    started = asyncio.Event()
    blocker = asyncio.Event()
    effects: list[int] = []
    invocations = 0
    cleanups = 0
    model_calls = 0

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        nonlocal invocations, cleanups
        invocations += 1
        ctx.append(args.value)  # A completed external effect would not be rolled back.
        started.set()
        try:
            await blocker.wait()
        finally:
            cleanups += 1
        return args.value

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal model_calls
        model_calls += 1
        return ModelResponse(parts=[ToolCallPart("record", {"value": 7})])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("record", "Record value", Parameters, invoke)],
    )
    task = asyncio.create_task(backend.run(RunRequest("cancel tool", effects)))
    await cancel_when_started(task, started)
    assert invocations == 1
    assert model_calls == 1
    assert cleanups == 1
    assert effects == [7]


@pytest.mark.asyncio
async def test_cancelled_continuation_does_not_mutate_prior_state() -> None:
    started = asyncio.Event()
    blocker = asyncio.Event()
    calls = 0

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[TextPart("ready")])
        started.set()
        await blocker.wait()
        return ModelResponse(parts=[TextPart("unexpected")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    first = await asyncio.wait_for(backend.run(RunRequest("start", None)), timeout=2)
    assert first.output == "ready"
    old_state = first.next_state
    original = replace(old_state)
    original_bytes = bytes(old_state.payload)
    task = asyncio.create_task(backend.run(RunRequest("continue", None, old_state)))
    await cancel_when_started(task, started)
    assert calls == 2  # One successful request, one cancelled request, zero retries.
    assert first.next_state is old_state
    assert old_state == original
    assert old_state.payload == original_bytes


@pytest.mark.asyncio
async def test_backend_does_not_close_borrowed_model_after_success() -> None:
    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[TextPart("done")])

    model = BorrowedModel(respond)
    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(model, output_type=str)
    result = await asyncio.wait_for(backend.run(RunRequest("success", None)), timeout=2)
    assert result.output == "done"
    assert_borrowed(model)
    del backend
    gc.collect()
    assert_borrowed(model)


@pytest.mark.asyncio
async def test_backend_does_not_close_borrowed_model_after_failure() -> None:
    failure = RuntimeError("offline model failure")
    calls = 0

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        raise failure

    model = BorrowedModel(respond)
    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(model, output_type=str)
    with pytest.raises(RuntimeError, match="offline model failure") as exc:
        await asyncio.wait_for(backend.run(RunRequest("fail", None)), timeout=2)
    assert exc.value is failure
    assert calls == 1
    assert_borrowed(model)
    # Drop the traceback's reference to the run before checking backend destruction.
    failure.__traceback__ = None
    del backend
    gc.collect()
    assert_borrowed(model)


@pytest.mark.asyncio
async def test_backend_does_not_close_borrowed_model_after_cancellation() -> None:
    started = asyncio.Event()
    blocker = asyncio.Event()
    calls = 0

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        started.set()
        await blocker.wait()
        return ModelResponse(parts=[TextPart("unexpected")])

    model = BorrowedModel(respond)
    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(model, output_type=str)
    task = asyncio.create_task(backend.run(RunRequest("cancel", None)))
    await cancel_when_started(task, started)
    assert calls == 1
    assert_borrowed(model)
    del task, backend
    gc.collect()
    assert_borrowed(model)
