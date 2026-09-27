from importlib.metadata import version

import pytest
from orivane_core import SessionState
from orivane_pydantic import (
    BACKEND_ID,
    BACKEND_VERSION,
    FORMAT_VERSION,
    validate_session_state,
)


def test_supported_envelope_is_not_decoded_or_modified() -> None:
    state = SessionState(BACKEND_ID, FORMAT_VERSION, BACKEND_VERSION, b"\xffopaque")
    validate_session_state(state)
    assert state.payload == b"\xffopaque"
    assert version("pydantic-ai-slim") == BACKEND_VERSION == "2.48.0"


@pytest.mark.parametrize(
    "field,state",
    [
        ("backend_id", SessionState("other", 1, "2.48.0", b"private-history")),
        ("format_version", SessionState(BACKEND_ID, 2, "2.48.0", b"private-history")),
        ("backend_version", SessionState(BACKEND_ID, 1, "2.49.0", b"private-history")),
        ("backend_version", SessionState(BACKEND_ID, 1, "2.47.0", b"private-history")),
    ],
)
def test_incompatible_envelope_rejected_without_dropping_history(
    field: str, state: SessionState
) -> None:
    with pytest.raises(ValueError, match=field) as exc:
        validate_session_state(state)
    assert state.payload == b"private-history"
    assert "private-history" not in str(exc.value)
