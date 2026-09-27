"""Fail closed before any future native-state decoding or history restoration."""

from typing import Final

from orivane_core import SessionState

BACKEND_ID: Final = "pydantic-ai"
FORMAT_VERSION: Final = 1
BACKEND_VERSION: Final = "2.48.0"


def validate_session_state(state: SessionState) -> None:
    """Reject unsupported envelopes without parsing, resetting, or disclosing payloads."""
    if state.backend_id != BACKEND_ID:
        raise ValueError("Unsupported session backend_id; expected pydantic-ai")
    if state.format_version != FORMAT_VERSION:
        raise ValueError("Unsupported session format_version; expected 1")
    if state.backend_version != BACKEND_VERSION:
        raise ValueError("Unsupported session backend_version; expected 2.48.0")
