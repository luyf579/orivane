import traceback
from dataclasses import replace

import pytest
from orivane_core import RunRequest, SessionState, ToolDefinition
from orivane_pydantic import (
    BACKEND_ID,
    BACKEND_VERSION,
    FORMAT_VERSION,
    PydanticAgentBackend,
    _session,
)
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
        SessionState("other", FORMAT_VERSION, BACKEND_VERSION, b"private-history"),
        SessionState(BACKEND_ID, 2, BACKEND_VERSION, b"private-history"),
        SessionState(BACKEND_ID, FORMAT_VERSION, "2.48.0", b"private-history"),
        SessionState(BACKEND_ID, FORMAT_VERSION, "2.53.0", b"private-history"),
        SessionState(BACKEND_ID, FORMAT_VERSION, "2.55.0", b"private-history"),
        SessionState(BACKEND_ID, FORMAT_VERSION, "2.49.0", b"private-history"),
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
    state = SessionState(BACKEND_ID, FORMAT_VERSION, BACKEND_VERSION, payload)
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
    assert first.next_state.backend_version == BACKEND_VERSION
    original = replace(first.next_state)
    before = ModelMessagesTypeAdapter.validate_json(original.payload)
    second = await backend.run(RunRequest("second", context, first.next_state))
    assert second.next_state.backend_version == BACKEND_VERSION
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


@pytest.mark.asyncio
async def test_old_native_state_rejected_before_parser_model_and_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Genuine 2.48.0 all_messages_json history; this old snapshot must not be relabeled.
    payload = (
        b'[{"parts":[{"content":"synthetic-old-history","timestamp":"2026-1'
        b'0-04T12:28:49.616284Z","part_kind":"user-prompt"}],"timestamp":"2'
        b'026-10-04T12:28:49.616284Z","instructions":null,"kind":"request",'
        b'"run_id":"01a106e3-6a44-7489-b9dd-c015b1a5f276","conversation_id"'
        b':"01a106e3-6a44-7489-b9dd-c016fb29ab68","metadata":null,"state":"'
        b'complete"},{"parts":[{"content":"synthetic-old-response","id":nul'
        b'l,"provider_name":null,"provider_details":null,"part_kind":"text"'
        b'}],"usage":{"input_tokens":51,"cache_write_tokens":0,"cache_read_'
        b'tokens":0,"output_tokens":1,"input_audio_tokens":0,"cache_audio_r'
        b'ead_tokens":0,"output_audio_tokens":0,"details":{},"cost":null},"'
        b'model_name":"function:respond:","timestamp":"2026-10-04T12:28:49.'
        b'617283Z","kind":"response","provider_name":null,"provider_url":nu'
        b'll,"provider_details":null,"provider_response_id":null,"finish_re'
        b'ason":null,"run_id":"01a106e3-6a44-7489-b9dd-c015b1a5f276","conve'
        b'rsation_id":"01a106e3-6a44-7489-b9dd-c016fb29ab68","metadata":nul'
        b'l,"state":"complete"}]'
    )
    parser_calls: list[bytes] = []
    model_calls: list[int] = []
    tool_calls: list[int] = []

    class Parameters(BaseModel):
        value: int

    def decode(payload: bytes) -> list[ModelMessage]:
        parser_calls.append(payload)
        return []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        model_calls.append(1)
        if len(model_calls) == 1:
            return ModelResponse(parts=[ToolCallPart("record", {"value": 7})])
        return ModelResponse(parts=[TextPart("unexpected")])

    async def invoke(ctx: list[int], args: Parameters) -> JsonValue:
        ctx.append(args.value)
        return args.value

    monkeypatch.setattr(ModelMessagesTypeAdapter, "validate_json", decode)
    backend: PydanticAgentBackend[list[int], str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("record", "Record integer", Parameters, invoke)],
    )
    state = SessionState(BACKEND_ID, FORMAT_VERSION, "2.48.0", payload)
    original = replace(state)
    prompt = "synthetic-old-prompt"
    with pytest.raises(ValueError, match="backend_version") as exc:
        await backend.run(RunRequest(prompt, tool_calls, state))
    assert not parser_calls and not model_calls and not tool_calls
    assert state == original
    assert str(exc.value) == f"Unsupported session backend_version; expected {BACKEND_VERSION}"
    diagnostic = "".join(traceback.format_exception(exc.value))
    assert "synthetic-old-history" not in diagnostic and prompt not in diagnostic
