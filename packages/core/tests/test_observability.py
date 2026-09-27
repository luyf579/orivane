import asyncio
import json
import logging
from collections.abc import Iterator
from uuid import UUID

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF
from orivane_core import (
    InMemorySessionRuntime,
    RunRequest,
    RunResult,
    SessionState,
    Workflow,
)
from orivane_core._observability import _run_id


@pytest.fixture
def spans(monkeypatch: pytest.MonkeyPatch) -> Iterator[InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Patch the public getter locally; never install an irreversible global provider.
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    try:
        yield exporter
    finally:
        provider.shutdown()


async def identity(value: int) -> int:
    return value


@pytest.mark.asyncio
async def test_nested_workflow_inherits_run_id_and_restores_context(
    spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="agent_framework.workflow")
    child = Workflow[int]().branch(
        "choose", lambda value: True, if_true=identity, if_false=identity
    )
    workflow = Workflow[int]().then("child", child.run)
    assert _run_id.get() is None
    assert await workflow.run(5) == 5
    assert _run_id.get() is None
    finished = spans.get_finished_spans()
    assert len(finished) == 4
    ids = {s.attributes["agent_framework.run_id"] for s in finished if s.attributes}
    assert len(ids) == 1
    UUID(str(next(iter(ids))))
    for span in finished:
        assert span.context is not None
        matching = [
            r
            for r in caplog.records
            if r.__dict__["af_span_id"] == format(span.context.span_id, "016x")
        ]
        assert len(matching) == 2
        assert all(
            r.__dict__["af_trace_id"] == format(span.context.trace_id, "032x") for r in matching
        )
        assert matching[0].__dict__["af_run_id"] == next(iter(ids))
        assert matching[1].__dict__["af_outcome"] == "success"
        assert matching[1].__dict__["af_duration_ms"] >= 0
        assert not span.events and span.status.description is None
    root = finished[-1]
    outer_node = finished[-2]
    inner_run = finished[-3]
    inner_node = finished[-4]
    assert root.parent is None
    for parent, child_span in [
        (root, outer_node),
        (outer_node, inner_run),
        (inner_run, inner_node),
    ]:
        assert parent.context is not None and child_span.parent is not None
        assert child_span.parent.span_id == parent.context.span_id
    assert outer_node.attributes and outer_node.attributes["agent_framework.node.name"] == "child"
    assert inner_node.attributes and inner_node.attributes["agent_framework.node.kind"] == "branch"
    await Workflow[int]().run(0)
    last = spans.get_finished_spans()[-1]
    assert last.attributes and last.attributes["agent_framework.run_id"] not in ids


@pytest.mark.asyncio
async def test_concurrent_run_ids_are_isolated_at_event_barrier(
    spans: InMemorySpanExporter,
) -> None:
    entered = {1: asyncio.Event(), 2: asyncio.Event()}
    release = asyncio.Event()
    observed: dict[int, str | None] = {}

    async def blocking(value: int) -> int:
        observed[value] = _run_id.get()
        entered[value].set()
        await release.wait()
        assert _run_id.get() == observed[value]
        return value

    workflow = Workflow[int]().then("wait", blocking)
    tasks = [asyncio.create_task(workflow.run(value)) for value in [1, 2]]
    try:
        await asyncio.wait_for(asyncio.gather(*(e.wait() for e in entered.values())), timeout=2)
        assert observed[1] and observed[2] and observed[1] != observed[2]
        assert _run_id.get() is None
        release.set()
        assert await asyncio.wait_for(asyncio.gather(*tasks), timeout=2) == [1, 2]
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2)
    roots = [s for s in spans.get_finished_spans() if s.parent is None]
    assert len(roots) == 2
    assert len({s.context.trace_id for s in roots if s.context}) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("cancelled", [False, True])
async def test_errors_and_cancellation_preserve_identity_without_text(
    spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture, cancelled: bool
) -> None:
    caplog.set_level(logging.INFO, logger="agent_framework.workflow")
    error = (
        asyncio.CancelledError("SECRET_EXCEPTION_9f12")
        if cancelled
        else RuntimeError("SECRET_EXCEPTION_9f12")
    )

    async def fail(value: int) -> int:
        raise error

    with pytest.raises(type(error)) as caught:
        await Workflow[int]().then("fail", fail).run(1)
    assert caught.value is error and _run_id.get() is None
    assert len(spans.get_finished_spans()) == 2
    for span in spans.get_finished_spans():
        assert span.attributes
        assert span.attributes["agent_framework.outcome"] == ("cancelled" if cancelled else "error")
        assert span.status.status_code == (
            trace.StatusCode.UNSET if cancelled else trace.StatusCode.ERROR
        )
        assert span.status.description is None and not span.events
    terminal = [r for r in caplog.records if not r.__dict__["af_event"].endswith("start")]
    assert len(terminal) == 2
    assert all(
        r.__dict__["af_error_type"] == type(error).__name__ and r.exc_info is None for r in terminal
    )
    serialized = str([r.__dict__ for r in caplog.records]) + str(
        [s.to_json() for s in spans.get_finished_spans()]
    )
    assert "SECRET_EXCEPTION_9f12" not in serialized


