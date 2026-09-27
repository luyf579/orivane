"""argparse entry point with safe errors and stable exit codes."""

import argparse
import asyncio
import sys
from importlib.metadata import version
from pathlib import Path
from typing import NoReturn

from ._commands import _InitError, execute, initialize
from ._config import _ConfigError, load_config
from ._loader import _LoadError
from ._trace import _ProviderConfiguredError


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # argparse's default text can echo rejected command-line values.
        self.exit(2, "Invalid command usage; use --help.\n")


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(prog="orivane", description="Local Orivane developer commands")
    parser.add_argument("--version", action="version", version=version("orivane-cli"))
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("init", "Create an offline starter in a new or empty directory"),
        ("validate", "Statically validate TOML without importing application code"),
        ("run", "Run an application once with the entire stdin as its prompt"),
        ("trace", "Run once and display local allowlisted spans"),
    ):
        command = commands.add_parser(name, help=help_text, description=help_text)
        command.add_argument("path", nargs="?", default=".")
    args = parser.parse_args(argv)
    root = Path(args.path)
    try:
        if args.command == "init":
            try:
                initialize(root)
            except OSError as error:
                print("Initialization failed: " + type(error).__name__, file=sys.stderr)
                return 2
            print("INITIALIZED")
        elif args.command == "validate":
            load_config(root)
            print("VALID")
        else:
            execute(root, tracing=args.command == "trace")
        return 0
    except (_ConfigError, _InitError) as error:
        print("Invalid configuration or usage: " + error.args[0], file=sys.stderr)
        return 2
    except _LoadError as error:
        print("Application load failed: " + error.error_type, file=sys.stderr)
        return 1
    except _ProviderConfiguredError:
        print("Trace provider already configured", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Interrupted", file=sys.stderr)
        return 130
    except SystemExit:
        print("Run failed: SystemExit", file=sys.stderr)
        return 1
    except Exception as error:
        print("Run failed: " + type(error).__name__, file=sys.stderr)
        return 1
