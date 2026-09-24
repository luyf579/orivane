import json

import pytest
from agent_framework_core import RunRequest, ToolDefinition
from agent_framework_pydantic import PydanticAgentBackend
from agent_framework_pydantic._tools import build_tool
from pydantic import BaseModel, ConfigDict, JsonValue
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel as OfflineModel


class Parameters(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    value: int


def test_injected_context_excluded_from_schema() -> None:
    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        return args.value

    tool = build_tool(ToolDefinition("record", "Record value", Parameters, invoke))
    schema = tool.tool_def.parameters_json_schema
    assert set(schema["properties"]) == {"value"}
    assert schema["properties"]["value"]["type"] == "integer"
    assert schema["additionalProperties"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_args", [{"value": "private-value"}, {"value": 7, "extra": "private-value"}]
)
async def test_invalid_retry_then_valid_invokes_once(bad_args: dict[str, object]) -> None:
    effects: list[int] = []
    calls = 0

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        assert ctx is effects
        assert isinstance(args, Parameters)
        ctx.append(args.value)
        return {"value": args.value, "nested": [True, None, "ok"]}

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(parts=[ToolCallPart("record", bad_args)])
        if calls == 2:
            assert effects == []
            retries = [p for m in messages for p in m.parts if isinstance(p, RetryPromptPart)]
            assert len(retries) == 1
            assert "Invalid tool arguments" in str(retries[0].content)
            assert "private-value" not in str(retries[0].content)
            return ModelResponse(parts=[ToolCallPart("record", {"value": 7})])
        return ModelResponse(parts=[TextPart("done")])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("record", "Record value", Parameters, invoke)],
    )
    result = await backend.run(RunRequest("record", effects))
    assert result.output == "done" and effects == [7] and calls == 3
    history = ModelMessagesTypeAdapter.validate_json(result.next_state.payload)
    returned = [p for m in history for p in m.parts if isinstance(p, ToolReturnPart)]
    assert len(returned) == 1
    assert json.loads(json.dumps(returned[0].content)) == {"value": 7, "nested": [True, None, "ok"]}


@pytest.mark.asyncio
async def test_always_invalid_never_invokes_business_tool() -> None:
    effects: list[int] = []

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        ctx.append(args.value)
        return args.value

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("record", {"value": "invalid"})])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("record", "Record value", Parameters, invoke)],
    )
    with pytest.raises(UnexpectedModelBehavior):
        await backend.run(RunRequest("record", effects))
    assert effects == []


@pytest.mark.asyncio
async def test_heterogeneous_tools_keep_their_own_models_and_context() -> None:
    class ContextArgument(BaseModel):
        ctx: str  # a business field must not collide with the injected positional context

    effects: list[str] = []

    async def record(ctx: list[str], args: Parameters) -> JsonValue:
        assert ctx is effects and isinstance(args, Parameters)
        ctx.append("integer")
        return args.value

    async def label(ctx: list[str], args: ContextArgument) -> JsonValue:
        assert ctx is effects and isinstance(args, ContextArgument)
        ctx.append("string")
        return args.ctx

    backend: PydanticAgentBackend[list[str], str] = PydanticAgentBackend(
        OfflineModel(call_tools=["record", "label"], custom_output_text="done"),
        output_type=str,
        tools=[
            ToolDefinition("record", "Record integer", Parameters, record),
            ToolDefinition("label", "Record string", ContextArgument, label),
        ],
    )
    assert (await backend.run(RunRequest("record both", effects))).output == "done"
    assert sorted(effects) == ["integer", "string"]
