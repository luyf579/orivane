import pytest
from orivane_core import RunRequest, ToolDefinition
from orivane_pydantic import PydanticAgentBackend
from pydantic import BaseModel, JsonValue
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel as OfflineModel


@pytest.mark.parametrize("limit", [-1, None, float("inf"), True])
@pytest.mark.parametrize("field", ["request", "tool"])
def test_invalid_limits_rejected(limit: int, field: str) -> None:
    with pytest.raises(ValueError, match="finite non-negative integers"):
        if field == "request":
            PydanticAgentBackend[None, str](OfflineModel(), output_type=str, request_limit=limit)
        else:
            PydanticAgentBackend[None, str](OfflineModel(), output_type=str, tool_calls_limit=limit)


@pytest.mark.asyncio
async def test_zero_request_budget_never_calls_model() -> None:
    calls: list[int] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        return ModelResponse(parts=[TextPart("unexpected")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str, request_limit=0
    )
    with pytest.raises(UsageLimitExceeded):
        await backend.run(RunRequest("no budget", None))
    assert calls == []


@pytest.mark.asyncio
async def test_tool_limit_prevents_side_effects_and_is_fresh_per_run() -> None:
    class Parameters(BaseModel):
        value: int

    effects: list[int] = []

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        ctx.append(args.value)
        return args.value

    calls = 0

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        return ModelResponse(parts=[ToolCallPart("record", {"value": 7})])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tool_calls_limit=1,
        tools=[ToolDefinition("record", "Record", Parameters, invoke)],
    )
    for _ in range(2):
        with pytest.raises(UsageLimitExceeded):
            await backend.run(RunRequest("loop", effects))
    assert effects == [7, 7]
    assert calls == 4


@pytest.mark.asyncio
async def test_default_request_budget_is_finite() -> None:
    class Parameters(BaseModel):
        value: int

    effects: list[int] = []

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        ctx.append(args.value)
        return args.value

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("record", {"value": 1})])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("record", "Record", Parameters, invoke)],
    )
    with pytest.raises(UsageLimitExceeded, match="request_limit of 50"):
        await backend.run(RunRequest("loop", effects))
    assert len(effects) == 50
