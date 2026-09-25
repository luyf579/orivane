"""Typed linear async composition with synchronous if/else decisions."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class _Step(Generic[T]):
    name: str
    function: Callable[[T], Awaitable[T]]


@dataclass(frozen=True)
class _Branch(Generic[T]):
    name: str
    predicate: Callable[[T], bool]
    if_true: Callable[[T], Awaitable[T]]
    if_false: Callable[[T], Awaitable[T]]


class Workflow(Generic[T]):
    """Compose named nodes without changing existing workflows or copying values."""

    def __init__(self) -> None:
        self._nodes: tuple[_Step[T] | _Branch[T], ...] = ()

    def then(self, name: str, step: Callable[[T], Awaitable[T]]) -> "Workflow[T]":
        """Return a new workflow with an async step appended."""
        return self._append(_Step(name, step))

    def branch(
        self,
        name: str,
        predicate: Callable[[T], bool],
        *,
        if_true: Callable[[T], Awaitable[T]],
        if_false: Callable[[T], Awaitable[T]],
    ) -> "Workflow[T]":
        """Return a new workflow that awaits only the selected branch function."""
        return self._append(_Branch(name, predicate, if_true, if_false))

    def _append(self, node: _Step[T] | _Branch[T]) -> "Workflow[T]":
        if not isinstance(node.name, str) or not node.name:
            raise ValueError("node name must be a non-empty string")
        if any(existing.name == node.name for existing in self._nodes):
            raise ValueError("node name already exists")
        workflow = Workflow[T]()
        workflow._nodes = (*self._nodes, node)
        return workflow

    async def run(self, value: T) -> T:
        """Pass each result to the next node; errors and cancellation propagate."""
        current = value
        for node in self._nodes:
            if isinstance(node, _Step):
                current = await node.function(current)
            else:
                decision = node.predicate(current)
                if type(decision) is not bool:
                    raise TypeError("predicate must return bool")
                function = node.if_true if decision else node.if_false
                current = await function(current)
        return current
