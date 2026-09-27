import io
import json
import sys
from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from orivane_cli._main import main
from orivane_cli._trace import capture, format_spans


@pytest.fixture
def local_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    # Model the public one-time installation without resetting private OTel globals.
    current: list[trace.TracerProvider] = [trace.ProxyTracerProvider()]
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: current[0])

    def install(provider: trace.TracerProvider) -> None:
        current[0] = provider

    monkeypatch.setattr(trace, "set_tracer_provider", install)


@pytest.mark.parametrize("instrumented", [False, True])
def test_cli_trace_output_and_provider_before_module_and_factory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    local_provider: None,
    instrumented: bool,
) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "trace_app:create_runner"\n'
    )
    (tmp_path / "trace_app.py").write_text(
        """from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from orivane_core import Workflow
assert isinstance(trace.get_tracer_provider(), TracerProvider)
def create_runner():
    assert isinstance(trace.get_tracer_provider(), TracerProvider)
    async def run(prompt):
        return prompt
    return """
        + ('Workflow[str]().then("work", run).run' if instrumented else "run")
        + "\n"
    )
    monkeypatch.delitem(sys.modules, "trace_app", raising=False)
    monkeypatch.setattr(sys, "stdin", io.StringIO("SECRET_PROMPT_CLI_9f12"))
    original = sys.path[:]
    assert main(["trace", str(tmp_path)]) == 0
    assert sys.path == original
    captured = capsys.readouterr()
    result, structural = captured.out.split("\nTRACE\n", 1)
    assert result == "SECRET_PROMPT_CLI_9f12"
    assert "SECRET_" not in structural and captured.err == ""
    if instrumented:
        captured_rows = [json.loads(line) for line in structural.splitlines()]
        rows = {row["name"]: row for row in captured_rows}
        assert set(rows) == {"agent_framework.workflow.run", "agent_framework.workflow.node"}
        assert (
            rows["agent_framework.workflow.node"]["parent_span_id"]
            == rows["agent_framework.workflow.run"]["span_id"]
        )
    else:
        assert structural == "(no spans)\n"


@pytest.mark.parametrize("fail", [False, True])
def test_cli_owned_provider_always_flushes_and_shuts_down(
    local_provider: None, monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    calls: list[str] = []
    flush_original, shutdown_original = TracerProvider.force_flush, TracerProvider.shutdown

    def flush(self: TracerProvider, timeout_millis: int = 30000) -> bool:
        calls.append("flush")
        return flush_original(self, timeout_millis)

    def shutdown(self: TracerProvider) -> None:
        calls.append("shutdown")
        shutdown_original(self)

    monkeypatch.setattr(TracerProvider, "force_flush", flush)
    monkeypatch.setattr(TracerProvider, "shutdown", shutdown)
    error = RuntimeError("SECRET_EXCEPTION_CLI_9f12")
    try:
        with capture():
            if fail:
                raise error
    except RuntimeError as caught:
        assert caught is error
    assert calls == ["flush", "shutdown"]


@pytest.mark.parametrize("code", ['"SECRET_SYSTEM_EXIT_CLI_9f12"', "17"])
def test_cli_trace_systemexit_cleans_provider_without_partial_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    local_provider: None,
    code: str,
) -> None:
    calls: list[str] = []
    flush_original, shutdown_original = TracerProvider.force_flush, TracerProvider.shutdown

    def flush(self: TracerProvider, timeout_millis: int = 30000) -> bool:
        calls.append("flush")
        return flush_original(self, timeout_millis)

    def shutdown(self: TracerProvider) -> None:
        calls.append("shutdown")
        shutdown_original(self)

    monkeypatch.setattr(TracerProvider, "force_flush", flush)
    monkeypatch.setattr(TracerProvider, "shutdown", shutdown)
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "trace_exit_app:create_runner"\n'
    )
    (tmp_path / "trace_exit_app.py").write_text(
        "from opentelemetry import trace\ndef create_runner():\n    async def run(prompt):\n"
        '        with trace.get_tracer("test").start_as_current_span("work"):\n'
        f"            raise SystemExit({code})\n    return run\n"
    )
    monkeypatch.delitem(sys.modules, "trace_exit_app", raising=False)
    monkeypatch.setattr(sys, "stdin", io.StringIO("SECRET_PROMPT_CLI_9f12"))
    original = sys.path[:]
    assert main(["trace", str(tmp_path)]) == 1
    assert sys.path == original
    assert calls == ["flush", "shutdown"]
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == "Run failed: SystemExit\n"


def test_cli_shutdown_even_if_flush_raises(
    local_provider: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    closed: list[bool] = []
    original = TracerProvider.shutdown

    def flush(self: TracerProvider, timeout_millis: int = 30000) -> bool:
        raise RuntimeError("flush failed")

    def shutdown(self: TracerProvider) -> None:
        closed.append(True)
        original(self)

    monkeypatch.setattr(TracerProvider, "force_flush", flush)
    monkeypatch.setattr(TracerProvider, "shutdown", shutdown)
    with pytest.raises(RuntimeError, match="flush failed"):
        with capture():
            pass
    assert closed == [True]


def test_cli_trace_formatter_allowlist_ignores_sensitive_native_attributes_and_events() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    secret = "SECRET_CONTEXT_CLI_9f12"
    try:
        with provider.get_tracer("test").start_as_current_span("safe-parent") as parent:
            parent.set_attribute("prompt", secret)
            parent.set_attribute("gen_ai.tool.definitions", secret)
            parent.set_attribute("session_id", secret)
            parent.set_attribute("agent_framework.run_id", "excluded even though opaque")
            parent.set_attribute("agent_framework.operation", "run")
            parent.set_attribute("gen_ai.operation.name", "chat")
            parent.add_event("SECRET_EXCEPTION_CLI_9f12", {"exception.message": secret})
            parent.set_status(trace.Status(trace.StatusCode.ERROR, secret))
            with provider.get_tracer("test").start_as_current_span("safe-child"):
                pass
        spans = exporter.get_finished_spans()
        text = format_spans(spans)
        assert text == format_spans(list(reversed(spans)))
        assert "SECRET_" not in text and "excluded even though opaque" not in text
        captured_rows = [json.loads(line) for line in text.splitlines()]
        rows = {row["name"]: row for row in captured_rows}
        parent_row, child_row = rows["safe-parent"], rows["safe-child"]
        assert parent_row["attributes"] == {
            "agent_framework.operation": "run",
            "gen_ai.operation.name": "chat",
        }
        assert parent_row["status"] == "ERROR"
        assert child_row["parent_span_id"] == parent_row["span_id"]
        assert len(parent_row["trace_id"]) == 32 and len(parent_row["span_id"]) == 16
        assert set(parent_row) == {
            "name",
            "trace_id",
            "span_id",
            "parent_span_id",
            "status",
            "attributes",
        }
    finally:
        provider.shutdown()


def test_cli_trace_formatter_accepts_empty_and_missing_optional_span_fields() -> None:
    assert format_spans([]) == "(no spans)"
    row = json.loads(format_spans([ReadableSpan("minimal")]))
    assert row["trace_id"] is row["span_id"] is row["parent_span_id"] is None
    assert row["attributes"] == {}
