from dataclasses import fields

import agent_framework_core
import pytest
from agent_framework_core import RunRequest, RunResult, SessionState, ToolDefinition
from pydantic import BaseModel, ConfigDict, JsonValue


class Parameters(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    value: int


@pytest.mark.asyncio
async def test_owned_tool_preserves_typed_model_and_dependencies() -> None:
    effects: list[int] = []

    async def invoke(context: list[int], args: Parameters) -> JsonValue:
        context.append(args.value)
        return args.value

    tool = ToolDefinition("record", "Record one integer", Parameters, invoke)
    assert tool.parameters is Parameters
    result = await tool.invoke(effects, tool.parameters.model_validate({"value": 7}))
    assert result == 7
    assert effects == [7]


def test_records_preserve_context_and_opaque_snapshot() -> None:
    context = {"local": object()}
    payload = b"\x00\xffnot-json"
    state = SessionState("test", 1, "test-version", payload)
    request = RunRequest("hello", context, state)
    result = RunResult("done", state)
    assert request.context is context
    assert request.state is state
    assert result.next_state is state
    assert result.output == "done"
    assert state.payload is payload
    assert RunRequest("new", context).state is None


def test_public_surface_stays_minimal() -> None:
    assert set(agent_framework_core.__all__) == {
        "ToolDefinition",
        "SessionState",
        "RunRequest",
        "RunResult",
        "AgentBackend",
        "InMemorySessionRuntime",
    }
    assert {f.name for f in fields(ToolDefinition)} == {
        "name",
        "description",
        "parameters",
        "invoke",
    }
    assert {f.name for f in fields(SessionState)} == {
        "backend_id",
        "format_version",
        "backend_version",
        "payload",
    }
    assert {f.name for f in fields(RunRequest)} == {"prompt", "context", "state"}
    assert {f.name for f in fields(RunResult)} == {"output", "next_state"}
