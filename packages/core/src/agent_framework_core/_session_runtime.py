"""In-memory session ordering for one shared owner on one event loop."""

import asyncio
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from ._contracts import AgentBackend, RunRequest, RunResult, SessionState
from ._observability import _operation

_DepsT = TypeVar("_DepsT")
_OutputT = TypeVar("_OutputT")


@dataclass(slots=True)
class _SessionEntry:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    users: int = 0


def _validate_session_id(session_id: str) -> None:
    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id must be a non-empty string")


class InMemorySessionRuntime(Generic[_DepsT, _OutputT]):
    """Own opaque snapshots and per-session ordering, without persistence.

    Share one instance on one event loop; management must use the same thread.
    The borrowed backend retains responsibility for its own execution semantics.
    """

    def __init__(self, backend: AgentBackend[_DepsT, _OutputT], *, max_sessions: int) -> None:
        if type(max_sessions) is not int or max_sessions <= 0:
            raise ValueError("max_sessions must be a positive integer")
        self._backend = backend
        self._max_sessions = max_sessions
        self._sessions: dict[str, SessionState | None] = {}
        self._entries: dict[str, _SessionEntry] = {}

    def create_session(self, session_id: str) -> None:
        """Create an empty session; reject duplicates and exhausted capacity."""
        _validate_session_id(session_id)
        if session_id in self._sessions:
            raise ValueError("Session already exists")
        if len(self._sessions) >= self._max_sessions:
            raise RuntimeError("Session capacity exceeded")
        self._sessions[session_id] = None

    def _require_session(self, session_id: str) -> None:
        _validate_session_id(session_id)
        if session_id not in self._sessions:
            raise KeyError("Unknown session")

    async def run(self, session_id: str, prompt: str, context: _DepsT) -> RunResult[_OutputT]:
        """Load, run and commit under the session lock; propagate failure/cancellation."""
        with _operation("session", "run"):
            self._require_session(session_id)
            # Lookup/create/retain is synchronous. Count both the holder and all waiters.
            entry = self._entries.get(session_id)
            if entry is None:
                entry = _SessionEntry()
                self._entries[session_id] = entry
            entry.users += 1
            try:
                async with entry.lock:
                    state = self._sessions[session_id]
                    result = await self._backend.run(RunRequest(prompt, context, state))
                    self._sessions[session_id] = result.next_state
                    return result
            finally:
                entry.users -= 1
                if entry.users == 0 and self._entries.get(session_id) is entry:
                    del self._entries[session_id]

    def delete_session(self, session_id: str) -> None:
        """Delete only an idle session, freeing capacity without cancelling work."""
        self._require_session(session_id)
        # Entries exist only while at least one operation retains them.
        if session_id in self._entries:
            raise RuntimeError("Session is busy")
        del self._sessions[session_id]
