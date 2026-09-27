"""A single complete PydanticAI run behind the owned async contract."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from opentelemetry import trace
from orivane_core import RunRequest, RunResult, ToolDefinition
from orivane_core._observability import _operation
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.models import Model
from pydantic_ai.models.instrumented import InstrumentationSettings

from ._session import decode_state, encode_result
from ._tools import build_tool

_DepsT = TypeVar("_DepsT")
_OutputT = TypeVar("_OutputT")


class PydanticAgentBackend(Generic[_DepsT, _OutputT]):
    """Borrow the caller's Model; own only the Agent, with no external resources.

    Cancellation propagates without a result or automatic whole-run retry.
    Model lifecycle and logical-session serialization remain caller responsibilities.
    """

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
            capabilities=[
                Instrumentation(
                    settings=InstrumentationSettings(
                        tracer_provider=trace.get_tracer_provider(),
                        include_content=False,
                        include_binary_content=False,
                        include_model_request_parameters=False,
                    )
                )
            ],
        )

    async def run(self, request: RunRequest[_DepsT]) -> RunResult[_OutputT]:
        with _operation("agent", "run", backend_id="pydantic-ai"):
            history = decode_state(request.state) if request.state is not None else None
            result = await self._agent.run(
                request.prompt,
                deps=request.context,
                message_history=history,
                usage_limits=self._limits,
            )
            return RunResult(result.output, encode_result(result))
