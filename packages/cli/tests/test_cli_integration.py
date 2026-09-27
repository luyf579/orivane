import json
import os
import subprocess
import sys
from importlib.metadata import distribution, version
from pathlib import Path

import pytest


def invoke(root: Path, *args: str, prompt: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "orivane_cli", *args],
        cwd=root,
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )


def test_cli_init_validate_run_trace_subprocess_roundtrip(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    result = invoke(tmp_path, "init", "demo")
    assert result.returncode == 0 and result.stdout == "INITIALIZED\n" and result.stderr == ""
    result = invoke(project, "validate")
    assert result.returncode == 0 and result.stdout == "VALID\n" and result.stderr == ""
    result = invoke(project, "run", prompt="SECRET_PROMPT_CLI_9f12")
    assert result.returncode == 0 and result.stdout == "offline starter\n"
    assert "SECRET_" not in result.stderr
    result = invoke(project, "trace", prompt="SECRET_PROMPT_CLI_9f12")
    assert result.returncode == 0, result.stderr
    output, trace_output = result.stdout.split("\nTRACE\n", 1)
    assert output == "offline starter"
    assert "SECRET_" not in trace_output + result.stderr
    rows = [json.loads(line) for line in trace_output.splitlines()]
    framework = next(row for row in rows if row["name"] == "agent_framework.agent.run")
    native = [row for row in rows if row["attributes"].get("gen_ai.operation.name") == "chat"]
    assert native  # provider installed before backend construction in the starter factory
    assert all(row["trace_id"] == framework["trace_id"] for row in native)
    by_id = {row["span_id"]: row for row in rows}
    parent = native[0]
    while parent["span_id"] != framework["span_id"]:
        parent = by_id[parent["parent_span_id"]]


def test_cli_trace_privacy_subprocess_separates_requested_output(tmp_path: Path) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "app:create_runner"\n'
    )
    (tmp_path / "app.py").write_text("""from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
assert isinstance(trace.get_tracer_provider(), TracerProvider)
def create_runner():
    async def run(prompt):
        with trace.get_tracer("application").start_as_current_span("application.run") as span:
            span.set_attribute("prompt", prompt)
            span.set_attribute("context", "SECRET_CONTEXT_CLI_9f12")
            span.set_attribute("gen_ai.tool.definitions", "SECRET_SCHEMA_CLI_9f12")
            span.add_event("unsafe", {"exception.message": "SECRET_EXCEPTION_CLI_9f12"})
            span.set_status(trace.Status(trace.StatusCode.ERROR, "SECRET_EXCEPTION_CLI_9f12"))
        return prompt
    return run
""")
    result = invoke(tmp_path, "trace", prompt="SECRET_PROMPT_CLI_9f12")
    assert result.returncode == 0, result.stderr
    output, structural = result.stdout.split("\nTRACE\n", 1)
    assert output == "SECRET_PROMPT_CLI_9f12"
    assert "SECRET_" not in structural + result.stderr


@pytest.mark.parametrize("command", ["run", "trace"])
def test_cli_subprocess_error_message_privacy(tmp_path: Path, command: str) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "app:create_runner"\n'
    )
    (tmp_path / "app.py").write_text("""def create_runner():
    async def run(prompt):
        raise RuntimeError("SECRET_EXCEPTION_CLI_9f12 SECRET_CONTEXT_CLI_9f12")
    return run
""")
    result = invoke(tmp_path, command, prompt="SECRET_PROMPT_CLI_9f12")
    assert result.returncode == 1
    assert result.stdout == "" and result.stderr == "Run failed: RuntimeError\n"


@pytest.mark.parametrize("command", ["run", "trace"])
@pytest.mark.parametrize(
    "source,diagnostic",
    [
        ('raise SystemExit("SECRET_SYSTEM_EXIT_CLI_9f12")', "Application load failed: SystemExit"),
        (
            'def create_runner():\n    raise SystemExit("SECRET_SYSTEM_EXIT_CLI_9f12")',
            "Application load failed: SystemExit",
        ),
        (
            "def create_runner():\n    async def run(prompt):\n"
            '        raise SystemExit("SECRET_SYSTEM_EXIT_CLI_9f12")\n    return run\n',
            "Run failed: SystemExit",
        ),
        (
            "def create_runner():\n    async def run(prompt):\n"
            "        raise SystemExit(17)\n    return run\n",
            "Run failed: SystemExit",
        ),
    ],
    ids=["import", "factory", "runner-message", "runner-code"],
)
def test_cli_systemexit_subprocess_privacy(
    tmp_path: Path, command: str, source: str, diagnostic: str
) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "app:create_runner"\n'
    )
    (tmp_path / "app.py").write_text(source)
    result = invoke(tmp_path, command, prompt="SECRET_PROMPT_CLI_9f12")
    assert result.returncode == 1
    assert result.stdout == "" and result.stderr == diagnostic + "\n"
    assert "SECRET_" not in result.stdout + result.stderr
    assert "Traceback" not in result.stdout + result.stderr


@pytest.mark.parametrize("command", ["run", "trace"])
@pytest.mark.parametrize("exception", ["KeyboardInterrupt", "asyncio.CancelledError"])
def test_cli_subprocess_interruptions(tmp_path: Path, command: str, exception: str) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "app:create_runner"\n'
    )
    (tmp_path / "app.py").write_text(
        "import asyncio\ndef create_runner():\n    async def run(prompt):\n"
        f'        raise {exception}("SECRET_EXCEPTION_CLI_9f12")\n    return run\n'
    )
    result = invoke(tmp_path, command)
    assert result.returncode == 130
    assert result.stdout == "" and result.stderr == "Interrupted\n"


def test_cli_console_entrypoint_matches_module_and_help(tmp_path: Path) -> None:
    entries = [
        entry for entry in distribution("orivane-cli").entry_points if entry.name == "orivane"
    ]
    assert len(entries) == 1 and entries[0].value == "orivane_cli._main:main"
    assert callable(entries[0].load())
    executable = Path(sys.executable).parent / ("orivane.exe" if os.name == "nt" else "orivane")
    result = subprocess.run(
        [str(executable), "--version"], capture_output=True, text=True, timeout=15
    )
    module = invoke(tmp_path, "--version")
    assert result.returncode == module.returncode == 0
    assert result.stdout == module.stdout == version("orivane-cli") + "\n"
    for args in [
        ("--help",),
        ("init", "--help"),
        ("validate", "--help"),
        ("run", "--help"),
        ("trace", "--help"),
    ]:
        result = invoke(tmp_path, *args)
        assert result.returncode == 0 and result.stderr == "" and "usage:" in result.stdout


def test_cli_validation_subprocess_never_executes_application(tmp_path: Path) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "app:create_runner"\n'
    )
    (tmp_path / "app.py").write_text(
        'from pathlib import Path\nPath("executed").touch()\n'
        'raise RuntimeError("SECRET_EXCEPTION_CLI_9f12")\n'
    )
    assert invoke(tmp_path, "validate").returncode == 0
    assert not (tmp_path / "executed").exists()
