"""Versioned native history; only the adapter understands payload bytes."""

from typing import TypeVar

from orivane_core import SessionState
from pydantic import ValidationError
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_ai.run import AgentRunResult

from .compatibility import BACKEND_ID, BACKEND_VERSION, FORMAT_VERSION, validate_session_state

_OutputT = TypeVar("_OutputT")


def decode_state(state: SessionState) -> list[ModelMessage]:
    validate_session_state(state)
    try:
        return ModelMessagesTypeAdapter.validate_json(state.payload)
    except ValidationError:
        raise ValueError("Invalid native session payload") from None


def encode_result(result: AgentRunResult[_OutputT]) -> SessionState:
    return SessionState(BACKEND_ID, FORMAT_VERSION, BACKEND_VERSION, result.all_messages_json())
