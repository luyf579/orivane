import asyncio
import json
import logging
import os
import subprocess
import sys
from collections.abc import Iterator

import pytest
from agent_framework_core import InMemorySessionRuntime, RunRequest, ToolDefinition, Workflow
from agent_framework_core._observability import _run_id
from agent_framework_pydantic import PydanticAgentBackend
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import BaseModel, JsonValue
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel


@pytest.fixture
def spans(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> Iterator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    for name in ["workflow", "session", "backend.pydantic"]:
        caplog.set_level(logging.INFO, logger="agent_framework." + name)
    try:
        yield exporter
    finally:
        provider.shutdown()


def telemetry_text(spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture) -> str:
    # Include every captured LogRecord field, span name/attribute/event/status description.
    return json.dumps([r.__dict__ for r in caplog.records], default=str) + "\n".join(
        s.to_json() for s in spans.get_finished_spans()
    )


class Parameters(BaseModel):
    value: str


@pytest.mark.asyncio
async def test_full_chain_privacy_correlation_and_native_model_tool_spans(
    spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture
) -> None:
    calls: list[str] = []

    async def tool(context: str, args: Parameters) -> JsonValue:
        assert context == "SECRET_CONTEXT_9f12" and args.value == "SECRET_TOOL_ARG_9f12"
        calls.append("tool")
        return "SECRET_TOOL_RESULT_9f12"

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append("model")
        if any(isinstance(p, ToolReturnPart) for p in messages[-1].parts):
            return ModelResponse(parts=[TextPart("SECRET_OUTPUT_9f12")])
        return ModelResponse(parts=[ToolCallPart("lookup", {"value": "SECRET_TOOL_ARG_9f12"})])

    backend: PydanticAgentBackend[str, str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        instructions="SECRET_INSTRUCTIONS_9f12",
        tools=[ToolDefinition("lookup", "Look up a value", Parameters, tool)],
    )
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("SECRET_SESSION_9f12")

    async def ask(value: str) -> str:
        result = await runtime.run("SECRET_SESSION_9f12", value, "SECRET_CONTEXT_9f12")
        return result.output

    workflow = Workflow[str]().then("ask", ask)
    for _ in range(2):
        assert await workflow.run("SECRET_PROMPT_9f12 SECRET_PAYLOAD_9f12") == "SECRET_OUTPUT_9f12"
    saved = runtime._sessions["SECRET_SESSION_9f12"]
    assert saved is not None and b"SECRET_PAYLOAD_9f12" in saved.payload
    assert calls == ["model", "tool", "model"] * 2
    assert _run_id.get() is None
    text = telemetry_text(spans, caplog)
    for kind in [
        "PROMPT",
        "CONTEXT",
        "OUTPUT",
        "TOOL_ARG",
        "TOOL_RESULT",
        "PAYLOAD",
        "SESSION",
        "INSTRUCTIONS",
    ]:
        assert f"SECRET_{kind}_9f12" not in text
    finished = spans.get_finished_spans()
    framework = [s for s in finished if s.name.startswith("agent_framework.")]
    assert len(framework) == 8
    by_id = {s.context.span_id: s for s in finished if s.context}
    expected_parent = {
        "agent_framework.agent.run": "agent_framework.session.run",
        "agent_framework.session.run": "agent_framework.workflow.node",
        "agent_framework.workflow.node": "agent_framework.workflow.run",
    }
    for span in framework:
        assert span.attributes and span.context
        if span.name in expected_parent:
            assert span.parent and by_id[span.parent.span_id].name == expected_parent[span.name]
            parent = by_id[span.parent.span_id]
            assert parent.attributes
            assert (
                parent.attributes["agent_framework.run_id"]
                == span.attributes["agent_framework.run_id"]
            )
        records = [
            r
            for r in caplog.records
            if getattr(r, "af_span_id", None) == format(span.context.span_id, "016x")
        ]
        assert len(records) == 2
        assert all(
            r.__dict__["af_trace_id"] == format(span.context.trace_id, "032x") for r in records
        )
        assert all(
            r.__dict__["af_run_id"] == span.attributes["agent_framework.run_id"] for r in records
        )
    native = [
        s
        for s in finished
        if s.instrumentation_scope and s.instrumentation_scope.name == "pydantic-ai"
    ]
    operations = {s.attributes.get("gen_ai.operation.name") for s in native if s.attributes}
    assert {"chat", "execute_tool"} <= operations
    for span in native:
        ancestor = span
        while ancestor.parent and not ancestor.name.startswith("agent_framework."):
            ancestor = by_id[ancestor.parent.span_id]
        assert ancestor.name == "agent_framework.agent.run"


@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["model", "tool"])
async def test_native_exceptions_are_type_only_and_propagate_unchanged(
    spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture, location: str
) -> None:
    error = RuntimeError("SECRET_EXCEPTION_9f12")

    async def tool(context: None, args: Parameters) -> JsonValue:
        raise error

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if location == "model":
            raise error
        return ModelResponse(parts=[ToolCallPart("fail", {"value": "SECRET_TOOL_ARG_9f12"})])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond),
        output_type=str,
        tools=[ToolDefinition("fail", "Fail deliberately", Parameters, tool)],
    )
    with pytest.raises(RuntimeError) as caught:
        await backend.run(RunRequest("SECRET_PROMPT_9f12", None))
    assert caught.value is error and _run_id.get() is None
    assert "SECRET_" not in telemetry_text(spans, caplog)
    errors = [
        s for s in spans.get_finished_spans() if s.status.status_code == trace.StatusCode.ERROR
    ]
    assert len(errors) >= 3  # framework agent + native agent + model/tool
    assert all(s.status.description is None for s in errors)
    for span in errors:
        for event in span.events:
            assert event.attributes and "exception.message" not in event.attributes
            assert "exception.stacktrace" not in event.attributes
    assert "RuntimeError" in telemetry_text(spans, caplog)


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_concurrent_full_chains_and_cancellation(
    spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture, cancel: bool
) -> None:
    both_entered = asyncio.Event()
    release = asyncio.Event()
    observed: list[str | None] = []

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        observed.append(_run_id.get())
        if len(observed) == 2:
            both_entered.set()
        await release.wait()
        return ModelResponse(parts=[TextPart("SECRET_OUTPUT_9f12")])

    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        FunctionModel(respond), output_type=str
    )
    runtime = InMemorySessionRuntime(backend, max_sessions=2)
    for name in ["one", "two"]:
        runtime.create_session(name)

    async def ask(session: str) -> str:
        return (await runtime.run(session, "SECRET_PROMPT_9f12", None)).output

    workflow = Workflow[str]().then("ask", ask)
    tasks = [asyncio.create_task(workflow.run(name)) for name in ["one", "two"]]
    try:
        await asyncio.wait_for(both_entered.wait(), timeout=2)
        assert len(set(observed)) == 2 and None not in observed
        assert _run_id.get() is None
        if cancel:
            tasks[0].cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(tasks[0], timeout=2)
            assert runtime._sessions["one"] is None
        release.set()
        assert await asyncio.wait_for(tasks[1], timeout=2) == "SECRET_OUTPUT_9f12"
        if not cancel:
            assert await asyncio.wait_for(tasks[0], timeout=2) == "SECRET_OUTPUT_9f12"
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2)
    assert not runtime._entries and _run_id.get() is None
    assert "SECRET_" not in telemetry_text(spans, caplog)
    framework = [s for s in spans.get_finished_spans() if s.name.startswith("agent_framework.")]
    assert len(framework) == 8
    for run_id in observed:
        chain = [
            s
            for s in framework
            if s.attributes and s.attributes["agent_framework.run_id"] == run_id
        ]
        assert len(chain) == 4
        assert len({s.context.trace_id for s in chain if s.context}) == 1
    if cancel:
        cancelled = [
            s
            for s in framework
            if s.attributes and s.attributes["agent_framework.outcome"] == "cancelled"
        ]
        assert len(cancelled) == 4
        assert (
            sum(r.af_event.endswith(".cancel") for r in caplog.records if hasattr(r, "af_event"))
            == 4
        )


