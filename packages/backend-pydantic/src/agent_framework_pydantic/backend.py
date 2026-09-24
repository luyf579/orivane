"""A single complete PydanticAI run behind the owned async contract."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from agent_framework_core import RunRequest, RunResult, ToolDefinition
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.models import Model

from ._session import decode_state, encode_result
from ._tools import build_tool

_DepsT = TypeVar("_DepsT")
_OutputT = TypeVar("_OutputT")


class PydanticAgentBackend(Generic[_DepsT, _OutputT]):
    """Development runtime; no session storage, resource ownership, or automatic run retries."""

    def __init__(
        self,
        model: Model,
        *,
        output_type: type[_OutputT],
        instructions: str = "",
        # A heterogeneous collection erases only ArgsT. Each tool keeps its own model
        # and typed invoke together; build_tool validates that model before invocation.
        tools: Sequence[ToolDefinition[Any, _DepsT]] = (),
        request_limit: int = 50,
        tool_calls_limit: int = 50,
    ) -> None:
        for limit in (request_limit, tool_calls_limit):
            if type(limit) is not int or limit < 0:
                raise ValueError("Usage limits must be finite non-negative integers")
        self._limits = UsageLimits(request_limit=request_limit, tool_calls_limit=tool_calls_limit)
        self._agent: Agent[_DepsT, _OutputT] = Agent(
            model,
            output_type=output_type,
            instructions=instructions,
            tools=[build_tool(tool) for tool in tools],
        )

    async def run(self, request: RunRequest[_DepsT]) -> RunResult[_OutputT]:
        history = decode_state(request.state) if request.state is not None else None
        result = await self._agent.run(
            request.prompt,
            deps=request.context,
            message_history=history,
            usage_limits=self._limits,
        )
        return RunResult(result.output, encode_result(result))
