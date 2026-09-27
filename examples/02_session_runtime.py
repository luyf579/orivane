"""Reuse two turns in one explicitly created, in-memory session."""

import asyncio

from orivane_core import InMemorySessionRuntime
from orivane_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel


async def main() -> None:
    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        TestModel(custom_output_text="offline session"), output_type=str
    )
    runtime = InMemorySessionRuntime(backend, max_sessions=1)
    runtime.create_session("demo")
    first = await runtime.run("demo", "hello", None)
    second = await runtime.run("demo", "continue", None)
    assert second.output == first.output == "offline session"
    assert second.next_state.payload != first.next_state.payload
    runtime.delete_session("demo")
    print(second.output)


if __name__ == "__main__":
    asyncio.run(main())