@pytest.mark.asyncio
async def test_session_cancellation_does_not_commit_or_leak_id(
    spans: InMemorySpanExporter, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="agent_framework.session")
    entered = asyncio.Event()
    blocker = asyncio.Event()

    class Backend:
        async def run(self, request: RunRequest[None]) -> RunResult[str]:
            entered.set()
            await blocker.wait()
            return RunResult("done", SessionState("fake", 1, "v0", b"SECRET_PAYLOAD_9f12"))

    runtime = InMemorySessionRuntime(Backend(), max_sessions=1)
    session_id = "SECRET_SESSION_9f12"
    runtime.create_session(session_id)
    task = asyncio.create_task(runtime.run(session_id, "SECRET_PROMPT_9f12", None))
    try:
        await asyncio.wait_for(entered.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
        assert runtime._sessions[session_id] is None and not runtime._entries
        runtime.delete_session(session_id)
    finally:
        task.cancel()
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=2)
    assert _run_id.get() is None
    (span,) = spans.get_finished_spans()
    assert span.name == "agent_framework.session.run"
    assert span.attributes and span.attributes["agent_framework.outcome"] == "cancelled"
    assert "SECRET_" not in str([r.__dict__ for r in caplog.records]) + span.to_json()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [False, True])
async def test_broken_logging_formatter_never_changes_business_result(
    spans: InMemorySpanExporter, failure: bool
) -> None:
    class BrokenFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            raise RuntimeError("broken formatter")

    class Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            self.format(record)

    logger = logging.getLogger("agent_framework.workflow")
    previous = logger.level
    handler = Handler()
    handler.setFormatter(BrokenFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    error = ValueError("business failure")

    async def step(value: int) -> int:
        if failure:
            raise error
        return value + 1

    try:
        workflow = Workflow[int]().then("work", step)
        if failure:
            with pytest.raises(ValueError) as caught:
                await workflow.run(1)
            assert caught.value is error
        else:
            assert await workflow.run(1) == 2
        assert _run_id.get() is None
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)
        handler.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["start_span", "set_attribute", "end"])
async def test_framework_span_failures_do_not_change_workflow_result(
    spans: InMemorySpanExporter, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise RuntimeError("telemetry failed")

    if method == "start_span":
        monkeypatch.setattr(trace, "get_tracer", broken)
    else:
        monkeypatch.setattr(Span, method, broken)
    assert await Workflow[int]().then("work", identity).run(9) == 9
    assert _run_id.get() is None
    assert not trace.get_current_span().get_span_context().is_valid


@pytest.mark.asyncio
async def test_noop_provider_with_logging_and_disabled_logger(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    provider = trace.NoOpTracerProvider()
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    logger = logging.getLogger("agent_framework.workflow")
    caplog.set_level(logging.INFO, logger=logger.name)
    assert await Workflow[int]().run(8) == 8
    assert len(caplog.records) == 2
    assert all(
        "af_trace_id" not in r.__dict__ and "af_span_id" not in r.__dict__ for r in caplog.records
    )
    caplog.clear()
    caplog.set_level(logging.WARNING, logger=logger.name)
    assert await Workflow[int]().run(8) == 8
    assert not caplog.records and _run_id.get() is None
    assert json.dumps([r.__dict__ for r in caplog.records]) == "[]"


@pytest.mark.asyncio
async def test_host_parent_is_preserved_and_context_restored(spans: InMemorySpanExporter) -> None:
    with trace.get_tracer("host").start_as_current_span("host") as parent:
        assert await Workflow[int]().run(1) == 1
        (child,) = spans.get_finished_spans()
        assert child.parent and child.context
        assert child.parent.span_id == parent.get_span_context().span_id
        assert child.context.trace_id == parent.get_span_context().trace_id
        assert trace.get_current_span() is parent and _run_id.get() is None


@pytest.mark.asyncio
async def test_host_sampler_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider(sampler=ALWAYS_OFF)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    try:
        assert await Workflow[int]().then("work", identity).run(1) == 1
        assert not exporter.get_finished_spans()
        assert _run_id.get() is None
    finally:
        provider.shutdown()
