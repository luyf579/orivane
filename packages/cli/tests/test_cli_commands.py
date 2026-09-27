import io
import runpy
import socket
import sys
from pathlib import Path

import pytest
from opentelemetry import trace
from orivane_cli import _commands
from orivane_cli._commands import _InitError, initialize
from orivane_cli._loader import project_path
from orivane_cli._main import main


def application(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str) -> None:
    (tmp_path / "orivane.toml").write_text(
        'schema_version = 1\n[app]\nfactory = "cli_test_app:create_runner"\n', encoding="utf-8"
    )
    (tmp_path / "cli_test_app.py").write_text(source, encoding="utf-8")
    monkeypatch.delitem(sys.modules, "cli_test_app", raising=False)


@pytest.mark.parametrize("existing", [False, True])
def test_cli_init_is_deterministic_and_safe(tmp_path: Path, existing: bool) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    if existing:
        one.mkdir()
    assert main(["init", str(one)]) == main(["init", str(two)]) == 0
    assert {p.name: p.read_bytes() for p in one.iterdir()} == {
        p.name: p.read_bytes() for p in two.iterdir()
    }
    assert {p.name for p in one.iterdir()} == {"app.py", "orivane.toml", ".gitignore"}


@pytest.mark.parametrize("name", ["orivane.toml", "app.py", "unrelated.txt"])
def test_cli_init_never_overwrites_or_partially_writes(tmp_path: Path, name: str) -> None:
    original = tmp_path / name
    original.write_bytes(b"user content")
    assert main(["init", str(tmp_path)]) == 2
    assert list(tmp_path.iterdir()) == [original] and original.read_bytes() == b"user content"


def test_cli_init_rejects_file_target(tmp_path: Path) -> None:
    target = tmp_path / "file"
    target.write_text("original")
    with pytest.raises(_InitError):
        initialize(target)
    assert target.read_text() == "original"


def test_cli_init_io_failure_cleans_only_its_own_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # The second exclusive open meets a preexisting directory: first file rolls back.
    monkeypatch.setattr(_commands, "_TEMPLATES", {"created": "ours", ".": "blocked"})
    assert main(["init", str(tmp_path)]) == 2
    assert not list(tmp_path.iterdir())
    assert "Initialization failed:" in capsys.readouterr().err


def test_cli_validate_does_not_import_app_or_read_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    application(tmp_path, monkeypatch, 'raise RuntimeError("SECRET_EXCEPTION_CLI_9f12")\n')
    monkeypatch.chdir(tmp_path)
    assert main(["validate"]) == 0  # pytest stdin raises on read
    assert capsys.readouterr().out == "VALID\n"
    assert "cli_test_app" not in sys.modules
    (tmp_path / "orivane.toml").write_text('secret invalid TOML "SECRET_CONTEXT_CLI_9f12"')
    assert main(["validate"]) == 2
    error = capsys.readouterr().err
    assert "SECRET_" not in error and "Traceback" not in error


@pytest.mark.parametrize("command", ["run", "trace"])
def test_cli_bad_config_fails_before_reading_stdin(tmp_path: Path, command: str) -> None:
    assert main([command, str(tmp_path)]) == 2  # pytest stdin raises if read


@pytest.mark.parametrize(
    "source,category",
    [
        ('raise ImportError("SECRET_EXCEPTION_CLI_9f12")', "ImportError"),
        ('raise SystemExit("SECRET_SYSTEM_EXIT_CLI_9f12")', "SystemExit"),
        (
            'def create_runner():\n    raise SystemExit("SECRET_SYSTEM_EXIT_CLI_9f12")',
            "SystemExit",
        ),
        ("other = 1", "AttributeError"),
        ("create_runner = 1", "TypeError"),
        ("def create_runner(required):\n    return required", "TypeError"),
        ('def create_runner():\n    raise ValueError("SECRET_EXCEPTION_CLI_9f12")', "ValueError"),
        ("def create_runner():\n    return 1", "TypeError"),
        ("async def create_runner():\n    return 1", "TypeError"),
        (
            "class Factory:\n    async def __call__(self):\n        return 1\n"
            "create_runner = Factory()",
            "TypeError",
        ),
    ],
)
def test_cli_loader_failures_are_safe_and_restore_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    source: str,
    category: str,
) -> None:
    application(tmp_path, monkeypatch, source)
    original = sys.path[:]
    monkeypatch.setattr(sys, "stdin", io.StringIO("SECRET_PROMPT_CLI_9f12"))
    assert main(["run", str(tmp_path)]) == 1
    assert sys.path == original
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == f"Application load failed: {category}\n"


