"""Private, structural telemetry; host applications own all output configuration."""

import asyncio
import logging
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from time import perf_counter_ns
from uuid import uuid4

from opentelemetry import trace

_run_id: ContextVar[str | None] = ContextVar("orivane_run_id", default=None)


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
        extra: dict[str, object] = {
            **fields,
            "orivane_event": event,
            "orivane_duration_ms": duration_ms,
        }
        context = span.get_span_context()
        if context.is_valid:
            extra["orivane_trace_id"] = format(context.trace_id, "032x")
            extra["orivane_span_id"] = format(context.span_id, "016x")
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
    fields = {
        "orivane_component": component,
        "orivane_operation": operation,
        "orivane_run_id": run_id,
    }
    attributes = {
        "orivane.component": component,
        "orivane.operation": operation,
        "orivane.run_id": run_id,
    }
    for key, attribute, value in (
        ("orivane_node_name", "orivane.node.name", node_name),
        ("orivane_node_kind", "orivane.node.kind", node_kind),
        ("orivane_backend_id", "orivane.backend.id", backend_id),
    ):
        if value is not None:
            fields[key] = value
            attributes[attribute] = value
    logger_name = "backend.pydantic" if component == "agent" else component
    logger = logging.getLogger("orivane." + logger_name)
    event = component + "." + operation
    span: trace.Span = trace.INVALID_SPAN
    stack = ExitStack()
    outcome = "success"
    terminal = "end"
    try:
        with _quiet():
            span = trace.get_tracer("orivane").start_span(
                "orivane." + event,
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
            fields["orivane_error_type"] = type(error).__name__
            raise
        finally:
            fields["orivane_outcome"] = outcome
            with _quiet():
                span.set_attribute("orivane.outcome", outcome)
                if outcome == "error":
                    span.set_attribute("error.type", fields["orivane_error_type"])
                    span.set_status(trace.StatusCode.ERROR)
            _emit(logger, event + "." + terminal, fields, span, (perf_counter_ns() - started) / 1e6)
    finally:
        with _quiet():
            stack.close()
        with _quiet():
            span.end()
        _run_id.reset(token)
