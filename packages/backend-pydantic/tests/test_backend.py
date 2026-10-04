import pytest
from orivane_core import AgentBackend, RunRequest, RunResult, ToolDefinition
from orivane_pydantic import BACKEND_VERSION, PydanticAgentBackend
from pydantic import BaseModel, JsonValue
from pydantic_ai import ModelRetry
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel as OfflineModel


class Answer(BaseModel):
    total: int


@pytest.mark.asyncio
async def test_structured_output_through_owned_protocol() -> None:
    backend: AgentBackend[None, Answer] = PydanticAgentBackend(
        OfflineModel(custom_output_args={"total": 7}), output_type=Answer
    )
    result = await backend.run(RunRequest("Return total", None))
    assert isinstance(result, RunResult)
    assert result.output == Answer(total=7)
    assert result.next_state.backend_version == BACKEND_VERSION


@pytest.mark.asyncio
async def test_instructions_and_prompt_reach_model() -> None:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.instructions == "Be brief"
        assert messages[-1].parts[0].part_kind == "user-prompt"
        return ModelResponse(parts=[TextPart("done")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str, instructions="Be brief"
    )
    assert (await backend.run(RunRequest("hello", None))).output == "done"


@pytest.mark.asyncio
async def test_business_failure_propagates_without_state_commit_or_run_retry() -> None:
    class Parameters(BaseModel):
        value: int

    effects: list[int] = []

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        ctx.append(args.value)
        raise RuntimeError("warehouse unavailable")

    calls = 0

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[TextPart("ready")])
        return ModelResponse(parts=[ToolCallPart("reserve", {"value": 7})])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("reserve", "Reserve stock", Parameters, invoke)],
    )
    first = await backend.run(RunRequest("start", effects))
    original = first.next_state.payload
    with pytest.raises(RuntimeError, match="warehouse unavailable") as exc:
        await backend.run(RunRequest("reserve", effects, first.next_state))
    assert not isinstance(exc.value, ModelRetry)
    assert effects == [7]  # side effects are not rolled back or automatically repeated
    assert calls == 2
    assert first.next_state.payload == original
