"""Offline quickstart; no credentials or provider certification required."""

import asyncio

from orivane_core import AgentBackend, RunRequest
from orivane_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel


async def main() -> None:
    backend: AgentBackend[None, str] = PydanticAgentBackend(
        TestModel(custom_output_text="offline agent"), output_type=str
    )
    result = await backend.run(RunRequest("hello", None))
    assert result.output == "offline agent"
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
