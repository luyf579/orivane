"""One-process, local SDK ownership and allowlisted structural formatting."""

import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_ATTRIBUTES = frozenset(
    {
        "orivane.component",
        "orivane.operation",
        "orivane.node.name",
        "orivane.node.kind",
        "orivane.backend.id",
        "orivane.outcome",
        "gen_ai.operation.name",
    }
)


class _ProviderConfiguredError(Exception):
    pass


@contextmanager
def capture() -> Iterator[InMemorySpanExporter]:
    if not isinstance(trace.get_tracer_provider(), trace.ProxyTracerProvider):
        raise _ProviderConfiguredError
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    try:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        yield exporter
    finally:
        try:
            provider.force_flush()
        finally:
            provider.shutdown()


def format_spans(spans: Sequence[ReadableSpan]) -> str:
    if not spans:
        return "(no spans)"
    rows = []
    for span in sorted(spans, key=lambda item: (item.start_time or 0, item.name)):
        context = span.context
        rows.append(
            json.dumps(
                {
                    "name": span.name,
                    "trace_id": format(context.trace_id, "032x") if context else None,
                    "span_id": format(context.span_id, "016x") if context else None,
                    "parent_span_id": format(span.parent.span_id, "016x") if span.parent else None,
                    "status": span.status.status_code.name,
                    "attributes": {
                        key: value
                        for key, value in (span.attributes or {}).items()
                        if key in _ATTRIBUTES
                    },
                },
                sort_keys=True,
            )
        )
    return "\n".join(rows)
