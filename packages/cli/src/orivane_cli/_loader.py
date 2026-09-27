"""The sole dynamic application boundary; no reload system or Core-private imports."""

import importlib
import inspect
import sys
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast


class _LoadError(Exception):
    def __init__(self, error_type: str) -> None:
        self.error_type = error_type


@contextmanager
def project_path(root: Path) -> Iterator[None]:
    original = sys.path[:]
    sys.path.insert(0, str(root))
    try:
        yield
    finally:
        sys.path[:] = original


def load_runner(module: str, attribute: str) -> Callable[[str], Awaitable[object]]:
    try:
        factory: object = getattr(importlib.import_module(module), attribute)
        if not callable(factory) or inspect.iscoroutinefunction(factory):
            raise TypeError
        runner: object = factory()
        if inspect.iscoroutine(runner):
            runner.close()
            raise TypeError
        if not callable(runner):
            raise TypeError
    except SystemExit:
        raise _LoadError("SystemExit") from None
    except Exception as error:
        raise _LoadError(type(error).__name__) from None

    async def invoke(prompt: str) -> object:
        pending: object = runner(prompt)
        if not inspect.isawaitable(pending):
            raise TypeError
        return await cast(Awaitable[object], pending)

    return invoke
