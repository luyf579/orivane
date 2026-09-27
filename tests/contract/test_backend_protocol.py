import inspect

import pytest
from orivane_core import AgentBackend, RunRequest, RunResult, SessionState


class FakeBackend:
    async def run(self, request: RunRequest[list[str]]) -> RunResult[str]:
        request.context.append(request.prompt)
        return RunResult(request.prompt.upper(), SessionState("fake", 1, "1", b"next"))


@pytest.mark.asyncio
async def test_structural_backend_works_without_inheritance() -> None:
    # mypy checks structural compatibility; no runtime_checkable or base class is needed.
    backend: AgentBackend[list[str], str] = FakeBackend()
    context: list[str] = []
    result = await backend.run(RunRequest("hello", context))
    assert context == ["hello"]
    assert result.output == "HELLO"
    assert result.next_state.payload == b"next"
    assert inspect.iscoroutinefunction(AgentBackend.run)
    assert list(inspect.signature(AgentBackend.run).parameters) == ["self", "request"]
