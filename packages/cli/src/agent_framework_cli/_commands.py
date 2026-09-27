"""Small command operations; application output is separate from telemetry."""

import asyncio
import sys
from pathlib import Path

from ._config import load_config
from ._loader import load_runner, project_path
from ._trace import capture, format_spans

_TEMPLATES = {
    "agent-framework.toml": 'schema_version = 1\n\n[app]\nfactory = "app:create_runner"\n',
    ".gitignore": ".env\n.venv/\n__pycache__/\n*.pyc\n",
    "app.py": """from collections.abc import Awaitable, Callable

from agent_framework_core import RunRequest
from agent_framework_pydantic import PydanticAgentBackend
from pydantic_ai.models.test import TestModel


def create_runner() -> Callable[[str], Awaitable[object]]:
    # TestModel is an offline starter only.
    # Replace it with a real PydanticAI Model in your application when ready.
    backend: PydanticAgentBackend[None, str] = PydanticAgentBackend(
        TestModel(custom_output_text="offline starter"), output_type=str
    )

    async def run(prompt: str) -> object:
        result = await backend.run(RunRequest(prompt, None))
        return result.output

    return run
""",
}


class _InitError(ValueError):
    pass


def initialize(root: Path) -> None:
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise _InitError("initialization requires a new or empty directory")
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    try:
        for name, content in _TEMPLATES.items():
            path = root / name
            with path.open("x", encoding="utf-8", newline="\n") as target:
                created.append(path)
                target.write(content)
    except OSError:
        # Only remove files exclusively created by this invocation, never user files.
        for path in created:
            path.unlink()
        raise


async def _run(root: Path, factory: tuple[str, str], prompt: str) -> object:
    with project_path(root.resolve()):
        runner = load_runner(*factory)
        return await runner(prompt)


def execute(root: Path, *, tracing: bool) -> None:
    factory = load_config(root)
    prompt = sys.stdin.read()
    if tracing:
        with capture() as exporter:
            result = asyncio.run(_run(root, factory, prompt))
        print(str(result))
        print("TRACE")
        print(format_spans(exporter.get_finished_spans()))
    else:
        result = asyncio.run(_run(root, factory, prompt))
        print(str(result))
