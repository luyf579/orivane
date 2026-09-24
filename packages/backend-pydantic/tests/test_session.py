import traceback
from dataclasses import replace

import pytest
from agent_framework_core import RunRequest, SessionState, ToolDefinition
from agent_framework_pydantic import PydanticAgentBackend, _session
from pydantic import BaseModel, JsonValue
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelResponse,
    TextPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel


@pytest.mark.parametrize(
    "state",
    [
        SessionState("other", 1, "2.48.0", b"private-history"),
        SessionState("pydantic-ai", 2, "2.48.0", b"private-history"),
        SessionState("pydantic-ai", 1, "2.49.0", b"private-history"),
    ],
)
def test_envelope_rejected_before_decoder(
    state: SessionState, monkeypatch: pytest.MonkeyPatch
) -> None:
    decoded: list[bytes] = []

    def decode(payload: bytes) -> list[ModelMessage]:
        decoded.append(payload)
        return []

    monkeypatch.setattr(ModelMessagesTypeAdapter, "validate_json", decode)
    with pytest.raises(ValueError, match="Unsupported session"):
        _session.decode_state(state)
    assert decoded == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        b"secret-private-history",
        b'{"secret-private-history": true}',
        b'[{"kind":"unknown", "parts": ["secret-private-history"]}]',
        b"\xff",
    ],
)
async def test_malformed_state_fails_safely_before_model(payload: bytes) -> None:
    calls: list[int] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        return ModelResponse(parts=[TextPart("unexpected")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    state = SessionState("pydantic-ai", 1, "2.48.0", payload)
    with pytest.raises(ValueError, match="Invalid native session payload") as exc:
        await backend.run(RunRequest("continue", None, state))
    assert calls == [] and state.payload == payload
    assert "secret-private-history" not in str(exc.value)
    assert "secret-private-history" not in "".join(traceback.format_exception(exc.value))


@pytest.mark.asyncio
async def test_dependencies_and_native_history_continue_without_double_append() -> None:
    class Parameters(BaseModel):
        value: int

    context: list[int] = []

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        assert ctx is context
        ctx.append(args.value)
        return args.value

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        # TestModel may skip a tool already present in history. Explicitly request
        # one new call for each user turn to test two complete native round-trips.
        if isinstance(messages[-1].parts[-1], UserPromptPart):
            return ModelResponse(parts=[ToolCallPart("record", {"value": 7})])
        return ModelResponse(parts=[TextPart("done")])

    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("record", "Record integer", Parameters, invoke)],
    )
    first = await backend.run(RunRequest("first", context))
    original = replace(first.next_state)
    before = ModelMessagesTypeAdapter.validate_json(original.payload)
    second = await backend.run(RunRequest("second", context, first.next_state))
    after = ModelMessagesTypeAdapter.validate_json(second.next_state.payload)
    assert len(context) == 2
    assert first.next_state == original
    assert len(after) == 2 * len(before)
    assert after[: len(before)] == before
    prompts = [p.content for m in after for p in m.parts if isinstance(p, UserPromptPart)]
    assert prompts == ["first", "second"]
    assert after[-1].conversation_id == before[-1].conversation_id
    assert after[-1].run_id != before[-1].run_id
    assert (
        ModelMessagesTypeAdapter.validate_json(ModelMessagesTypeAdapter.dump_json(after)) == after
    )