def test_cli_missing_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    application(tmp_path, monkeypatch, "")
    (tmp_path / "cli_test_app.py").unlink()
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert main(["run", str(tmp_path)]) == 1
    assert capsys.readouterr().err == "Application load failed: ModuleNotFoundError\n"


@pytest.mark.parametrize(
    "body,code,diagnostic",
    [
        ('raise RuntimeError("SECRET_EXCEPTION_CLI_9f12")', 1, "Run failed: RuntimeError"),
        ('raise SystemExit("SECRET_SYSTEM_EXIT_CLI_9f12")', 1, "Run failed: SystemExit"),
        ("raise SystemExit(17)", 1, "Run failed: SystemExit"),
        ('raise KeyboardInterrupt("SECRET_EXCEPTION_CLI_9f12")', 130, "Interrupted"),
        ('raise asyncio.CancelledError("SECRET_EXCEPTION_CLI_9f12")', 130, "Interrupted"),
    ],
)
def test_cli_runner_errors_and_interruptions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    body: str,
    code: int,
    diagnostic: str,
) -> None:
    application(
        tmp_path,
        monkeypatch,
        "import asyncio\ndef create_runner():\n    async def run(prompt):\n"
        f"        {body}\n    return run\n",
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("SECRET_PROMPT_CLI_9f12"))
    original = sys.path[:]
    assert main(["run", str(tmp_path)]) == code
    assert sys.path == original
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == diagnostic + "\n"


def test_cli_nonawaitable_result_is_runtime_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    application(tmp_path, monkeypatch, "def create_runner():\n    return lambda prompt: 1\n")
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert main(["run", str(tmp_path)]) == 1
    assert capsys.readouterr().err == "Run failed: TypeError\n"


@pytest.mark.parametrize("prompt", ["", "  SECRET_PROMPT_CLI_9f12\nnext line\n"])
def test_cli_success_preserves_stdin_and_restores_import_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], prompt: str
) -> None:
    application(
        tmp_path,
        monkeypatch,
        "def create_runner():\n    async def run(prompt):\n        return prompt\n    return run\n",
    )
    original = sys.path[:]
    monkeypatch.setattr(sys, "stdin", io.StringIO(prompt))
    assert main(["run", str(tmp_path)]) == 0
    assert sys.path == original
    assert capsys.readouterr().out == prompt + "\n"


def test_cli_project_path_restores_after_application_path_mutation(tmp_path: Path) -> None:
    original = sys.path[:]
    with project_path(tmp_path):
        assert sys.path[0] == str(tmp_path)
        sys.path.append("added by application")
    assert sys.path == original


@pytest.mark.asyncio
async def test_cli_offline_starter_needs_no_network_or_provider_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("offline starter attempted network")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.delitem(sys.modules, "app", raising=False)
    initialize(tmp_path)
    (tmp_path / ".env").write_text("SECRET_CONTEXT_CLI_9f12=must-not-load")
    provider = trace.get_tracer_provider()
    # Install the network guard after pytest creates the Windows event-loop self-pipe.
    result = await _commands._run(tmp_path, ("app", "create_runner"), "SECRET_PROMPT_CLI_9f12")
    assert result == "offline starter"
    assert trace.get_tracer_provider() is provider


@pytest.mark.parametrize("argv", [[], ["unknown"], ["run", "--prompt", "SECRET_PROMPT_CLI_9f12"]])
def test_cli_usage_errors_never_echo_arguments(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 2
    assert capsys.readouterr().err == "Invalid command usage; use --help.\n"


@pytest.mark.parametrize(
    "argv",
    [
        ["--help"],
        ["--version"],
        ["init", "--help"],
        ["validate", "--help"],
        ["run", "--help"],
        ["trace", "--help"],
    ],
)
def test_cli_help_and_version(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 0 and capsys.readouterr().err == ""


def test_cli_module_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["orivane", "--version"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("orivane_cli", run_name="__main__")
    assert caught.value.code == 0


def test_cli_preconfigured_provider_is_not_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    application(tmp_path, monkeypatch, 'raise RuntimeError("factory must not load")')
    provider = trace.NoOpTracerProvider()
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert main(["trace", str(tmp_path)]) == 1
    assert trace.get_tracer_provider() is provider and "cli_test_app" not in sys.modules
    assert capsys.readouterr().err == "Trace provider already configured\n"