def test_default_process_has_no_telemetry_configuration_or_payload_output() -> None:
    script = """
import asyncio
import logging
from opentelemetry import trace
from agent_framework_core import Workflow, RunRequest
from agent_framework_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel
before = trace.get_tracer_provider()
root = logging.getLogger()
handlers, level = list(root.handlers), root.level
async def main():
    backend = PydanticAgentBackend(TestModel(custom_output_text="done"), output_type=str)
    async def ask(value):
        return (await backend.run(RunRequest(value, None))).output
    assert await Workflow[str]().then("ask", ask).run("private") == "done"
asyncio.run(main())
assert trace.get_tracer_provider() is before
assert root.handlers == handlers and root.level == level
assert not trace.get_current_span().get_span_context().is_valid
for name in ["workflow", "session", "backend.pydantic"]:
    assert not logging.getLogger("agent_framework." + name).handlers
"""
    env = os.environ.copy()
    for name in ["PYTEST_VERSION", "PYTEST_CURRENT_TEST", "CI", "PYDANTIC_AI_NO_BANNER"]:
        env.pop(name, None)
    env["AI_AGENT"] = "offline-test"
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=15, env=env
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "private" not in result.stderr and "agent_framework." not in result.stderr
    # The upstream local startup banner is separate from telemetry. Only the host
    # opts out through this public setting; the adapter never changes global policy.
    quiet = "import pydantic_ai\npydantic_ai.BANNER_ENABLED = False\n" + script
    result = subprocess.run(
        [sys.executable, "-c", quiet], capture_output=True, text=True, timeout=15, env=env
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
