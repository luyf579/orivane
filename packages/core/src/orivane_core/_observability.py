"""Private, structural telemetry; host applications own all output configuration."""

import asyncio
import logging
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from time import perf_counter_ns
from uuid import uuid4

from opentelemetry import trace

_run_id: ContextVar[str | None] = ContextVar("agent_framework_run_id", default=None)


@contextmanager
def _quiet() -> Iterator[None]:
    """Isolate ordinary telemetry failures, never place business work in this scope."""
    try:
        yield
    except Exception:
        pass


def _emit(
    logger: logging.Logger,
    event: str,
    fields: dict[str, str],
    span: trace.Span,
    duration_ms: float = 0,
) -> None:
    with _quiet():
        if not logger.isEnabledFor(logging.INFO):
            return
        extra: dict[str, object] = {**fields, "af_event": event, "af_duration_ms": duration_ms}
        context = span.get_span_context()
        if context.is_valid:
            extra["af_trace_id"] = format(context.trace_id, "032x")
            extra["af_span_id"] = format(context.span_id, "016x")
        # INFO avoids logging.lastResort output when the host has no handlers.
        logger.info(event, extra=extra)


@contextmanager
def _operation(
    component: str,
    operation: str,
    *,
    node_name: str | None = None,
    node_kind: str | None = None,
    backend_id: str | None = None,
) -> Iterator[None]:
    run_id = _run_id.get() or str(uuid4())
    token = _run_id.set(run_id)
    started = perf_counter_ns()
    fields = {"af_component": component, "af_operation": operation, "af_run_id": run_id}
    attributes = {
        "agent_framework.component": component,
        "agent_framework.operation": operation,
        "agent_framework.run_id": run_id,
    }
    for key, attribute, value in (
        ("af_node_name", "agent_framework.node.name", node_name),
        ("af_node_kind", "agent_framework.node.kind", node_kind),
        ("af_backend_id", "agent_framework.backend.id", backend_id),
    ):
        if value is not None:
            fields[key] = value
            attributes[attribute] = value
    logger_name = "backend.pydantic" if component == "agent" else component
    logger = logging.getLogger("agent_framework." + logger_name)
    event = component + "." + operation
    span: trace.Span = trace.INVALID_SPAN
    stack = ExitStack()
    outcome = "success"
    terminal = "end"
    try:
        with _quiet():
            span = trace.get_tracer("agent_framework").start_span(
                "agent_framework." + event,
                attributes=attributes,
                record_exception=False,
                set_status_on_exception=False,
            )
            stack.enter_context(
                trace.use_span(span, record_exception=False, set_status_on_exception=False)
            )
        _emit(logger, event + ".start", fields, span)
        try:
            yield
        except BaseException as error:
            outcome = "cancelled" if isinstance(error, asyncio.CancelledError) else "error"
            terminal = "cancel" if outcome == "cancelled" else "error"
            fields["af_error_type"] = type(error).__name__
            raise
        finally:
            fields["af_outcome"] = outcome
            with _quiet():
                span.set_attribute("agent_framework.outcome", outcome)
                if outcome == "error":
                    span.set_attribute("error.type", fields["af_error_type"])
                    span.set_status(trace.StatusCode.ERROR)
            _emit(logger, event + "." + terminal, fields, span, (perf_counter_ns() - started) / 1e6)
    finally:
        with _quiet():
            stack.close()
        with _quiet():
            span.end()
        _run_id.reset(token)
