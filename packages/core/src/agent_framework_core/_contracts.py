"""Owned business contracts; no upstream runtime types cross this boundary."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel, JsonValue

_ArgsT = TypeVar("_ArgsT", bound=BaseModel)
_DepsT = TypeVar("_DepsT")
_OutputT = TypeVar("_OutputT")


@dataclass(frozen=True, slots=True)
class ToolDefinition(Generic[_ArgsT, _DepsT]):
    """An owned tool; adapters must validate parameters before invoking it."""

    name: str
    description: str
    parameters: type[_ArgsT]
    invoke: Callable[[_DepsT, _ArgsT], Awaitable[JsonValue]]


@dataclass(frozen=True, slots=True)
class SessionState:
    """Opaque native snapshot; cross-backend lossless migration is not promised."""

    backend_id: str
    format_version: int
    backend_version: str
    payload: bytes


@dataclass(frozen=True, slots=True)
class RunRequest(Generic[_DepsT]):
    """One prompt with local dependencies and optional prior state."""

    prompt: str
    context: _DepsT
    state: SessionState | None = None


@dataclass(frozen=True, slots=True)
class RunResult(Generic[_OutputT]):
    """Successful output plus a complete replacement state, not an append delta."""

    output: _OutputT
    next_state: SessionState


class AgentBackend(Protocol[_DepsT, _OutputT]):
    """The only runtime replacement boundary; configuration lives outside requests."""

    async def run(self, request: RunRequest[_DepsT]) -> RunResult[_OutputT]: ...
