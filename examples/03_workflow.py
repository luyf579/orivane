"""Linear async steps and one synchronous branch, without durable execution."""

import asyncio

from orivane_core import Workflow


async def prepare(value: str) -> str:
    return value.strip()


async def fallback(value: str) -> str:
    return "offline workflow"


async def accept(value: str) -> str:
    return value


async def main() -> None:
    workflow = (
        Workflow[str]()
        .then("prepare", prepare)
        .branch("empty", lambda value: not value, if_true=fallback, if_false=accept)
    )
    assert await workflow.run("  hello  ") == "hello"
    result = await workflow.run("  ")
    assert result == "offline workflow"
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
