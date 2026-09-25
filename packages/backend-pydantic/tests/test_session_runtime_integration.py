import asyncio

import pytest
from agent_framework_core import InMemorySessionRuntime, RunResult
from agent_framework_pydantic import PydanticAgentBackend
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


async def drain(*tasks: asyncio.Task[RunResult[str]]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2)


@pytest.mark.asyncio
async def test_runtime_serializes_native_history_continuations() -> None:
    first_started = asyncio.Event()
    release_first = asyncio.Event()
    second_joining = asyncio.Event()
    incoming: list[bytes] = []

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        incoming.append(ModelMessagesTypeAdapter.dump_json(messages))
        prompt = prompts(messages)[-1]
        if prompt == "first":
            first_started.set()
            await release_first.wait()
        return ModelResponse(parts=[TextPart(f"{prompt}-result")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("explicit-id")

    async def second_run() -> RunResult[str]:
        second_joining.set()
        return await runtime.run("explicit-id", "second", None)

    first = asyncio.create_task(runtime.run("explicit-id", "first", None))
    tasks = [first]
    try:
        await asyncio.wait_for(first_started.wait(), timeout=2)
        second = asyncio.create_task(second_run())
        tasks.append(second)
        await asyncio.wait_for(second_joining.wait(), timeout=2)
        assert len(incoming) == 1 and not second.done()
        release_first.set()
        first_result, second_result = await asyncio.wait_for(asyncio.gather(*tasks), timeout=2)
        assert first_result.output == "first-result"
        assert second_result.output == "second-result"
        assert len(incoming) == 2
        prior = ModelMessagesTypeAdapter.validate_json(first_result.next_state.payload)
        second_input = ModelMessagesTypeAdapter.validate_json(incoming[1])
        final = ModelMessagesTypeAdapter.validate_json(second_result.next_state.payload)
        assert second_input[: len(prior)] == prior
        assert final[: len(prior)] == prior
        assert prompts(final) == ["first", "second"]
        assert [p.content for m in final for p in m.parts if isinstance(p, TextPart)] == [
            "first-result",
            "second-result",
        ]
    finally:
        await drain(*tasks)


@pytest.mark.asyncio
async def test_runtime_allows_independent_native_sessions_to_overlap() -> None:
    entered = {label: asyncio.Event() for label in "AB"}
    release = asyncio.Event()
    calls: list[str] = []

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert len(messages) == 1
        label = prompts(messages)[-1]
        calls.append(label)
        entered[label].set()
        await release.wait()
        return ModelResponse(parts=[TextPart(f"{label}-result")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    runtime = InMemorySessionRuntime(backend, max_sessions=2)
    for label in "AB":
        runtime.create_session(label)
    tasks = [asyncio.create_task(runtime.run(label, label, None)) for label in "AB"]
    try:
        await asyncio.wait_for(asyncio.gather(*(e.wait() for e in entered.values())), timeout=2)
        assert sorted(calls) == ["A", "B"] and all(not task.done() for task in tasks)
        release.set()
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=2)
        assert [result.output for result in results] == ["A-result", "B-result"]
        histories = [ModelMessagesTypeAdapter.validate_json(r.next_state.payload) for r in results]
        assert [prompts(history) for history in histories] == [["A"], ["B"]]
        assert histories[0][-1].conversation_id != histories[1][-1].conversation_id
    finally:
        await drain(*tasks)
