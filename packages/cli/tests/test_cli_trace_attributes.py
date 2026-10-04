import base64
import json
from typing import cast

import pytest
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.util.types import AttributeValue
from orivane_cli._trace import _json_safe_attribute, format_spans


class _Unsupported:
    def __repr__(self) -> str:
        raise AssertionError("must not expose unsupported values")

    def __str__(self) -> str:
        raise AssertionError("must not expose unsupported values")


@pytest.mark.parametrize("value", [None, "operation", True, False, 7, -2, 1.25])
def test_trace_attribute_primitives_are_unchanged(value: object) -> None:
    assert _json_safe_attribute(value) is value


@pytest.mark.parametrize(
    "value,expected",
    [
        ("operation", "operation"),
        (None, None),
        (True, True),
        (7, 7),
        (1.25, 1.25),
        (b"operation", "operation"),
        ("操作".encode(), "操作"),
        ([b"run", b"trace"], ["run", "trace"]),
        ((b"run", b"trace"), ["run", "trace"]),
        ([b"run", (b"trace", [b"nested"])], ["run", ["trace", ["nested"]]]),
        ([], []),
        ((), []),
        (b"\xffSECRET_BYTES_CLI_9f12", "<bytes>"),
        ([b"\xffSECRET_BYTES_CLI_9f12"], ["<bytes>"]),
        ({"payload": "SECRET_MAPPING_CLI_9f12"}, "<unsupported>"),
        (_Unsupported(), "<unsupported>"),
        ([_Unsupported()], ["<unsupported>"]),
    ],
)
def test_trace_formatter_normalizes_allowlisted_attribute(value: object, expected: object) -> None:
    # Model formatter inputs directly; SDK attribute filtering differs by version.
    span = ReadableSpan("structural", attributes={"orivane.operation": cast(AttributeValue, value)})
    row = json.loads(format_spans([span]))
    assert row["attributes"] == {"orivane.operation": expected}


def test_trace_formatter_bytes_privacy_and_allowlist() -> None:
    secret = b"\xffSECRET_BYTES_CLI_9f12"
    attributes = {
        "orivane.operation": cast(AttributeValue, secret),
        "prompt": cast(AttributeValue, b"SECRET_PROMPT_CLI_9f12"),
        "input": "SECRET_INPUT_CLI_9f12",
        "output": cast(AttributeValue, b"SECRET_OUTPUT_CLI_9f12"),
        "tool.arguments": cast(AttributeValue, b"SECRET_TOOL_ARGS_CLI_9f12"),
        "tool.results": "SECRET_TOOL_RESULTS_CLI_9f12",
        "session.payload": cast(AttributeValue, b"SECRET_SESSION_CLI_9f12"),
        "exception.message": "SECRET_EXCEPTION_CLI_9f12",
    }
    text = format_spans([ReadableSpan("structural", attributes=attributes)])
    assert json.loads(text)["attributes"] == {"orivane.operation": "<bytes>"}
    assert "SECRET_" not in text
    assert repr(secret) not in text
    assert secret.hex() not in text
    assert base64.b64encode(secret).decode() not in text
