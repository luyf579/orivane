"""Convert owned tools without exposing injected dependencies to the model."""

from typing import TypeVar

from agent_framework_core import ToolDefinition
from pydantic import BaseModel, JsonValue, ValidationError
from pydantic_ai import ModelRetry, RunContext, Tool

_ArgsT = TypeVar("_ArgsT", bound=BaseModel)
_DepsT = TypeVar("_DepsT")


def build_tool(definition: ToolDefinition[_ArgsT, _DepsT]) -> Tool[_DepsT]:
    async def invoke(ctx: RunContext[_DepsT], /, **raw_args: object) -> JsonValue:
        # from_schema skips schema validation: validate before any business side effect.
        try:
            arguments = definition.parameters.model_validate(raw_args)
        except ValidationError:
            raise ModelRetry("Invalid tool arguments. Follow the tool parameter schema.") from None
        # Business exceptions must propagate; do not include this call in the retry handler.
        return await definition.invoke(ctx.deps, arguments)

    return Tool[_DepsT].from_schema(
        invoke,
        name=definition.name,
        description=definition.description,
        json_schema=definition.parameters.model_json_schema(),
        takes_ctx=True,
    )
